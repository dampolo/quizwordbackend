from types import SimpleNamespace
from unittest.mock import patch

from allauth.account.signals import user_logged_in
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from auth_app.api.google_login import GoogleTokenLoginView
from auth_app.api.views import MeView
from auth_app.models import User


class SocialLoginTests(SimpleTestCase):
    @override_settings(AUTH_COOKIE_SECURE=True)
    def test_completed_google_login_sets_jwt_cookies_on_redirect(self):
        user = User(pk=123, username="test", email="test@example.com")
        response = HttpResponseRedirect("http://127.0.0.1:5173/my-quiz/")
        user_logged_in.send(
            sender=User,
            request=APIRequestFactory().get("/accounts/google/login/callback/"),
            response=response,
            user=user,
            sociallogin=SimpleNamespace(
                account=SimpleNamespace(provider="google")),
        )

        for name, token_class in (("access_token", AccessToken), ("refresh_token", RefreshToken)):
            cookie = response.cookies[name]
            token = token_class(cookie.value)
            self.assertEqual(token["user_id"], str(user.pk))
            self.assertEqual(token["auth_provider"], "google")
            self.assertEqual(token["role"], user.role)
            self.assertTrue(cookie["httponly"])
            self.assertTrue(cookie["secure"])
            self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(response["Location"],
                         "http://127.0.0.1:5173/my-quiz/")

    def test_regular_allauth_login_does_not_issue_social_tokens(self):
        response = HttpResponseRedirect("/")
        user_logged_in.send(
            sender=User, request=None, response=response, user=User(pk=123),
        )
        self.assertNotIn("access_token", response.cookies)

    @patch("auth_app.api.views.EmailAddress.objects.filter")
    @patch(
        "auth_app.api.views.UserLanguageStatus.languages_active",
        return_value=False,
    )
    def test_me_accepts_session_authentication_without_token(
        self, languages_active, email_addresses
    ):
        email_addresses.return_value.exists.return_value = False

        request = APIRequestFactory().get("/api/me/")
        force_authenticate(
            request,
            user=User(pk=123, username="test"),
        )

        response = MeView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["auth_provider"])
        self.assertFalse(response.data["is_email_verified"])

    @patch("auth_app.api.google_login.get_adapter")
    def test_google_login_rejects_invalid_token_without_setting_cookies(self, mock_get_adapter):
        mock_adapter = mock_get_adapter.return_value
        mock_provider = mock_adapter.get_provider.return_value
        mock_provider.verify_token.side_effect = ValidationError(
            "Ungültiger Token")

        payload = {
            "id_token": "unvalid-test-token"
        }

        request = APIRequestFactory().post(
            "/api/token/google/",
            payload,
            format="json",
        )

        response = GoogleTokenLoginView.as_view()(request)

        self.assertEqual(response.status_code, 401)

        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)
        mock_provider.verify_token.assert_called_once()

    def test_google_login_rejects_missing_id_token(self):
        request = APIRequestFactory().post(
            "/api/token/google/",
            {},
            format="json",
        )

        response = GoogleTokenLoginView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        print("Profile: ", response.data)
        self.assertIn("id_token", response.data)

    @patch("auth_app.api.google_login.get_adapter")
    def test_google_login_rejects_unlinked_account(self, mock_get_adapter):
        mock_adapter = mock_get_adapter.return_value
        mock_provider = mock_adapter.get_provider.return_value
        mock_provider.verify_token.return_value = SimpleNamespace(
            account=SimpleNamespace(
                uid="google-test-user",
                extra_data={"sub": "google-test-user", "exp": 2_000_000_000},
            ),
        )
        with patch("auth_app.api.google_login.SocialAccount.objects.select_related") as mock_select_related:
            mock_select_related.return_value.filter.return_value.first.return_value = None

            request = APIRequestFactory().post(
                "/api/token/google/",
                {"id_token": "test-token"},
                format="json",
            )

            response = GoogleTokenLoginView.as_view()(request)
            self.assertEqual(response.status_code, 403)

    @patch("auth_app.api.google_login.get_adapter")
    def test_google_login_sets_cookies_for_linked_account(self, mock_get_adapter):
        mock_adapter = mock_get_adapter.return_value
        mock_provider = mock_adapter.get_provider.return_value
        mock_provider.verify_token.return_value = SimpleNamespace(
            account=SimpleNamespace(
                uid="google-test-user",
                extra_data={"sub": "google-test-user", "exp": 2_000_000_000},
            ),
        )

        user = User(pk=123, username="test", email="test@example.com")
        linked_account = SimpleNamespace(user=user, provider="google")

        with patch("auth_app.api.google_login.SocialAccount.objects.select_related") as mock_select_related:
            mock_select_related.return_value.filter.return_value.first.return_value = linked_account

            request = APIRequestFactory().post(
                "/api/token/google/",
                {"id_token": "test-token"},
                format="json",
            )
            
            response = GoogleTokenLoginView.as_view()(request)
            self.assertEqual(response.status_code, 200)
            self.assertIn("access_token", response.cookies)
            self.assertIn("refresh_token", response.cookies)