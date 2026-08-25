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
