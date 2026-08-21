from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    QuizViewSet,
    QuizAttemptViewSet,
    QuizSubmitAPIView,
    LastQuizView
)

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'attempts', QuizAttemptViewSet, basename='attempt')

urlpatterns = [
    path('quiz-answers/<int:quiz_id>/submit/', QuizSubmitAPIView.as_view(), name='quiz-answer'),
    path('last-quiz/', LastQuizView.as_view(), name='last-quiz'),
    path('', include(router.urls)),
]