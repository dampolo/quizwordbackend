from rest_framework import status
from rest_framework.views import APIView, View
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializer import RegistrationSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from auth_app.models import User
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import logout

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            saved_account.is_active = False
            saved_account.save() 
            # EmailService.confirm_your_email(saved_account, request)

            data = {
                'username': saved_account.username,
                'email': saved_account.email,
                'user_id': saved_account.pk,
                'customer_number': saved_account.customer_number,
            }
            return Response(data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Login
class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data['refresh']
        access = serializer.validated_data['access']

        response = Response({'message': 'Login erfolgreich'})

        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=True,
            samesite='Lax',
            # path='/'
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='Lax',
            # path='/'
        )

        return response


class CookieTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {'message': 'Refresh token not found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {'message': 'Refresh token invalid'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")

        response = Response({'message': 'Access Token refreshed'})

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
        )

        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'role': request.user.role
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # This method logout remove sessionid as well
        logout(request)
        response = Response({'message': 'Logged out'})
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')

        return response


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If the email exists, a reset link was sent.'})

        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = f"http://127.0.0.1:4200/reset-password/{uid}/{token}"

        html_content = render_to_string(
            'templates/forgot_password.html',
            {
                'reset_link': reset_link,
            }
        )

        email_message = EmailMessage(
            subject='Passwort zurücksetzen',
            body=html_content,
            from_email=f"Start in Krypto <{settings.DEFAULT_FROM_EMAIL}>",
            to=[email],
        )

        email_message.content_subtype = 'html'
        email_message.send()

        return Response({'message': 'Reset link sent'})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')
        print('test')
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'error': "Invalid link"}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'error': "Token is invalid or expired"}, status=400)

        user.set_password(password)
        user.save()

        return Response({'message': 'Password reset successful'})

class EmailService():
    
    @staticmethod
    def confirm_your_email(user, request):
        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        active_link = f"{settings.DEFAULT_API}kurse/verify-email/{uidb64}/{token}"

        html_content= render_to_string(
            'templates/confirm_your_email.html',
            {
                'active_link': active_link
            }
        )

        email_message = EmailMessage(
            subject='Bestätige deine E-Mail',
            body=html_content,
            from_email=f"Start in Krypto <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email],
        )

        email_message.content_subtype = 'html'
        email_message.send()

        return Response({'message': 'Email confirmation link sent'})

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):

            return Response(
                {"error": "Invalid verification link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                {"error": "Verification link is invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_active:
            return Response(
                {"message": "Account already verified"},
                status=status.HTTP_200_OK
            )
        print("TOKEN VALID, ACTIVATING USER")
        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            {"message": "Email successfully verified"},
            status=status.HTTP_200_OK
        )