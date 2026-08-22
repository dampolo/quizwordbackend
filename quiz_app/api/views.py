from rest_framework import viewsets, filters
from rest_framework.views import APIView, View
from quiz_app.models import Quiz, QuizAttempt, QuizAnswer
from django_filters.rest_framework import DjangoFilterBackend
from quiz_app.api.serializer import (
    QuizSerializer,
    QuizAttemptDetailSerializer,
    QuizAttemptListSerializer,
    GetQuizSerializer,
    UpdateQuizSerializer
)


from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from vocabulary_app.models import VocabularyWord, VocabularyConcept

# Use can see all his quizes
class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {"target_language": ["exact"]}

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return GetQuizSerializer

        if self.action in ["update", "partial_update"]:
            return UpdateQuizSerializer
        
        return QuizSerializer


class QuizAttemptViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = QuizAttempt.objects.filter(user=self.request.user)

        quiz_id = self.request.query_params.get("quiz_id")
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return QuizAttemptListSerializer

        return QuizAttemptDetailSerializer


class QuizSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        quiz = Quiz.objects.get(
            id=quiz_id,
            user=request.user
        )

        direction = request.data.get("direction")

        target_language = quiz.target_language
        native_language = quiz.native_language

        answers = request.data.get("answers", [])

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz
        )

        results = []

        for answer in answers:
            concept_id = answer.get("id")
            user_answer = answer.get("answer", "")

            concept = VocabularyConcept.objects.get(
                id=concept_id,
                user=request.user
            )

            source_word = concept.translations.get(
                language=native_language
            )

            target_word = concept.translations.get(
                language=target_language
            )

            if direction == QuizAttempt.Direction.FORWARD:
                correct_answer = target_word.word
                rank_word = target_word
            else:
                correct_answer = source_word.word
                rank_word = source_word

            is_correct = correct_answer == user_answer

            QuizAnswer.objects.create(
                attempt=attempt,
                concept=concept,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct
            )

            UpdateRank.update_rank(rank_word, is_correct, direction)

            results.append({
                "word_id": concept.id,
                "source_word": source_word.word,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
            })

        attempt.finished_at = timezone.now()
        attempt.direction = direction
        attempt.save()

        return Response({
            "attempt_id": attempt.id,
            "quiz_id": quiz.id,
            "score": attempt.score,
            "results": results
        })


class UpdateRank:
    @staticmethod
    def update_rank(word, is_correct, direction):
        if direction == QuizAttempt.Direction.FORWARD:
            if is_correct:
                word.rank += 1
            else:
                word.rank -= 1
            word.save(update_fields=["rank"])
        else:
            if is_correct:
                word.source_rank += 1
            else:
                word.source_rank -= 1
            word.save(update_fields=["rank"])


class LastQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        last_quiz = QuizAttempt.objects.filter(
            user=user).order_by("-started_at").first()

        if last_quiz is None:
            return Response(
                {'detail': 'Du hast bis jetzt keine Quize erstellt'},
                status=status.HTTP_404_NOT_FOUND
                )

        quiz = last_quiz.quiz

        serializer = GetQuizSerializer(
            quiz,
            context={'request': request}
        )
        return Response(serializer.data)