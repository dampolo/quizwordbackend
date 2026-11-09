from unittest.mock import patch

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

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

        self.assertEqual(profile_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

        self.client.post(reverse("token_refresh"))

        profile_response = self.client.get(reverse("me"))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_refresh_without_refresh_cookie_is_rejected(self):

        refresh_response = self.client.post(reverse("token_refresh"))

        self.assertEqual(refresh_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

        self.assertNotIn("access_token", refresh_response.cookies)

@patch("auth_app.api.views.ResendVerificationView.throttle_classes", [])
class PasswordResetViewTest(APITestCase):
    def test_password_reset_saves_new_password(self):

        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        payload = {
            "password": "StrongPass124!",
            "uid": uid,
            "token": token,

        }

        response = self.client.post(
            reverse("reset-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password(payload["password"]))

    def test_password_reset_with_invalid_token_is_rejected(self):

        old_password = "StrongPass123!"

        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password=old_password,
            is_active=True
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        payload = {
            "password": "StrongPass124!",
            "uid": uid,
            "token": "invalid-token",
        }

        response = self.client.post(
            reverse("reset-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertTrue(user.check_password(old_password))

    def test_password_reset_token_cannot_be_reused(self):

        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        first_new_password = "StrongPass124!"

        payload = {
            "password": first_new_password,
            "uid": uid,
            "token": token,
        }

        response = self.client.post(
            reverse("reset-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = {
            "password": "StrongPass125!",
            "uid": uid,
            "token": token,
        }

        response = self.client.post(
            reverse("reset-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user.refresh_from_db()
        self.assertTrue(user.check_password(first_new_password))

    def test_forgot_password_sends_reset_email(self):

        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
        }

        response = self.client.post(
            reverse("forgot-password"),
            payload,
            format="json"
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertIn(f"reset-password/{uid}/", mail.outbox[0].body)

    def test_forgot_password_does_not_send_email_for_unknown_address(self):
        payload = {
            "email": "unknown@example.com",
        }

        response = self.client.post(
            reverse("forgot-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_returns_same_response_for_known_and_unknown_email(self):
        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test@example.com",
        }

        known_response = self.client.post(
            reverse("forgot-password"),
            payload,
            format="json"
        )

        payload = {
            "email": "unknown@example.com",
        }

        unknown_response = self.client.post(
            reverse("forgot-password"),
            payload,
            format="json"
        )

        self.assertEqual(known_response.status_code,
                         unknown_response.status_code)
        self.assertEqual(known_response.data, unknown_response.data)

    def test_verify_email_marks_address_as_verified(self):
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        email_address = EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        response = self.client.get(
            reverse("verify-email", kwargs={"uidb64": uid, "token": token}),
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        email_address.refresh_from_db()
        self.assertTrue(email_address.verified)

    def test_verify_email_with_invalid_token_keeps_address_unverified(self):
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        email_address = EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = self.client.get(
            reverse("verify-email",
                    kwargs={"uidb64": uid, "token": "invalid-token"}),
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        email_address.refresh_from_db()
        self.assertFalse(email_address.verified)

    def test_change_email_saves_new_address_as_unverified(self):
        password = "StrongPass123!"
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password=password,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "password": password,
            "new_email": "newemail@example.com"
        }

        response = self.client.post(
            reverse("change-email"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

        user.refresh_from_db()
        self.assertEqual(user.email, payload["new_email"])
        email_address = EmailAddress.objects.get(
            user=user,
            email=payload["new_email"],
        )
        self.assertFalse(email_address.verified)

    def test_change_email_with_wrong_password_keeps_old_address(self):
        old_email = "test@example.com"

        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "password": "WrongPass123!",
            "new_email": "newemail@example.com"
        }

        response = self.client.post(
            reverse("change-email"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertEqual(user.email, old_email)

    def test_change_email_requires_authentication(self):
        password = "StrongPass123!"
        old_email = "test@example.com"

        user = User.objects.create_user(
            username="existing-user",
            email=old_email,
            password=password,
            is_active=True
        )

        payload = {
            "password": password,
            "new_email": "newemail@example.com"
        }

        response = self.client.post(
            reverse("change-email"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        user.refresh_from_db()
        self.assertEqual(user.email, old_email)

    def test_change_email_rejects_address_used_by_another_user(self):
        user1_email = "test1@example.com"

        user1 = User.objects.create_user(
            username="existing-user1",
            email=user1_email,
            password="StrongPass123!",
            is_active=True
        )

        password = "StrongPass1234!"
        old_email2 = "test2@example.com"

        user2 = User.objects.create_user(
            username="existing-user2",
            email=old_email2,
            password=password,
            is_active=True
        )

        self.client.force_authenticate(user=user2)

        payload = {
            "password": password,
            "new_email": user1_email
        }

        response = self.client.post(
            reverse("change-email"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user1.refresh_from_db()
        self.assertEqual(user1.email, user1_email)
        user2.refresh_from_db()
        self.assertEqual(user2.email, old_email2)

    def test_resend_verification_skips_verified_address(self):
        user = User.objects.create_user(
            username="existing-user",
            email="test2@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": "test2@example.com",
        }

        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=True,
            primary=True,
        )

        response = self.client.post(
            reverse("resend-verification"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_sends_email_to_unverified_address(self):
        user = User.objects.create_user(
            username="existing-user",
            email="resend-unverified@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": user.email,
        }

        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True,
        )

        response = self.client.post(
            reverse("resend-verification"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_resend_verification_sends_only_one_email_during_cooldown(self):
        user = User.objects.create_user(
            username="existing-user",
            email="resend-cooldown@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "email": user.email,
        }

        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True,
        )

        response = self.client.post(
            reverse("resend-verification"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

        response = self.client.post(
            reverse("resend-verification"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_resend_verification_returns_same_response_for_known_and_unknown_email(self):
        user = User.objects.create_user(
            username="existing-user",
            email="resend-email@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload1 = {
            "email": user.email,
        }

        payload2 = {
            "email": "resend-unknown_email@example.com",
        }

        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True,
        )

        known_response = self.client.post(
            reverse("resend-verification"),
            payload1,
            format="json"
        )

        unknown_response = self.client.post(
            reverse("resend-verification"),
            payload2,
            format="json"
        )

        print("TEST: ", unknown_response, known_response)

        self.assertEqual(known_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown_response.status_code, known_response.status_code)
        self.assertEqual(unknown_response.data, known_response.data)
