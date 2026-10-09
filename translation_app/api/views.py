import html

import requests
from quizword_core import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from translation_app.api.serializer import TranslateSerializer


class TranslateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TranslateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            response = requests.post(
                "https://translation.googleapis.com/language/translate/v2",
                headers={
                    "X-goog-api-key": settings.GOOGLE_TRANSLATE_API_KEY,
                },
                json={
                    "q": data["text"],
                    "source": data["source"],
                    "target": data["target"],
                    "format": "text",
                },
                timeout=10,
            )
            response.raise_for_status()

            translation = response.json()["data"]["translations"][0][
                "translatedText"
            ]

        except (requests.RequestException, KeyError, IndexError, ValueError):
            return Response(
                {"detail": "Translation service is currently unavailable."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            "translated_text": html.unescape(translation),
        })