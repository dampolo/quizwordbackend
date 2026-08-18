from rest_framework import serializers
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language, UserLanguages, VocabularyConcept
from django.db import transaction
from auth_app.user_language_status import UserLanguageStatus


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
    learning_languages_id = serializers.PrimaryKeyRelatedField(
        source="learning_languages",
        queryset=Language.objects.all(),
        many=True,
        write_only=True,
    )
    languages_active = serializers.SerializerMethodField()

    class Meta:
        model = UserLanguages
        fields = ["id",
                  "native_language",
                  "native_language_id",
                  "learning_languages",
                  "learning_languages_id",
                  "languages_active"
                  ]
        read_only_fields = ["id"]

    def get_languages_active(self, obj):
        return UserLanguageStatus.languages_active(obj.user)

    def create(self, validated_data):
        learning_languages = validated_data.pop("learning_languages", [])
        instance = UserLanguages.objects.create(**validated_data)
        instance.learning_languages.set(learning_languages)
        return instance

    def update(self, instance, validated_data):
        learning_languages = validated_data.pop("learning_languages", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if learning_languages is not None:
            instance.learning_languages.set(learning_languages)

        return instance

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
    category = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyCategory.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    allow_new_meaning = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
    )
    translations = TranslationSerializer(many=True)

    def validate(self, attrs):
        user = self.context["request"].user

        if not UserLanguageStatus.languages_active(user):
            raise serializers.ValidationError({
                "languages": (
                    "Please choose your native language and at least "
                    "one learning language before creating a word."
                ),
                "code": "LANGUAGES_NOT_CONFIGURED",
            })

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        translations = validated_data["translations"]
        category = validated_data.get("category")

        allow_new_meaning = validated_data.pop(
            "allow_new_meaning",
            False,
        )

        user_languages = user.user_languages
        native_language = user_languages.native_language

        self.info_messages = []
        self.requires_confirmation = False
        self.confirmation_data = None

        # Find native translation from payload
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

        # Find concepts which already contain this native word
        existing_native_translations = (
            VocabularyWord.objects
            .filter(
                concept__user=user,
                language=native_language,
                word__iexact=native_word,
            )
            .select_related("concept")
        )

        # -------------------------------------------------
        # Native word doesn't exist -> completely new concept
        # -------------------------------------------------

        if not existing_native_translations.exists():
            concept = VocabularyConcept.objects.create(user=user)

        else:
            # For now take the existing concept.
            existing_concepts = [translation.concept for translation in existing_native_translations]

            # Find target translations from payload
            other_items = [
                item
                for item in translations
                if item["language"] != native_language
            ]

            exact_concept = None

            for existing_concept in existing_concepts:
                exact_match = True

                for item in other_items:
                    language = item["language"]
                    word = item["word"].strip()

                    existing_translation = (
                        existing_concept.translations
                        .filter(language=language)
                        .first()
                    )

                    if (
                        existing_translation is None
                        or existing_translation.word.casefold()
                        != word.casefold()
                    ):
                        exact_match = False
                        break

                if exact_match:
                    exact_concept = existing_concept
                    break
            # ---------------------------------------------
            # Exact translation already exists
            # ---------------------------------------------

            if exact_concept:
                concept = existing_concept

                self.info_messages.append(
                    f"'{native_word}' with this translation "
                    f"already exists."
                )

                return concept

            # ---------------------------------------------
            # Different meaning -> confirmation required
            # ---------------------------------------------

            if not allow_new_meaning:
                self.requires_confirmation = True

                existing_words = [
                    {
                        "language": translation.language.language_name,
                        "word": translation.word,
                    }
                    for translation in existing_concept.translations.all()
                    if translation.language != native_language
                ]

                self.confirmation_data = {
                    "native_word": native_word,
                    "existing_translations": existing_words,
                    "new_translations": [
                        {
                            "language": item["language"].language_name,
                            "word": item["word"].strip(),
                        }
                        for item in other_items
                    ],
                }

                return existing_concept

            # ---------------------------------------------
            # User confirmed -> NEW concept
            # ---------------------------------------------

            concept = VocabularyConcept.objects.create(user=user)

        # -------------------------------------------------
        # Create translations
        # -------------------------------------------------

        for item in translations:
            language = item["language"]
            word = item["word"].strip()

            current_category = category

            if current_category is None:
                current_category, _ = (
                    VocabularyCategory.objects.get_or_create(
                        user=user,
                        target_language=language,
                        category_name="STANDARD",
                    )
                )

            VocabularyWord.objects.create(
                concept=concept,
                language=language,
                category=current_category,
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
    language = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(),
        required=False,
    )
    word = serializers.CharField()
    tip = serializers.CharField(required=False, allow_blank=True)
    sentence = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=VocabularyCategory.objects.all(),
        required=False,
        allow_null=True,
    )


class VocabularyConceptUpdateSerializer(serializers.Serializer):
    translations = TranslationUpdateSerializer(many=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context["request"]

        for data in validated_data["translations"]:
            translation = instance.translations.get(id=data["id"])

            language = data.get("language", translation.language)

            category = data.get("category")

            if category is None:
                category, _ = VocabularyCategory.objects.get_or_create(
                    user=request.user,
                    target_language=language,
                    category_name="STANDARD",
                )
            if category and category.user != request.user:
                raise serializers.ValidationError({
                    "category_id": "This category does not belong to you."
                })

            if category and category.target_language != language:
                raise serializers.ValidationError({
                    "category_id": (
                        "The category language must match "
                        "the translation language."
                    )
                })

            # The concept cannot contain the same language twice.
            if (
                instance.translations
                .exclude(id=translation.id)
                .filter(language=language)
                .exists()
            ):
                raise serializers.ValidationError({
                    "language": (
                        "This concept already has a translation "
                        "in this language."
                    )
                })

            translation.language = language
            translation.category = category
            translation.word = data.get(
                "word",
                translation.word
            )
            translation.tip = data.get(
                "tip",
                translation.tip
            )
            translation.sentence = data.get(
                "sentence",
                translation.sentence
            )

            translation.save()

        return instance
