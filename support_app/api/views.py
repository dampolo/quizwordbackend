from rest_framework.views import APIView
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializer import SupportSerializer


class SupportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SupportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = request.get("name")
        email = request.get("email")
        message = request.get("message")

        context = {
            "name": name,
            "email": email,
            "message": message,
        }

        html_to_me = render_to_string("templates/email_to_me.html", context)
        email_to_support = EmailMessage(
            subject=f"Nachricht von {name}",
            body=html_to_me,
            # always your verified sender
            from_email=f"Quiz Word <{settings.DEFAULT_FROM_EMAIL}>",
            to=[settings.DEFAULT_FROM_EMAIL],
            reply_to=[email],
        )

        email_to_support.content_subtype = "html"
        email_to_support.send()

        # Confirmation email to USER
        html_answer = render_to_string("templates/email_answer.html", context)
        confirmation_email = EmailMessage(
            subject="Bestätigung von Quiz Word",
            body=html_answer,
            from_email=f"Quiz Word <{settings.DEFAULT_FROM_EMAIL}>",
            to=[email],
        )
        confirmation_email.content_subtype = "html"
        confirmation_email.send()

        return Response({'message': 'Wir haben dein E-Mail bekommen.'})
