from rest_framework import viewsets
from rest_framework.views import APIView, View
from quiz_app.models import Quiz, QuizAttempt, QuizAnswer
from quiz_app.api.serializer import (
    QuizSerializer,
    QuizAttemptSerializer,
    QuizAnswerSerializer,
)

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from vocabulary_app.models import VocabularyWord


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer


class QuizSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id):
        quiz = Quiz.objects.get(
            id=quiz_id,
            user=request.user
        )

        direction=request.data.get("direction")

        answers = request.data.get("answers", [])

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz
        )

        results = []

        for answer in answers:
            word_id = answer.get("id")
            user_answer = answer.get("answer", "")

            word = VocabularyWord.objects.get(
                id=word_id,
                category__user=request.user
            )

            if direction == QuizAttempt.Direction.FORWARD:
                correct_answer = word.target_word
            else:
                correct_answer = word.source_word

            is_correct = correct_answer == user_answer

            QuizAnswer.objects.create(
                attempt=attempt,
                word=word,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct
            )

            UpdateRank.update_rank(word, is_correct, direction);

            results.append({
                "word_id": word.id,
                "source_word": word.source_word,
                "user_answer": correct_answer,
                "correct_answer": word.target_word,
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
                word.target_rank += 1
            else:
                word.target_rank -= 1
            word.save(update_fields=["target_rank"])
        else:
            if is_correct:
                word.source_rank += 1
            else:
                word.source_rank -= 1
            word.save(update_fields=["source_rank"])