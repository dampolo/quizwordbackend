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
        write_only=True,
        required=False
    )

    category_name = serializers.StringRelatedField(
        source="category",
        read_only=False
    )

    language_id = serializers.IntegerField(
        source="category.target_language_id",
        read_only=True,
    )

    language_name = serializers.CharField(
        source="category.target_language.language_name",
        read_only=True,
    )

    class Meta:
        model = VocabularyWord
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["category"].queryset = VocabularyCategory.objects.filter(
                user=request.user
            )

    class Meta:
        model = VocabularyWord
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class VocabularyCategorySerializer(serializers.ModelSerializer):
    language_id = serializers.IntegerField(
    source="target_language_id",
    write_only=True,
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
