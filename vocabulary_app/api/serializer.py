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

    category = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    category_name = serializers.CharField(
        source="concept.categories.category_name",
        read_only=True,
    )


    language_id = serializers.IntegerField(
        source="category.target_language.id",
        read_only=True,
        )

    language_name = serializers.CharField(
    source="category.target_language.language_name",
       read_only=True,
       )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["category"].queryset = VocabularyCategory.objects.filter(
                user=request.user
            )

    class Meta:
        model = VocabularyWord
        fields = (
            "id",
            "category",
            "category_name",
            "language_id",
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
            "category_name",
            "language_id",
            "language_name",
        )


class VocabularyCategorySerializer(serializers.ModelSerializer):
    language_id = serializers.IntegerField(
        source="target_language_id",
    )

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
            "name",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
        )


class VocabularyConceptSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=VocabularyCategory.objects.all(),
        required=False,
    )

    class Meta:
        model = VocabularyConcept
        fields = [
            "id",
            "categories",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["categories"].queryset = VocabularyCategory.objects.filter(
                user=request.user
            )