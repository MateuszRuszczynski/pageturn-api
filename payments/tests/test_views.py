from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

PAYMENTS_URL = reverse("api:payment-list")


def detail_url(payment_id):
    return reverse("api:payment-detail", args=[payment_id])


class PaymentApiTests(APITestCase):
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

        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            cover="HARD",
            inventory=5,
            daily_fee=Decimal("2.50"),
        )

        self.borrowing1 = Borrowing.objects.create(
            book=self.book, user=self.user1, expected_return_date="2026-06-05"
        )
        self.borrowing2 = Borrowing.objects.create(
            book=self.book, user=self.user2, expected_return_date="2026-06-05"
        )

        self.payment_user1 = Payment.objects.create(
            status=Payment.StatusChoices.PENDING,
            type=Payment.TypeChoices.PAYMENT,
            borrowing=self.borrowing1,
            session_url="https://checkout.stripe.com/pay/session_1",
            session_id="cs_test_1",
            money_to_pay=Decimal("12.50"),
        )

        self.payment_user2 = Payment.objects.create(
            status=Payment.StatusChoices.PENDING,
            type=Payment.TypeChoices.PAYMENT,
            borrowing=self.borrowing2,
            session_url="https://checkout.stripe.com/pay/session_2",
            session_id="cs_test_2",
            money_to_pay=Decimal("12.50"),
        )

    def test_anonymous_user_cannot_see_payments(self):
        response = self.client.get(PAYMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_sees_only_their_own_payments(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(PAYMENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.payment_user1.id)
        self.assertEqual(response.data[0]["session_id"], "cs_test_1")

    def test_admin_user_can_see_all_global_payments(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(PAYMENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_regular_user_cannot_retrieve_other_users_payment_detail(self):
        self.client.force_authenticate(user=self.user1)

        url = detail_url(self.payment_user2.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_detail_displays_correct_data(self):
        self.client.force_authenticate(user=self.user1)

        url = detail_url(self.payment_user1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["session_id"], self.payment_user1.session_id
        )
        self.assertEqual(response.data["money_to_pay"], "12.50")
