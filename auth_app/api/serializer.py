from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from auth_app.validators import CustomPasswordValidator

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'repeated_password', 'role']
        extra_kwargs = {
            'role': {
                'required': False
            },
            'email': {
                'required': True
            }
        }

    def get_help_text(self, obj):
        return CustomPasswordValidator().get_help_text()

    def validate_password(self, value):
        try:
            CustomPasswordValidator().validate(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        return value
    
    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError({
                "repeated_password": "Passwörter stimmen nicht überein."
            })

        return attrs

    def create(self, validated_data):
        password = validated_data['password']
        validated_data.pop('repeated_password')

        user = User(
            email=validated_data['email'],
            username=validated_data['email'],
        )

        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'username' in self.fields:
            self.fields.pop('username')

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Overwrite the token
        token['role'] = user.role

        return token

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'detail': 'Ungültige Email oder Passwort.'})

        if not user.check_password(password):
            raise serializers.ValidationError(
                {'detail': 'Ungültige Email oder Passwort.'})

        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': 'Du hast dein E-Mail nicht aktivert.'})

        data = super().validate({
            'username': user.username,
            'password': password
        })

        return data


class ChangeEmailSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    new_email = serializers.EmailField()

    def validate_password(self, password):
        user = self.context["request"].user

        if not user.check_password(password):
            raise serializers.ValidationError("Passwort ist falsch.")

        return password

    def validate_new_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Diese E-Mail-Adresse wird bereits verwendet."
            )

        return email


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
