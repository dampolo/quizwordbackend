from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    QuizViewSet,
    QuizAttemptViewSet,
    QuizAnswerViewSet,
)

router = DefaultRouter()
router.register(r"quizzes", QuizViewSet, basename="quiz")
router.register(r"attempts", QuizAttemptViewSet, basename="attempt")
router.register(r"answers", QuizAnswerViewSet, basename="answer")

urlpatterns = [
    path("", include(router.urls)),
]