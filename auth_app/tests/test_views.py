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
