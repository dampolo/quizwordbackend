from django.db import models
from vocabulary_app.models import VocabularyWord
from django.conf import settings


# Create your models here.
class Quiz(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )
    quiz_name = models.CharField(max_length=100)

    words = models.ManyToManyField(
        VocabularyWord,
        related_name="quizzes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    @property
    def score(self):
        answers = self.answers.all()
        correct = answers.filter(is_correct=True).count()
        total = answers.count()
        return f"{correct}/{total}"
    
class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    word = models.ForeignKey(
        VocabularyWord,
        on_delete=models.CASCADE
    )

    user_answer = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()