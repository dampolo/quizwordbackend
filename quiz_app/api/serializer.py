from rest_framework import serializers
from quiz_app.models import Quiz, QuizAttempt, QuizAnswer


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            "id",
            "user",
            "quiz_name",
            "words",
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