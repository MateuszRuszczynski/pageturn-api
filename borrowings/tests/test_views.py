from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

BORROWINGS_URL = reverse("api:borrowing-list")


def detail_url(borrowing_id):
    return reverse("api:borrowing-detail", args=[borrowing_id])


class BorrowingApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@library.com", password="AdminPassword123!"
        )
        self.user1 = get_user_model().objects.create_user(
            email="user1@library.com", password="User1Password123!"
        )
        self.user2 = get_user_model().objects.create_user(
            email="user2@library.com", password="User2Password123!"
        )

        self.book1 = Book.objects.create(
            title="The Hobbit",
            author="J.R.R. Tolkien",
            cover="HARD",
            inventory=5,
            daily_fee="2.00",
        )
        self.book2 = Book.objects.create(
            title="Dune",
            author="Frank Herbert",
            cover="SOFT",
            inventory=3,
            daily_fee="3.50",
        )

        self.borrowing_user1 = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=10),
            book=self.book1,
            user=self.user1,
        )
        self.borrowing_user2 = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book2,
            user=self.user2,
        )

    def test_anonymous_user_is_completely_unauthorized(self):
        response = self.client.get(BORROWINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_sees_only_their_own_borrowings(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(BORROWINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.borrowing_user1.id)
        self.assertEqual(response.data[0]["user"], self.user1.email)

    def test_admin_user_sees_all_global_borrowings(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(BORROWINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_regular_user_cannot_retrieve_other_users_borrowing_detail(self):
        self.client.force_authenticate(user=self.user1)
        url = detail_url(self.borrowing_user2.id)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("borrowings.views.create_stripe_checkout_session")
    def test_create_borrowing_endpoint_attaches_current_user_automatically(
        self, mock_stripe
    ):
        mock_stripe.return_value = {
            "session_url": "https://checkout.stripe.com/c/pay/test_session",
            "session_id": "cs_test_id",
        }
        self.client.force_authenticate(user=self.user1)
        payload = {
            "book": self.book2.id,
            "expected_return_date": str(date.today() + timedelta(days=5)),
        }

        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["book"]["id"], self.book2.id)

        created_borrowing = Borrowing.objects.get(id=response.data["id"])
        self.assertEqual(created_borrowing.user, self.user1)

    def test_filter_borrowings_by_active_status(self):
        self.client.force_authenticate(user=self.admin_user)

        Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=5),
            actual_return_date=date.today(),
            book=self.book1,
            user=self.user1,
        )

        response_active = self.client.get(BORROWINGS_URL, {"is_active": "true"})
        self.assertEqual(len(response_active.data), 2)

        response_inactive = self.client.get(BORROWINGS_URL, {"is_active": "false"})
        self.assertEqual(len(response_inactive.data), 1)

    def test_admin_can_filter_by_user_id(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(BORROWINGS_URL, {"user_id": self.user2.id})

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"], self.user2.email)


class BorrowingReturnFineTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@user.com", password="password123"
        )
        self.client.force_authenticate(self.user)

        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            inventory=5,
            daily_fee=Decimal("2.50"),
            cover="HARD",
        )

        self.borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=5),
            book=self.book,
            user=self.user,
        )

        Borrowing.objects.filter(id=self.borrowing.id).update(
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )

        self.borrowing.refresh_from_db()
        self.return_url = reverse(
            "api:borrowing-return-book", kwargs={"pk": self.borrowing.id}
        )

    @patch("borrowings.views.create_stripe_checkout_session")
    def test_return_book_overdue_calculates_fine_correctly(self, mock_stripe):
        mock_stripe.return_value = {
            "session_url": "https://checkout.stripe.com/c/pay/test_fine_session",
            "session_id": "cs_test_fine_id",
        }

        self.assertEqual(self.book.inventory, 5)
        response = self.client.post(self.return_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(self.borrowing.actual_return_date, date.today())
        self.assertEqual(self.book.inventory, 6)

        payment_exists = Payment.objects.filter(
            borrowing=self.borrowing, type=Payment.TypeChoices.FINE
        ).exists()
        self.assertTrue(payment_exists)

        payment = Payment.objects.get(
            borrowing=self.borrowing, type=Payment.TypeChoices.FINE
        )
        expected_fine = Decimal("5") * self.book.daily_fee * Decimal("2.0")

        self.assertEqual(payment.money_to_pay, expected_fine)
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)

    @patch("borrowings.views.create_stripe_checkout_session")
    def test_return_book_on_time_does_not_create_fine(self, mock_stripe):
        on_time_borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=2),
            book=self.book,
            user=self.user,
        )
        url = reverse("api:borrowing-return-book", kwargs={"pk": on_time_borrowing.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        on_time_borrowing.refresh_from_db()
        self.assertEqual(on_time_borrowing.actual_return_date, date.today())

        fine_exists = Payment.objects.filter(
            borrowing=on_time_borrowing, type=Payment.TypeChoices.FINE
        ).exists()
        self.assertFalse(fine_exists)

    def test_cannot_return_already_returned_book(self):
        self.borrowing.actual_return_date = date.today()
        self.borrowing.save()

        response = self.client.post(self.return_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
