from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from auth_app.models import User
from auth_app.validators import CustomPasswordValidator, UsernameValidator
import re
import unicodedata


class CustomerProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'customer_number',
            'image',
            'title',
            'username',
            'first_name',
            'last_name',
            'street',
            'street_number',
            'postcode',
            'city',
            'email',
            'phone',
            'has_subscription',
            'is_superuser',
            'is_active',
            'created_at'
        ]

        read_only_fields = ['id', 'customer_number',
                            'email', 'is_active', 'created_at', 'is_superuser']

    def validate_first_name(self, value):
        if not value:
            return value

        if not any(character.isalpha() for character in value):
            raise serializers.ValidationError(
                "Der Vorname muss mindestens einen Buchstaben enthalten."
            )

        return value

    def validate_last_name(self, value):
        if not value:
            return value

        if not any(character.isalpha() for character in value):
            raise serializers.ValidationError(
                "Der Nachname muss mindestens einen Buchstaben enthalten."
            )

        return value

    def validate_city(self, value):
        if not value:
            return value

        if not any(character.isalpha() for character in value):
            raise serializers.ValidationError(
                "Der Ort muss mindestens einen Buchstaben enthalten."
            )

        return value

    def validate_street(self, value):
        if not value:
            return value

        if not any(character.isalpha() for character in value):
            raise serializers.ValidationError(
                "Die Straße muss mindestens einen Buchstaben enthalten."
            )

        return value

    def validate_street_number(self, value):
        if not value:
            return value

        if not any(character.isdecimal() for character in value):
            raise serializers.ValidationError(
                "Die Hausnummer muss mindestens eine Ziffer enthalten."
            )

        return value

    def validate_phone(self, value):
        if not value:
            return value

        if not re.fullmatch(r"\+?[0-9 ()-]+", value):
            raise serializers.ValidationError(
                "Bitte gib eine Telefonnummer mit Ziffern und "
                "optional +, Leerzeichen, Klammern oder Bindestrichen ein."
            )

        digits = re.sub(r"[^0-9]", "", value)

        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError(
                "Die Telefonnummer muss zwischen 7 und 15 Ziffern enthalten."
            )

        return value

    def validate_postcode(self, value):
        if not value:
            return value

        has_letter_or_digit = any(
            character.isalnum() for character in value
        )

        has_only_allowed_characters = all(
            character.isalnum()
            or unicodedata.category(character).startswith("M")
            or character in " -"
            for character in value
        )

        if not has_letter_or_digit or not has_only_allowed_characters:
            raise serializers.ValidationError(
                "Die Postleitzahl darf nur Buchstaben, Ziffern, "
                "Leerzeichen und Bindestriche enthalten."
            )

        return value

    def validate_image(self, value):
        max_size = 2 * 1024 * 1024

        if value and value.size > max_size:
            raise serializers.ValidationError(
                "Das Bild darf maximal 2 MB groß sein."
            )

        return value

    def update(self, instance, validated_data):
        image_was_provided = "image" in validated_data
        old_image = instance.image

        instance = super().update(instance, validated_data)

        if (image_was_provided and old_image and old_image.name != instance.image.name):
            old_image.delete(save=False)

        return instance


class ChangeUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        return UsernameValidator().validate(
            value,
            instance=self.context["request"].user,
        )


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if user.is_superuser:
            raise serializers.ValidationError(
                {"detail": "Ein Superuser-Konto kann nicht gelöscht werden."}
            )

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError(
                {"password": "Dein Passwort ist nicht korrekt."}
            )

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    repeated_new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Das aktuelle Passwort ist ungültig."
            )

        return value

    def validate_new_password(self, value):
        try:
            CustomPasswordValidator().validate(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)

        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["repeated_new_password"]:
            raise serializers.ValidationError({
                "repeated_new_password": "Passwörter stimmen nicht überein."
            })

        return attrs
