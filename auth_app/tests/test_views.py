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

    def test_registration_normalizes_email(self):
        payload = {
            "email": "TEST@Example.com",
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

        self.assertEqual(response.data["email"], "test@example.com")

        user = User.objects.get(pk=response.data["user_id"])

        self.assertEqual(user.email, "test@example.com")


class LoginViewTest(APITestCase):
    def test_login_sets_auth_cookies(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

        access_cookie = response.cookies["access_token"]
        refresh_token = response.cookies["refresh_token"]

        self.assertTrue(access_cookie["httponly"])
        self.assertTrue(refresh_token["httponly"])

    def test_login_with_wrong_password_is_rejected(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123?",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_login_with_inactive_user_is_rejected(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=False
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_logged_in_user_can_get_own_profile(self):
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["id"], user.pk)
        self.assertEqual(profile_response.data["username"], user.username)

    def test_anonymous_user_cannot_get_profile(self):
        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("id", profile_response.data)

    def test_profile_shows_verified_email(self):
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )

        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=True,
            primary=True,
        )

        profile_response = self.client.get(reverse("me"))

        self.assertIs(profile_response.data["is_email_verified"], True)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_logout_blocks_profile_access(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )

        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        logout_response = self.client.post(
            reverse("logout"),
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_restores_profile_access(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(
            reverse("token_obtain_pair"),
            payload,
            format="json"
        )
        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        del self.client.cookies["access_token"]

        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.post(reverse("token_refresh"))

        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
