from rest_framework import serializers

from quiz_app.models import Quiz, QuizAnswer, QuizAttempt
from vocabulary_app.api.serializer import VocabularyConceptSerializer
from vocabulary_app.models import Language, VocabularyConcept


# User can see all his quizzes:
class GetQuizSerializer(serializers.ModelSerializer):
    quiz_id = serializers.IntegerField(source="id", read_only=True)
    concepts = serializers.SerializerMethodField()
    concepts_count = serializers.SerializerMethodField()
    language_name = serializers.CharField(source="target_language.language_name", read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "quiz_id",
            "quiz_name",
            "target_language",
            "concepts",
            "concepts_count",
            "language_name",
            "created_at",
            "updated_at",
        )

    def get_concepts(self, obj):
        serializer = VocabularyConceptSerializer(
            obj.concepts.all(),
            many=True,
            context={
                "request": self.context["request"],
                "language": obj.target_language.id,
            },
        )
        return serializer.data

    def get_concepts_count(self, obj):
        return obj.concepts.count()

# POST for create quiz:
class QuizSerializer(serializers.ModelSerializer):
    target_language = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all()
    )
    quiz_id = serializers.IntegerField(source="id", read_only=True)
    concepts = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyConcept.objects.all(),
        many=True,
        required=False,
    )

    concepts_count = serializers.SerializerMethodField()

    answers = VocabularyConceptSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Quiz
        fields = [
            "quiz_id",
            "quiz_name",
            "concepts",
            "concepts_count",
            "target_language",
            "answers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_concepts_count(self, obj):
        return obj.concepts.count()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["concepts"].queryset = VocabularyConcept.objects.filter(
                user=request.user
            )

    def validate(self, attrs):
        user = self.context["request"].user
        target_language = attrs["target_language"]
        quiz_name = attrs["quiz_name"]

        exist = Quiz.objects.filter(
            user=user,
            target_language=target_language,
            quiz_name__iexact=quiz_name,
            ).exists()

        if exist:
            raise serializers.ValidationError({
                "detail": "Das Quiz existiert bereits."
            })

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user

        concepts = validated_data.pop("concepts")
        target_language = validated_data.pop("target_language")

        native_language = user.user_languages.native_language

        quiz = Quiz.objects.create(
            user=user,
            native_language=native_language,
            target_language=target_language,
            **validated_data,
        )

        quiz.concepts.set(concepts)
        return quiz

class UpdateQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ["quiz_name"]


class QuizAnswerSerializer(serializers.ModelSerializer):
    soure_word = serializers.CharField(source="word.source_word", read_only=True)
    class Meta:
        model = QuizAnswer
        fields = [
            "id",
            "attempt",
            "concept",
            "soure_word",
            "user_answer",
            "correct_answer",
            "is_correct",
        ]

# User can see list of his all quizzes which he did
class QuizAttemptListSerializer(serializers.ModelSerializer):
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
        ]

# User can see details from every quiz
class QuizAttemptDetailSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = "__all__"
