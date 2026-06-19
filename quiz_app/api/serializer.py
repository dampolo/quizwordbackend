from rest_framework import serializers
from quiz_app.models import Quiz, QuizAttempt, QuizAnswer

from vocabulary_app.api.serializer import VocabularyWordSerializer
from vocabulary_app.models import VocabularyWord

class QuizSerializer(serializers.ModelSerializer):
    words = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyWord.objects.all(),
        many=True,
        write_only=True
    )

    words_detail = VocabularyWordSerializer(
        source="words",
        many=True,
        read_only=True
    )

    class Meta:
        model = Quiz
        fields = [
            "id",
            "quiz_name",
            "words",
            "words_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = [
            "id",
            "attempt",
            "word",
            "user_answer",
            "correct_answer",
            "is_correct",
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)
    score = serializers.ReadOnlyField()

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "user",
            "quiz",
            "started_at",
            "finished_at",
            "score",
            "answers",
        ]