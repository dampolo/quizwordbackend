from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from allauth.account.models import EmailAddress

User = get_user_model()


class RegistrationViewTest(APITestCase):
    def test_user_can_register(self):
        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!"
        }

        response = self.client.post(
            reverse("create-account"),
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(email="test@example.com")

        self.assertEqual(user.email, "test@example.com")

        self.assertTrue(user.is_active)

        self.assertTrue(
            EmailAddress.objects.filter(
                user=user,
                email=user.email,
                verified=False,
                primary=True,
            ).exists()
        )

        self.assertTrue(user.check_password("StrongPass123!"))

        self.assertEqual(response.data["email"], "test@example.com")

        self.assertEqual(response.data["username"], "test@example.com")

        self.assertEqual(response.data["user_id"], user.pk)

        self.assertEqual(
            response.data["customer_number"], user.customer_number)

    def test_registration_with_short_password_is_rejected(self):
        payload = {
            "email": "test@example.com",
            "password": "Strong1!",
            "repeated_password": "Strong1!"
        }

        response = self.client.post(
            reverse("create-account"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(User.objects.filter(
            email=payload["email"]).exists())

    def test_registration_with_mismatched_passwords_is_rejected(self):
        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "repeated_password": "DifferentPass123!"
        }

        response = self.client.post(
            reverse("create-account"),
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertFalse(User.objects.filter(
            email=payload["email"]).exists())

        self.assertIn("repeated_password", response.data)

        self.assertEqual(
            response.data["repeated_password"][0],
            "Passwörter stimmen nicht überein.",
        )

    def test_registration_with_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
        )
        
        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!"
        }

        response = self.client.post(
            reverse("create-account"),
            payload,
            format="json"
        )

        matching_users = User.objects.filter(email__iexact=payload["email"])

        self.assertEqual(matching_users.count(), 1)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
