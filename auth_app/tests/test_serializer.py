from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import serializers

from auth_app.api.serializer import (ChangeEmailSerializer,
                                     CustomTokenObtainPairSerializer,
                                     RegistrationSerializer)

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
        self.assertIn("repeated_password", serializer.errors)
        self.assertEqual(
            serializer.errors["repeated_password"][0],
            "Passwörter stimmen nicht überein.",
        )

    def test_short_password_is_rejected(self):
        data = {
            "email": "test@example.com",
            "password": "Strong1!",
            "repeated_password": "Strong1!"
        }

        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(
            serializer.errors["password"][0],
            "Your password must contain at least 10 characters.",
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

    def test_email_is_normalized(self):
        data = {
            "email": "  TEST@Example.com  ",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!",
        }

        serializer = RegistrationSerializer(data=data)

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["email"],
            "test@example.com",
        )

    def test_duplicate_email_is_case_insensitive(self):

        User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password="StrongPass123!",
        )

        serializer = RegistrationSerializer(data={
            "email": "TEST@example.com",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_invalid_email_is_rejected(self):
        serializer = RegistrationSerializer(data={
            "email": "keine-email",
            "password": "StrongPass123!",
            "repeated_password": "StrongPass123!",
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class LoginSerializerTest(TestCase):
    def test_login_email_is_case_insensitive(self):
        user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True,
        )

        serializer = CustomTokenObtainPairSerializer(data={
            "email": "TEST@example.com",
            "password": "StrongPass123!",
        })

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(serializer.user.pk, user.pk)
        self.assertIn("access", serializer.validated_data)
        self.assertIn("refresh", serializer.validated_data)


class ChangeEmailSerializerTest(TestCase):
    def test_new_email_is_normalized(self):
        serializer = ChangeEmailSerializer()

        result = serializer.fields["new_email"].run_validation(
            "  NEU@Example.com  "
        )

        result = serializer.validate_new_email(result)

        self.assertEqual(result, "neu@example.com")

    def test_existing_email_is_rejected(self):
        User.objects.create_user(
            username="existing-user",
            email="existing@example.com",
            password="StrongPass123!",
        )

        serializer = ChangeEmailSerializer()

        with self.assertRaises(serializers.ValidationError):
            serializer.validate_new_email("EXISTING@example.com")

    def test_wrong_password_is_rejected(self):
        user = User.objects.create_user(
            username="test-user",
            email="test@example.com",
            password="StrongPass123!",
        )

        serializer = ChangeEmailSerializer(
            data={
                "password": "WrongPassword123!",
                "new_email": "neu@example.com",
            },
            context={
                "request": SimpleNamespace(user=user),
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_valid_email_change_is_accepted(self):
        user = User.objects.create_user(
            username="test-user",
            email="test@example.com",
            password="StrongPass123!",
        )

        serializer = ChangeEmailSerializer(
            data={
                "password": "StrongPass123!",
                "new_email": "  NEU@Example.com  ",
            },
            context={
                "request": SimpleNamespace(user=user),
            },
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )
        self.assertEqual(
            serializer.validated_data["new_email"],
            "neu@example.com",
        )
