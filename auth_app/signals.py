from allauth.account.signals import user_logged_in
from django.conf import settings
from django.dispatch import receiver
from rest_framework_simplejwt.tokens import RefreshToken


@receiver(user_logged_in, dispatch_uid="auth_app.social_login_jwt_cookies")
def set_social_login_cookies(sender, request, response, user, **kwargs):
    sociallogin = kwargs.get("sociallogin")
    if sociallogin is None or not user.is_active:
        return

    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["auth_provider"] = sociallogin.account.provider
    access = refresh.access_token

    response.set_cookie(
        key="access_token",
        value=str(access),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="Lax",
        path="/",
        max_age=int(access.lifetime.total_seconds()),
    )


    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="Lax",
        path="/",
        max_age=int(refresh.lifetime.total_seconds()),
    )
