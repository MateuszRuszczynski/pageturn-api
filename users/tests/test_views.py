from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

User = get_user_model()


class PublicUserApiTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("user:create")
        self.user_data = {
            "email": "register@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
        }

    def test_create_user_success(self):
        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["email"], self.user_data["email"])
        self.assertNotIn("password", response.data)

        user_exists = User.objects.filter(email=self.user_data["email"]).exists()
        self.assertTrue(user_exists)

    def test_create_user_fails_with_invalid_data(self):
        invalid_data = self.user_data.copy()
        invalid_data["password"] = "short"

        response = self.client.post(self.register_url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


class PrivateUserApiTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.me_url = reverse("user:user_account")

        self.user = User.objects.create_user(
            email="profile@example.com",
            password="SecurePassword123!",
            first_name="Kevin",
            last_name="Smith",
        )

    def test_retrieve_profile_unauthorized(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertNotIn("password", response.data)

    def test_update_profile_success(self):
        self.client.force_authenticate(user=self.user)
        update_data = {"first_name": "Jack", "last_name": "Sparrow"}

        response = self.client.patch(self.me_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jack")
        self.assertEqual(self.user.last_name, "Sparrow")
