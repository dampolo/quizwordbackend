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
    VocabularyConceptSerializer
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
    "concept__categories__target_language": ["exact"],
    }
    search_fields = ["source_word", "target_word"]

    def get_queryset(self):
        return VocabularyWord.objects.filter(
            concept__user=self.request.user)


    def perform_create(self, serializer):
        source_word = serializer.validated_data["source_word"]
        category = serializer.validated_data.pop("category", None)
        language_id = serializer.validated_data["target_language"]
        user_languages = self.request.user.user_languages

        if language_id not in user_languages.learning_languages.all():
            raise ValidationError("You are not learning this language.")

        # 1. Find an existing concept with the same source word
        translation = VocabularyWord.objects.filter(
            concept__user=self.request.user,
            source_word__iexact=source_word,
            ).first()

        if translation:
            concept = translation.concept

            # 2. Check whether this concept already has this language
            if concept.translations.filter(
                target_language=language_id
            ).exists():
                raise ValidationError(
                    "This translation already exists."
                )
        else:
            # 3. Create a new concept
            concept = VocabularyConcept.objects.create(
            user=self.request.user
            )
        
        if category is None:
            category, _ = VocabularyCategory.objects.get_or_create(
                user=self.request.user,
                target_language=language_id,
                category_name="STANDARD",
            )
        concept.categories.add(category)

        serializer.save(concept=concept)


    
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



class VocabularyConceptViewSet(viewsets.ModelViewSet):
    serializer_class = VocabularyConceptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VocabularyConcept.objects.filter(
            user=self.request.user
        ).prefetch_related("categories")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)