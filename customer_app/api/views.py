from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .serializer import (ChangePasswordSerializer, ChangeUsernameSerializer,
                         CustomerProfileSerializer,
                         DeleteAccountSerializer)


# This method show the whole profile from Customer
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    serializer_class = CustomerProfileSerializer
    # Customer can see only his profile

    def get_object(self):
        return self.request.user


class ChangeUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangeUsernameSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.username = serializer.validated_data['username']
        user.save(update_fields=['username'])

        return Response({
            "detail": "Benutzername wurde erfolgreich geändert."
        })


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = DeleteAccountSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        user = request.user

        html_content = render_to_string(
            'templates/delete_your_account.html',
        )

        email_message = EmailMessage(
            subject='Dein Quiz Word Konto wurde gelöscht',
            body=html_content,
            from_email=f"Quiz Word <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email],
        )

        email_message.content_subtype = 'html'
        email_message.send()

        user.delete()

        return Response(
            {'detail': 'Dein Konto wurde gelöscht.'},
            status=status.HTTP_200_OK
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(
            serializer.validated_data['new_password']
        )

        user.save()

        return Response(
            {
                'detail': 'Passwort wurde erfolgreich geändert.'
            },
            status=status.HTTP_200_OK
        )
