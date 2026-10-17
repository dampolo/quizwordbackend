from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from auth_app.models import User
from auth_app.validators import CustomPasswordValidator


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

    def validate_postcode(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError(
                "Post code must contain numbers only.")
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

        if( image_was_provided and old_image and old_image.name != instance.image.name):
            old_image.delete(save=False)

        return instance
    
class ChangeUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Dieser Benutzername wird bereits verwendet."
            )
        if len(value) < 4 or len(value) > 10 or any(character.isspace() for character in value):
            raise serializers.ValidationError(
                "Mindestens 4, maximal 10 Zeichen und keine Leerzeichen."
            )

        return value


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