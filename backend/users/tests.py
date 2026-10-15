from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthenticationApiTests(APITestCase):
    def test_register_returns_user_and_jwt_pair(self):
        response = self.client.post(reverse("auth-register"), {
            "username": "alex", "email": "alex@example.com", "password": "A-safe-password-123",
            "timezone": "Europe/Samara",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["username"], "alex")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(username="alex").exists())

    def test_login_me_and_logout(self):
        user = User.objects.create_user(username="alex", email="alex@example.com", password="A-safe-password-123")
        login = self.client.post(reverse("auth-login"), {
            "username": user.username, "password": "A-safe-password-123",
        }, format="json")

        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertEqual(login.data["user"]["id"], user.id)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(self.client.get(reverse("auth-me")).data["username"], "alex")
        self.assertEqual(
            self.client.post(reverse("auth-logout"), {"refresh": login.data["refresh"]}, format="json").status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_invalid_credentials_and_missing_auth_are_rejected(self):
        User.objects.create_user(username="alex", password="A-safe-password-123")
        response = self.client.post(reverse("auth-login"), {"username": "alex", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, status.HTTP_401_UNAUTHORIZED)
