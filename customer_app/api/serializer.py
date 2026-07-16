from rest_framework import serializers
from auth_app.models import User


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
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
            'has_portfolio',
            'has_subscription',
            'is_active',
        ]

        read_only_fields = ['created_at', 'updated_at', 'user', 'customer_number']
    
    def validate_post_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Post code must contain numbers only.")
        return value
