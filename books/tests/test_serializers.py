from django.test import TestCase
from rest_framework.serializers import ValidationError
from books.serializers import BookSerializer


class BookSerializerTests(TestCase):

    def setUp(self):
        self.valid_payload = {
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "cover": "HARD",
            "inventory": 5,
            "daily_fee": "12.50",
        }

    def test_serializer_with_valid_payload(self):
        serializer = BookSerializer(data=self.valid_payload)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["title"], self.valid_payload["title"]
        )

    def test_serializer_validation_fails_lowercase_title(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload["title"] = "the Hobbit"

        serializer = BookSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_serializer_validation_fails_lowercase_author(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload["author"] = "J.R.R. tolkien"

        serializer = BookSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("author", serializer.errors)

    def test_serializer_validation_fails_missing_surname(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload["author"] = "Andrzej"

        serializer = BookSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("author", serializer.errors)

    def test_serializer_validation_fails_negative_inventory(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload["inventory"] = -5

        serializer = BookSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("inventory", serializer.errors)

    def test_serializer_allows_zero_inventory(self):
        valid_zero_payload = self.valid_payload.copy()
        valid_zero_payload["inventory"] = 0

        serializer = BookSerializer(data=valid_zero_payload)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["inventory"], 0)
