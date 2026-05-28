from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from books.models import Book
from books.serializers import BookSerializer

BOOKS_URL = reverse("api:book-list")


def detail_url(book_id):
    return reverse("api:book-detail", args=[book_id])


class PublicBookApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = Book.objects.create(
            title="A Game of Thrones",
            author="G.R.R. Martin",
            cover="SOFT",
            inventory=10,
            daily_fee="4.99",
        )

    def test_list_books_accessible_by_anyone(self):
        response = self.client.get(BOOKS_URL)
        books = Book.objects.all().order_by("title")
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_single_book_details_success(self):
        url = detail_url(self.book.id)
        response = self.client.get(url)
        serializer = BookSerializer(self.book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_unauthorized_for_anonymous_user(self):
        payload = {
            "title": "New Book",
            "author": "John Doe",
            "cover": "SOFT",
            "inventory": 1,
            "daily_fee": "1.00",
        }
        response = self.client.post(BOOKS_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateAdminBookApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@library.com", password="AdminPassword123!"
        )
        self.regular_user = get_user_model().objects.create_user(
            email="user@library.com", password="UserPassword123!"
        )
        self.book = Book.objects.create(
            title="The Fellowship of the Ring",
            author="J.R.R. Tolkien",
            cover="HARD",
            inventory=3,
            daily_fee="3.50",
        )

    def test_create_book_forbidden_for_regular_authenticated_user(self):
        self.client.force_authenticate(user=self.regular_user)
        payload = {
            "title": "Starlight",
            "author": "Jane Doe",
            "cover": "SOFT",
            "inventory": 2,
            "daily_fee": "1.50",
        }
        response = self.client.post(BOOKS_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_book_success_for_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "title": "The Return of the King",
            "author": "J.R.R. Tolkien",
            "cover": "HARD",
            "inventory": 7,
            "daily_fee": "5.00",
        }
        response = self.client.post(BOOKS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], payload["title"])
        self.assertTrue(Book.objects.filter(title=payload["title"]).exists())

    def test_update_book_success_for_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)
        url = detail_url(self.book.id)
        payload = {"inventory": 15}

        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 15)

    def test_delete_book_success_for_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)
        url = detail_url(self.book.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=self.book.id).exists())
