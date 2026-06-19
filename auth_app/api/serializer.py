from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'repeated_password', 'role']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
             'role': {
                'required': False
            },
            'email': {
                'required': True
            }
        }

    def validate_repeated_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def create(self, validated_data):
        print(validated_data)
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
            raise serializers.ValidationError('Ungültige Email oder Passwort')

        if not user.check_password(password):
            raise serializers.ValidationError('Ungültige Email oder Passwort')

        data = super().validate({
            'username': user.username,
            'password': password
        })

        return data

