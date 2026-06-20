from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    QuizViewSet,
    QuizAttemptViewSet,
    QuizSubmitAPIView,
)

router = DefaultRouter()
router.register(r"quizzes", QuizViewSet, basename="quiz")
router.register(r"attempts", QuizAttemptViewSet, basename="attempt")

urlpatterns = [
    path("quiz-answer/<int:quiz_id>/submit/", QuizSubmitAPIView.as_view(),name="quiz-answer"),
    path("", include(router.urls)),
]