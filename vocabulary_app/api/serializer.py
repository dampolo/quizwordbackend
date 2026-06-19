from rest_framework import serializers
from vocabulary_app.models import VocabularyCategory, VocabularyWord


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
    class Meta:
        model = VocabularyCategory
        fields = (
            "id",
            "name",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
        )
