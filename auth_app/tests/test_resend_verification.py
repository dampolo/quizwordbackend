from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory

from auth_app.api.views import ResendVerificationView


class ResendVerificationTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.factory = APIRequestFactory()
        self.url = reverse('resend-verification')

    def post(self, data):
        request = self.factory.post(self.url, data, format='json')
        return ResendVerificationView.as_view()(request)

    @patch('auth_app.api.views.EmailService.confirm_your_email')
    @patch('auth_app.api.views.User.objects.filter')
    def test_inactive_account_receives_email_with_cooldown(self, users, send):
        user = users.return_value.first.return_value
        first = self.post({'email': ' User@Example.com '})
        second = self.post({'email': 'user@example.com'})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data, second.data)
        users.assert_called_once_with(email__iexact='user@example.com', is_active=False)
        send.assert_called_once_with(user, send.call_args.args[1])

    @patch('auth_app.api.views.EmailService.confirm_your_email')
    @patch('auth_app.api.views.User.objects.filter')
    def test_unknown_or_active_account_has_same_response(self, users, send):
        users.return_value.first.return_value = None
        unknown = self.post({'email': 'unknown@example.com'})
        users.return_value.first.return_value = object()
        inactive = self.post({'email': 'inactive@example.com'})
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown.data, inactive.data)
        self.assertEqual(send.call_count, 1)

    def test_invalid_or_missing_email_is_rejected(self):
        for payload in ({}, {'email': 'invalid'}):
            with self.subTest(payload=payload):
                self.assertEqual(self.post(payload).status_code, 400)

    @patch('auth_app.api.views.User.objects.filter')
    def test_ip_request_limit(self, users):
        users.return_value.first.return_value = None
        for index in range(5):
            self.assertEqual(self.post({'email': f'user{index}@example.com'}).status_code, 200)
        self.assertEqual(self.post({'email': 'another@example.com'}).status_code, 429)

    def test_url_resolves_to_view(self):
        self.assertIs(resolve(self.url).func.view_class, ResendVerificationView)
