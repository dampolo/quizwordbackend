from rest_framework import serializers
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language, UserLanguages, VocabularyConcept
from django.db import transaction

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "language_name"]
        read_only_fields = ["id"]


class UserLanguageSerializer(serializers.ModelSerializer):
    native_language = LanguageSerializer(read_only=True)
    native_language_id = serializers.PrimaryKeyRelatedField(
        source="native_language",
        queryset=Language.objects.all(),
        write_only=True,
    )

    learning_languages = LanguageSerializer(many=True, read_only=True)
    learning_language_ids = serializers.PrimaryKeyRelatedField(
        source="learning_languages",
        queryset=Language.objects.all(),
        many=True,
        write_only=True,
    )

    class Meta:
        model = UserLanguages
        fields = ["id",
                  "native_language",
                  "native_language_id",
                  "learning_languages",
                  "learning_language_ids"]
        read_only_fields = ["id"]

# GET/PATCH/DELETE
class VocabularyWordSerializer(serializers.ModelSerializer):
    concept = serializers.PrimaryKeyRelatedField(read_only=True)

    language = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(),
    )

    language_name = serializers.CharField(
        source="language.language_name",
        read_only=True,
    )

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    category_name = serializers.CharField(
        source="category.category_name",
        read_only=True,
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["category_id"].queryset = VocabularyCategory.objects.filter(
                user=request.user
            )

    class Meta:
        model = VocabularyWord
        fields = (
            "id",
            "concept",
            "language",
            "language_name",
            "category_id",
            "category_name",
            "word",
            "tip",
            "sentence",
            "rank",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "concept",
            "language_name",
            "category_name",
            "created_at",
            "updated_at",
        )


class TranslationSerializer(serializers.Serializer):
    language = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all()
    )
    word = serializers.CharField()
    tip = serializers.CharField(required=False, allow_blank=True)
    sentence = serializers.CharField(required=False, allow_blank=True)


# POST
class VocabularyEntryCreateSerializer(serializers.Serializer):
    translations = TranslationSerializer(many=True)

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        translations = validated_data["translations"]

        user_languages = user.user_languages
        native_language = user_languages.native_language

        native_item = next(
            (
                item
                for item in translations
                if item["language"] == native_language
            ),
            None,
        )

        if native_item is None:
            raise serializers.ValidationError({
                "translations": (
                    "A translation in your native language is required."
                )
            })

        native_word = native_item["word"].strip()

        # Search for "Hund" in the user's native language.
        existing_native_translation = (
            VocabularyWord.objects
            .filter(
                concept__user=user,
                language=native_language,
                word__iexact=native_word,
            )
            .select_related("concept")
            .first()
        )

        if existing_native_translation:
            concept = existing_native_translation.concept
        else:
            concept = VocabularyConcept.objects.create(user=user)

        for item in translations:
            language = item["language"]
            word = item["word"].strip()

            # Check whether this concept already has this language.
            existing_translation = concept.translations.filter(
                language=language
            ).first()

            if existing_translation:
                # The same translation already exists.
                if existing_translation.word.casefold() == word.casefold():
                    continue

                raise serializers.ValidationError({
                    "translations": (
                        f"This concept already has a translation "
                        f"for {language.language_name}: "
                        f"'{existing_translation.word}'."
                    )
                })

            category, _ = VocabularyCategory.objects.get_or_create(
                user=user,
                target_language=language,
                category_name="STANDARD",
            )

            VocabularyWord.objects.create(
                concept=concept,
                language=language,
                category=category,
                word=word,
                tip=item.get("tip", ""),
                sentence=item.get("sentence", ""),
            )

        return concept

class VocabularyCategorySerializer(serializers.ModelSerializer):
    language_id = serializers.PrimaryKeyRelatedField(
        source="target_language",
         queryset=Language.objects.all(),
    )

    words_count = serializers.SerializerMethodField()

    language_name = serializers.CharField(
        source="target_language.language_name",
        read_only=True,
    )

    class Meta:
        model = VocabularyCategory
        fields = (
            "id",
            "language_id",
            "language_name",
            "category_name",
            "words_count",
            "created_at",
        )
        read_only_fields = (
            "id",
            "words_count",
            "created_at",
        )

    def get_words_count(self, obj):
        return VocabularyWord.objects.filter(
            category=obj
        ).count()


class VocabularyWordSimpleSerializer(serializers.ModelSerializer):
    language_name = serializers.CharField(
        source="target_language.language_name",
        read_only=True,
    )

    class Meta:
        model = VocabularyWord
        fields = [
            "id",
            "language_name",
            "source_word",
            "target_word",
        ]

# GET
class VocabularyConceptSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()

    class Meta:
        model = VocabularyConcept
        fields = (
            "id",
            "translations",
            "created_at",
            "updated_at",
        )

    def get_translations(self, obj):
        user_languages = self.context["request"].user.user_languages
        language = self.context["language"]

        if language is None:
            return []

        translations = obj.translations.filter(
            language_id__in=[
                user_languages.native_language.id,
                language,
            ]
        )

        return VocabularyWordSerializer(translations, many=True).data

class TranslationUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    word = serializers.CharField()
    tip = serializers.CharField(required=False, allow_blank=True)
    sentence = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False)


class VocabularyConceptUpdateSerializer(serializers.Serializer):
    translations = TranslationUpdateSerializer(many=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        for data in validated_data["translations"]:
            word = instance.translations.get(id=data["id"])

            word.word = data["word"]
            word.tip = data.get("tip", "")
            word.sentence = data.get("sentence", "")

            if "category_id" in data:
                word.category_id = data["category_id"]

            word.save()

        return instance