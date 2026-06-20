from rest_framework import serializers
from quiz_app.models import Quiz, QuizAttempt, QuizAnswer

from vocabulary_app.api.serializer import VocabularyWordSerializer
from vocabulary_app.models import VocabularyWord
from quiz_app.models import Quiz, VocabularyWord

class QuizSerializer(serializers.ModelSerializer):
    quiz_id = serializers.IntegerField(source="id", read_only=True)
    words = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyWord.objects.all(),
        many=True,
        write_only=True
    )

    answers = VocabularyWordSerializer(
        source="words",
        many=True,
        read_only=True
    )

    class Meta:
        model = Quiz
        fields = [
            "quiz_id",
            "quiz_name",
            "words",
            "answers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["words"].queryset = VocabularyWord.objects.filter(
                category__user=request.user
            )


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
    direction = serializers.CharField(
        source="get_direction_display",
        read_only=True
    )

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "direction",
            "user",
            "quiz",
            "started_at",
            "finished_at",
            "score",
            "answers",
        ]