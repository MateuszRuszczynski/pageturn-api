from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123",
            first_name="John",
            last_name="Doe",
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("StrongPass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="StrongPass123",
            )

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123",
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_get_full_name(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123",
            first_name="John",
            last_name="Doe",
        )

        self.assertEqual(user.get_full_name(), "John Doe")

    def test_str_method(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123",
        )

        self.assertEqual(str(user), "test@example.com")
