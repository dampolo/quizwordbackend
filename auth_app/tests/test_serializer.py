from django.test import TestCase
from auth_app.api.serializer import RegistrationSerializer


class RegistrationSerializerTest(TestCase):

    def test_serializer_with_valid_data(self):
        data = {
            "email": "john@example.com",
            "password": "Secret123!",
            "repeated_password": "Secret123!"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())
    
    def test_serializer_with_diffrent_password(self):
        data = {
            "email": "john@example.com",
            "password": "Secret123!",
            "repeated_password": "Secret123"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("repeated_password", serializer.errors)