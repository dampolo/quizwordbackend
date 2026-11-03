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

    for name, token in (("access_token", access), ("refresh_token", refresh)):
        response.set_cookie(
            key=name,
            value=str(token),
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite="Lax",
            path="/",
            max_age=int(token.lifetime.total_seconds()),
        )
