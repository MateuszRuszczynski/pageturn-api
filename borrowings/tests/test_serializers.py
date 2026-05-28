from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from books.models import Book
from borrowings.serializers import BorrowingCreateSerializer, BorrowingReadSerializer
from rest_framework.test import APIRequestFactory


class BorrowingSerializerTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="patron@library.com", password="SecurePassword123!"
        )
        self.book = Book.objects.create(
            title="Dune",
            author="Frank Herbert",
            cover="SOFT",
            inventory=2,
            daily_fee="3.00",
        )

    def _get_serializer_context(self):
        factory = APIRequestFactory()
        request = factory.post("/api/borrowings/")
        request.user = self.user
        return {"request": request}

    def _create_serializer(self, data):
        return BorrowingCreateSerializer(
            data=data,
            context=self._get_serializer_context()
        )

    def test_read_serializer_outputs_detailed_nested_data(self):
        from borrowings.models import Borrowing

        borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

        serializer = BorrowingReadSerializer(borrowing)

        self.assertEqual(serializer.data["book"]["title"], "Dune")
        self.assertEqual(serializer.data["user"], "patron@library.com")

    def test_create_serializer_automatically_sets_default_return_date(self):
        payload = {
            "book": self.book.id,
        }
        serializer = self._create_serializer(payload)

        self.assertTrue(serializer.is_valid())

        borrowing = serializer.save(user=self.user)
        expected_default_date = date.today() + timedelta(days=14)

        self.assertEqual(borrowing.expected_return_date, expected_default_date)

    def test_create_serializer_fails_when_book_out_of_stock(self):
        self.book.inventory = 0
        self.book.save()

        payload = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }

        serializer = self._create_serializer(payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("book", serializer.errors)

    def test_create_serializer_fails_for_past_expected_return_date(self):
        past_date = date.today() - timedelta(days=2)
        payload = {
            "book": self.book.id,
            "expected_return_date": past_date,
        }

        serializer = self._create_serializer(payload)

        self.assertFalse(serializer.is_valid())
        self.assertIn("expected_return_date", serializer.errors)

    def test_create_serializer_decrements_book_inventory_by_one(self):
        payload = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }

        initial_inventory = self.book.inventory
        serializer = self._create_serializer(payload)

        self.assertTrue(serializer.is_valid())
        serializer.save(user=self.user)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)
