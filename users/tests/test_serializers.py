from django.contrib.auth import get_user_model
from django.test import TestCase

from users.serializers import UserManageSerializer, UserSerializer

User = get_user_model()


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
        }

    def test_serializer_with_valid_data(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["email"], self.user_data["email"]
        )

    def test_password_is_write_only(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        output_data = UserSerializer(user).data

        self.assertNotIn("password", output_data)

    def test_read_only_fields_cannot_be_mutated(self):
        malicious_payload = self.user_data.copy()
        malicious_payload.update({"is_staff": True, "is_active": False})

        serializer = UserSerializer(data=malicious_payload)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_password_validation_fails_if_too_short(self):
        invalid_payload = self.user_data.copy()
        invalid_payload["password"] = "short"

        serializer = UserSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_create_method_hashes_password(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertNotEqual(user.password, self.user_data["password"])
        self.assertTrue(user.check_password(self.user_data["password"]))

    def test_update_method_saves_profile_fields(self):
        user = User.objects.create_user(
            email="original@example.com", password="OldSecurePassword123!"
        )
        update_payload = {"first_name": "Kevin", "last_name": "Smith"}

        serializer = UserSerializer(
            instance=user, data=update_payload, partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.first_name, "Kevin")
        self.assertEqual(updated_user.last_name, "Smith")

    def test_update_method_modifies_and_hashes_new_password(self):
        user = User.objects.create_user(
            email="original@example.com", password="OldSecurePassword123!"
        )
        update_payload = {"password": "BrandNewSecurePassword987!"}

        serializer = UserSerializer(
            instance=user, data=update_payload, partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertTrue(
            updated_user.check_password("BrandNewSecurePassword987!")
        )


class UserManageSerializerTests(TestCase):
    def test_serializer_output_schema(self):
        user = User.objects.create_user(
            email="profile@example.com",
            password="Password123!",
            first_name="Anna",
            last_name="Nowak",
        )

        serializer = UserManageSerializer(instance=user)
        expected_fields = {"id", "email", "first_name", "last_name"}

        self.assertEqual(set(serializer.data.keys()), expected_fields)
        self.assertEqual(serializer.data["email"], "profile@example.com")
        self.assertNotIn("password", serializer.data)
