import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from rest_framework import serializers

from auth_app.models import User


class CustomPasswordValidator:
    def validate(self, password, user=None):
        errors = []
        if len(password) < 10:
            errors.append(_("Your password must contain at least 10 characters."))
        if not re.search(r'[A-Z]', password):
            errors.append(_("At least one uppercase letter is required."))
        if not re.search(r'[a-z]', password):
            errors.append(_("At least one lowercase letter is required."))
        if not re.search(r'[0-9]', password):
            errors.append(_("At least one digit is required."))
        if not re.search(r'[@$!%+\-/*?&]', password):
            errors.append(_("At least one special character is required (@ $ ! % + - / * ? &)."))
        if re.search(r'\s', password):
            errors.append(_("Password must not contain any spaces."))        
        if errors:
            raise ValidationError(errors)
        
    def get_help_text(self):
        return _(
            "Your password must meet the following requirements:",
            "- At least 10 characters long",
            "- At least one uppercase letter (A-Z)",
            "- At least one lowercase letter (a-z)",
            "- At least one digit (0-9)",
            "- At least one special character (@ $ ! % + - / * ? &)",
            "- No spaces"
        )

class UsernameValidator:
    def validate(self, value, instance=None):
        if not 4 <= len(value) <= 10:
            raise serializers.ValidationError(
                "Der Benutzername muss zwischen 4 und 10 Zeichen lang sein."
            )

        has_letter_or_digit = any(
            character.isalnum() for character in value
        )

        has_only_allowed_characters = all(
            character.isalnum() or character in "-_@"
            for character in value
        )

        if not has_letter_or_digit or not has_only_allowed_characters:
            raise serializers.ValidationError(
                "Erlaubt sind Buchstaben, Zahlen und -, _, @. "
                "Mindestens ein Buchstabe oder eine Zahl ist erforderlich."
            )

        users = User.objects.filter(username__iexact=value)

        if instance is not None:
            users = users.exclude(pk=instance.pk)

        if users.exists():
            raise serializers.ValidationError(
                "Dieser Benutzername wird bereits verwendet."
            )

        return value