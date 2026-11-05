from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory

from auth_app.api.views import ResendVerificationView
from auth_app.models import User


@patch("auth_app.api.views.EmailAddress.objects.filter")
@patch("auth_app.api.views.EmailService.confirm_your_email")
@patch("auth_app.api.views.User.objects.filter")
def test_inactive_account_receives_email_with_cooldown(
    self, users, send, email_addresses
):
    user = User(
        pk=123,
        username="test",
        email="user@example.com",
        is_active=True,
    )
    users.return_value.first.return_value = user
    email_addresses.return_value.exists.return_value = False

    first = self.post({"email": " User@Example.com "})
    second = self.post({"email": "user@example.com"})

    self.assertEqual(first.status_code, 200)
    self.assertEqual(first.data, second.data)
    users.assert_called_once_with(
        email__iexact="user@example.com",
        is_active=True,
    )
    send.assert_called_once_with(user, send.call_args.args[1])


@patch("auth_app.api.views.EmailAddress.objects.filter")
@patch("auth_app.api.views.EmailService.confirm_your_email")
@patch("auth_app.api.views.User.objects.filter")
def test_unknown_or_active_account_has_same_response(
    self, users, send, email_addresses
):
    email_addresses.return_value.exists.return_value = False

    users.return_value.first.return_value = None
    unknown = self.post({"email": "unknown@example.com"})

    users.return_value.first.return_value = User(
        pk=123,
        username="test",
        email="inactive@example.com",
        is_active=True,
    )
    unverified = self.post({"email": "inactive@example.com"})

    self.assertEqual(unknown.status_code, 200)
    self.assertEqual(unknown.data, unverified.data)
    self.assertEqual(send.call_count, 1)
