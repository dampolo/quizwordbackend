from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.core import mail
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


class ChangeUsernameViewTest(APITestCase):
    def test_change_username_saves_new_username_and_sends_email(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "username": "newname"
        }

        response = self.client.patch(
            reverse("change-username"),
            payload,
            format="json"
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user.refresh_from_db()

        self.assertEqual(user.username, payload["username"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_duplicate_username_is_rejected_without_sending_email(self):
        user1 = User.objects.create_user(
            username="oldname",
            email="test@example1.com",
            password="StrongPass123!",
            is_active=True
        )

        user2 = User.objects.create_user(
            username="newname",
            email="test@example2.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user1)

        payload = {
            "username": "NewName"
        }

        response = self.client.patch(
            reverse("change-username"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)

        user1.refresh_from_db()

        self.assertEqual(user1.username, "oldname")
        self.assertEqual(len(mail.outbox), 0)
