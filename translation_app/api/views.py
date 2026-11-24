import html

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from functools import lru_cache

from verbecc import CompleteConjugator
from verbecc.core.defs.types.exceptions import ConjugatorError


from translation_app.api.serializer import TranslateSerializer, VerbConjugationSerializer


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

        translated_text = html.unescape(translation)

        source_conjugations = BetweenCheck.get_conjugations(
            data["source"], data["text"]
        )

        target_conjugations = BetweenCheck.get_conjugations(
            data["target"], translated_text
        )

        return Response({
            "translated_text": translated_text,
            "source_conjugations": source_conjugations is not None,
            "target_conjugations": target_conjugations is not None,
            "source_results": source_conjugations,
            "target_results": target_conjugations,
        })


@lru_cache(maxsize=8)
def get_conjugator(language):
    return CompleteConjugator(language)


class VerbConjugationView(APIView):
    def get(self, request, language, verb):
        serializer = VerbConjugationSerializer(
            data={
                "language": language,
                "verb": verb,
            }
        )

        serializer.is_valid(raise_exception=True)

        language = serializer.validated_data["language"]
        verb = serializer.validated_data["verb"]

        conjugator = get_conjugator(language)

        try:
            results = conjugator.conjugate(verb)

        except (ConjugatorError, ValueError, KeyError) as exc:
            raise ValidationError(
                {
                    "message": False,
                }
            ) from exc

        return Response(
            {
                "language": language,
                "verb": verb,
                "conjugations": results.get_data(),
            }
        )


class BetweenCheck():
    @staticmethod
    def get_conjugations(language, verb):
        serializer = VerbConjugationSerializer(
            data={"language": language, "verb": verb}
        )
        if not serializer.is_valid():
            return None

        data = serializer.validated_data
        conjugator = get_conjugator(data["language"])

        try:
            result = conjugator.conjugate(data["verb"])
        except ConjugatorError:
            return None

        return result.get_data()
