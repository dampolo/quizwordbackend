from types import SimpleNamespace
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from company_app.models import Company


class CompanyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('company')
        self.client.force_authenticate(user=SimpleNamespace(is_authenticated=True, is_superuser=True))
        self.payload = {
            'name': 'Example GmbH', 'street': 'Hauptstrasse', 'street_number': '1',
            'postcode': '10115', 'city': 'Berlin', 'owner_name': 'Example Owner',
            'tax_number': 'DE123456789', 'founding': '2000', 'email': 'office@example.com',
            'bank': 'Example Bank', 'bank_account': 'DE44500105175407324931',
            'swift_code': 'DEUTDEFF',
        }


    def test_only_superusers_can_access_every_method(self):
        for user in (None, SimpleNamespace(is_authenticated=True, is_superuser=False, is_staff=True)):
            self.client.force_authenticate(user=user)
            for method in ('get', 'post', 'patch', 'delete'):
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(self.url)
                    self.assertIn(response.status_code, (401, 403))
        self.assertFalse(Company.objects.exists())


    def test_full_crud_preserves_patch_contract(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        created = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['name'], self.payload['name'])
        self.assertEqual(self.client.get(self.url).data, created.data)
        self.assertEqual(self.client.post(self.url, self.payload, format='json').status_code, 409)
        updated = self.client.patch(self.url, {'name': 'Updated GmbH'}, format='json')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data, {'message': 'Die Daten wurden aktualisiert.'})
        self.assertEqual(Company.objects.get().name, 'Updated GmbH')
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        self.assertEqual(self.client.delete(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.payload, format='json').status_code, 201)


    def test_patch_creates_and_requires_full_data_when_missing(self):
        self.assertEqual(self.client.patch(self.url, {'name': 'Incomplete'}, format='json').status_code, 400)
        response = self.client.patch(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)


    def test_invalid_values_do_not_change_company(self):
        self.client.post(self.url, self.payload, format='json')
        for field, value in {
            'name': '   ', 'email': 'invalid', 'postcode': 'abc', 'city': '123',
            'tax_number': '123', 'founding': '9999', 'bank_account': 'invalid',
            'swift_code': 'invalid',
        }.items():
            with self.subTest(field=field):
                response = self.client.patch(self.url, {field: value}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
        self.assertEqual(Company.objects.get().name, self.payload['name'])


    def test_database_rejects_second_profile(self):
        Company.objects.create(**self.payload)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Company.objects.create(id=2, **self.payload)


    def test_concurrent_creation_returns_conflict(self):
        Company.objects.create(**self.payload)
        with patch('company_app.api.views.Company.objects.first', return_value=None):
            response = self.client.patch(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Company.objects.count(), 1)
