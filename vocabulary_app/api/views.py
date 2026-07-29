from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language, UserLanguages
from rest_framework.exceptions import PermissionDenied
from vocabulary_app import pagination
from rest_framework import generics

from vocabulary_app.api.serializer import (
    VocabularyCategorySerializer,
    VocabularyWordSerializer,
    LanguageSerializer,
    UserLanguageSerializer
)


class LanguageViewSet(viewsets.ModelViewSet):
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Language.objects.all()

    def perform_create(self, serializer):
        serializer.save()

class UserLanguageViewSet(generics.RetrieveUpdateAPIView):
    serializer_class = UserLanguageSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return UserLanguages.objects.get(user=self.request.user)

class VocabularyCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = VocabularyCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {"target_language": ["exact"]}

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
    pagination_class = pagination.VocabularyWordsPagination
    filterset_fields = {
        "category__target_language": ["exact"],
    }
    search_fields = ["source_word", "target_word"]

    def get_queryset(self):
        return VocabularyWord.objects.filter(
            category__user=self.request.user)


    def perform_create(self, serializer):
        category = serializer.validated_data.get("category")

        if category is None:
            language, _ = Language.objects.get_or_create(
                language_name="Without"
            )

            category, _ = VocabularyCategory.objects.get_or_create(
                user=self.request.user,
                target_language=language,
                name="STANDARD",
            )

        serializer.save(category=category)
    
    def perform_update(self, serializer):
        category = serializer.validated_data.get("category")

        if category is None:
            language, _ = Language.objects.get_or_create(
                language_name="Without"
            )

            category, _ = VocabularyCategory.objects.get_or_create(
                user=self.request.user,
                target_language=language,
                name="STANDARD",
            )

        serializer.save(category=category)
