from django.test import TestCase
from books.models import Book


class BookModelTests(TestCase):
    def test_create_book_successful(self):
        book = Book.objects.create(
            title="To Kill a Mockingbird",
            author="Harper Lee",
            cover="SOFT",
            inventory=15,
            daily_fee=1.20,
        )

        self.assertEqual(book.title, "To Kill a Mockingbird")
        self.assertEqual(book.author, "Harper Lee")
        self.assertEqual(book.cover, "SOFT")
        self.assertEqual(book.inventory, 15)
        self.assertEqual(book.daily_fee, 1.20)
        self.assertEqual(str(book), "To Kill a Mockingbird by Harper Lee (SOFT)")
