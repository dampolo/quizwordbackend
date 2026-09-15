import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

class SupportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    message = serializers.CharField(max_length=5000)
    captcha_token = serializers.CharField(write_only=True)

    def validate_captcha_token(self, value):
        response = requests.post(
             "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": value
            },
            timeout=5
        )
        result = response.json()

        if not result.get("success"):
            raise serializers.ValidationError(
                "Captcha konnte nicht bestätigt werden."
            )

        return value