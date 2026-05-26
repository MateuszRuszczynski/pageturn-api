from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from books.models import Book
from borrowings.models import Borrowing

BORROWINGS_URL = reverse("borrowing:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowing:borrowing-detail", args=[borrowing_id])


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

    def test_create_borrowing_endpoint_attaches_current_user_automatically(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            "book": self.book2.id,
            "expected_return_date": str(date.today() + timedelta(days=5)),
        }

        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["book"], self.book2.id)

        created_borrowing = Borrowing.objects.get(id=response.data["id"])
        self.assertEqual(created_borrowing.user, self.user1)
