from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language, UserLanguages, VocabularyConcept
from rest_framework.exceptions import PermissionDenied
from vocabulary_app import pagination
from rest_framework import generics
from rest_framework.validators import ValidationError

from vocabulary_app.api.serializer import (
    VocabularyCategorySerializer,
    VocabularyWordSerializer,
    LanguageSerializer,
    UserLanguageSerializer,
    VocabularyConceptSerializer,
    VocabularyEntryCreateSerializer,
    VocabularyConceptUpdateSerializer
)
from django.db.models import Count, Q


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

# CRUD word
class VocabularyWordViewSet(viewsets.ModelViewSet):
    serializer_class = VocabularyWordSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    pagination_class = pagination.VocabularyWordsPagination

    search_fields = ["word"]
    filterset_fields = {
        "language": ["exact"],
        "category": ["exact"],
        "category__target_language": ["exact"],
    }

    def get_queryset(self):
        return VocabularyWord.objects.filter(
            concept__user=self.request.user
        )
    

class VocabularyConceptViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = pagination.VocabularyWordsPagination

    def get_queryset(self):
        user = self.request.user
        queryset = VocabularyConcept.objects.filter(user=user)

        if self.action != "list":
            return queryset

        native_language = user.user_languages.native_language
        language = self.request.query_params.get("language")

        if language is None:
            learning = user.user_languages.learning_languages.first()

            if learning is None:
                return queryset.none()

            language = learning.id

        return (
            queryset.annotate(
                translation_count=Count(
                    "translations",
                    filter=Q(
                        translations__language_id__in=[
                            native_language.id,
                            int(language),
                        ]
                    ),
                    distinct=True,
                )
            )
            .filter(translation_count=2)
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        language = self.request.query_params.get("language")

        if language is None:
            learning = self.request.user.user_languages.learning_languages.first()
            language = learning.id if learning else None
        else:
            language = int(language)

        context["language"] = language
        return context

    def get_serializer_class(self):
        if self.action == "create":
            return VocabularyEntryCreateSerializer
        if self.action in ["update", "partial_update"]:
            return VocabularyConceptUpdateSerializer

        return VocabularyConceptSerializer