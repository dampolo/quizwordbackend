from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError
from rest_framework import serializers, status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from auth_app.signals import issue_social_login_cookies


class GoogleTokenSerializer(serializers.Serializer):
    id_token = serializers.CharField(max_length=8192)


class GoogleLoginThrottle(AnonRateThrottle):
    scope = "google_login"
    rate = "20/minute"


class GoogleTokenLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]
    throttle_classes = [GoogleLoginThrottle]

    def post(self, request):
        serializer = GoogleTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = get_adapter(request).get_provider(request, "google")

        try:
            social_login = provider.verify_token(request, serializer.validated_data)
            claims = social_login.account.extra_data
            if not claims.get("sub") or "exp" not in claims:
                raise ValidationError("Missing Google ID token claims")
        except (KeyError, ValidationError):
            return Response(
                {"detail": "Google-Anmeldung konnte nicht bestätigt werden."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        account = SocialAccount.objects.select_related("user").filter(
            provider="google", uid=social_login.account.uid, user__is_active=True,
        ).first()
        if account is None:
            return Response(
                {"detail": "Melde dich zuerst im QuizWord-Web mit Google an, um dein Konto zu verknüpfen."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response = Response({"message": "Login erfolgreich"})
        issue_social_login_cookies(response, account.user, account.provider)
        return response
