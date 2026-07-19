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

        read_only_fields = ['id','created_at', 'updated_at', 'customer_number']
    
    def validate_postcode(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Post code must contain numbers only.")
        return value
