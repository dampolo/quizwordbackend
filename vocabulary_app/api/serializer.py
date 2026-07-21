from rest_framework import serializers
from vocabulary_app.models import VocabularyCategory, VocabularyWord, Language


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "language_name"]
        read_only_fields = ["id"]


class VocabularyWordSerializer(serializers.ModelSerializer):

    category = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyCategory.objects.all(),
        required=False,
        allow_null=True,
    )

    category_name = serializers.CharField(
        source="category.name",
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
