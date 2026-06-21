from django.test import TestCase
from auth_app.api.serializer import RegistrationSerializer
from django.contrib.auth import get_user_model
User = get_user_model()


class RegistrationSerializerTest(TestCase):

    def test_serializer_with_valid_data(self):
        data = {
            "email": "john@example.com",
            "password": "Secret123!",
            "repeated_password": "Secret123!"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_passwords_must_match(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "repeated_password": "DifferentPass123!"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(
            serializer.errors["password"][0],
            "Passwords don't match."
        )

    def test_email_required(self):
        data = {
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_create_user(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertEqual(user.email, "test@example.com")

    def test_password_is_hashed(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!"
        }

        serializer = RegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertTrue(
            user.check_password("StrongPass123!")
        )
