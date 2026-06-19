from rest_framework import viewsets
from quiz_app.models import Quiz, QuizAttempt, QuizAnswer
from quiz_app.api.serializer import (
    QuizSerializer,
    QuizAttemptSerializer,
    QuizAnswerSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer


class QuizAnswerViewSet(viewsets.ModelViewSet):
    queryset = QuizAnswer.objects.all()
    serializer_class = QuizAnswerSerializer