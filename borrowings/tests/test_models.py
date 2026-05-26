from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from books.models import Book
from borrowings.models import Borrowing


class BorrowingModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="testuser@library.com", password="TestPassword123!"
        )
        self.book = Book.objects.create(
            title="The Hobbit",
            author="J.R.R. Tolkien",
            cover="HARD",
            inventory=5,
            daily_fee="2.50",
        )
        self.today = date.today()

    def test_borrowing_model_string_representation(self):
        expected_return_date = self.today + timedelta(days=14)
        borrowing = Borrowing.objects.create(
            expected_return_date=expected_return_date,
            book=self.book,
            user=self.user,
        )

        expected_str = (
            f"User {self.user.id} borrowed Book {self.book.id} "
            f"({borrowing.borrow_date} to {expected_return_date})"
        )
        self.assertEqual(str(borrowing), expected_str)

    def test_database_constraint_prevents_expected_return_date_in_past(self):
        past_date = self.today - timedelta(days=1)

        borrowing = Borrowing(
            expected_return_date=past_date,
            book=self.book,
            user=self.user,
        )
        borrowing.borrow_date = self.today

        with self.assertRaises(IntegrityError):
            borrowing.save()

    def test_database_constraint_prevents_actual_return_date_before_borrow_date(self):
        expected_return_date = self.today + timedelta(days=7)
        past_actual_return_date = self.today - timedelta(days=2)

        borrowing = Borrowing(
            expected_return_date=expected_return_date,
            actual_return_date=past_actual_return_date,
            book=self.book,
            user=self.user,
        )
        borrowing.borrow_date = self.today

        with self.assertRaises(IntegrityError):
            borrowing.save()

    def test_successful_borrowing_with_valid_dates(self):
        expected_return_date = self.today + timedelta(days=10)
        actual_return_date = self.today + timedelta(days=5)

        borrowing = Borrowing.objects.create(
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
            book=self.book,
            user=self.user,
        )

        self.assertEqual(borrowing.expected_return_date, expected_return_date)
        self.assertEqual(borrowing.actual_return_date, actual_return_date)
