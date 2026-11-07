from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, APITestCase

from auth_app.validators import CustomPasswordValidator


class CustomPasswordValidatorTest(SimpleTestCase):
    def test_password_with_nine_characters_is_rejected(self):
        validator = CustomPasswordValidator()
        password = "Secret12!"

        with self.assertRaises(ValidationError) as error:
            validator.validate(password)

        self.assertIn(
            "Your password must contain at least 10 characters.", error.exception.messages)

    def test_password_with_ten_characters_is_accepted(self):
        validator = CustomPasswordValidator()
        password = "Secret123!"

        validator.validate(password)

    def test_password_without_digit_is_rejected(self):
        validator = CustomPasswordValidator()
        password = "SecretABC!"

        with self.assertRaises(ValidationError) as error:
            validator.validate(password)

        self.assertIn(
            "At least one digit is required.", error.exception.messages)

    def test_password_reports_both_length_and_digit_errors(self):
        validator = CustomPasswordValidator()
        password = "SecretAB!"

        with self.assertRaises(ValidationError) as error:
            validator.validate(password)

        self.assertIn(
            "Your password must contain at least 10 characters.", error.exception.messages)
        
        self.assertIn(
            "At least one digit is required.", error.exception.messages)
