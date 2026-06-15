from rest_framework import serializers
from models import VocabularyCategory, VocabularyWord


class VocabularyWordSerializer(serializers.ModelSerializer):
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