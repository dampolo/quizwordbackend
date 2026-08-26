from rest_framework import serializers

from auth_app.models import User


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'customer_number',
            'image',
            'title',
            'username',
            'password',
            'first_name',
            'last_name',
            'street',
            'street_number',
            'postcode',
            'city',
            'email',
            'phone',
            'has_subscription',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = ['id', 'customer_number', 'password',
                            'email', 'has_subscription', 'is_active', 'created_at', 'updated_at']

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
        if validated_data.get("image", "not-provided") is None:
            if instance.image:
                instance.image.delete(save=False)

        return super().update(instance, validated_data)

class ChangeUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Dieser Benutzername wird bereits verwendet."
            )
        if len(value) < 4 or len(value) > 10:
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
