from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language
from rest_framework.exceptions import PermissionDenied

from vocabulary_app.api.serializer import (
    VocabularyCategorySerializer,
    VocabularyWordSerializer,
    LanguageSerializer
)


class LanguageViewSet(viewsets.ModelViewSet):
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Language.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VocabularyCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = VocabularyCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {"target_language": ["exact"]}
    filterset_fields = {
        "target_language__language_name": ["exact"],
    }

    def get_queryset(self):
        return VocabularyCategory.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VocabularyWordViewSet(viewsets.ModelViewSet):
    serializer_class = VocabularyWordSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        "category__target_language__language_name": ["exact"],
    }
    search_fields = ["source_word", "target_word"]

    def get_queryset(self):
        return VocabularyWord.objects.filter(
            category__user=self.request.user)


    def perform_create(self, serializer):
        category = serializer.validated_data.pop("category", None)
        language = serializer.validated_data.pop("language", None)

        if category:
            if category.user != self.request.user:
                raise PermissionDenied(
                    "You cannot add words to another user's category."
                )

            serializer.save(category=category)
            return

        if language:
            if language.user != self.request.user:
                raise PermissionDenied(
                    "You cannot use another user's language."
                )
        else:
            language, _ = Language.objects.get_or_create(
                user=self.request.user,
                language_name="Without",
            )

        category, _ = VocabularyCategory.objects.get_or_create(
            user=self.request.user,
            target_language=language,
            name="STANDARD",
        )

        serializer.save(category=category)
