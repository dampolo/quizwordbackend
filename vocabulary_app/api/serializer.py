from rest_framework import serializers
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language, UserLanguages, VocabularyConcept


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


class VocabularyWordSerializer(serializers.ModelSerializer):
    concept = serializers.PrimaryKeyRelatedField(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    category_name = serializers.CharField(
        source="category.category_name",
        read_only=True,
    )

    language_name = serializers.CharField(
        source="target_language.language_name",
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
            "category_id",
            "category_name",
            "target_language",
            "language_name",
            "source_word",
            "target_word",
            "source_tip",
            "target_tip",
            "source_sentence",
            "target_sentence",
            "source_rank",
            "target_rank",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "concept",
            "category_name",
            "language_name",
        )


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


class VocabularyConceptSerializer(serializers.ModelSerializer):

    translations = VocabularyWordSimpleSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = VocabularyConcept
        fields = [
            "id",
            "translations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
