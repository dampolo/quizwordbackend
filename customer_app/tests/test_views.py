from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
User = get_user_model()


class ChangePasswordViewTest(APITestCase):
    def test_change_password_saves_new_password(self):
        password = "StrongPass123!"
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password=password,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "old_password": password,
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user.refresh_from_db()

        self.assertTrue(user.check_password(payload["new_password"]))
        self.assertFalse(user.check_password(password))

    def test_wrong_old_password_does_not_change_password(self):
        password = "StrongPass123!"
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password=password,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "old_password": "WrongPass123!",
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)

        user.refresh_from_db()

        self.assertFalse(user.check_password(payload["new_password"]))
        self.assertTrue(user.check_password(password))
        self.assertIn("old_password", response.data)

    def test_unauthenticated_user_cannot_change_password(self):
        payload = {
            "old_password": "WrongPass123!",
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED, response.data)

