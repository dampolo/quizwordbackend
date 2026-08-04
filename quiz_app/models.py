from django.db import models
from vocabulary_app.models import Language, VocabularyConcept
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Quiz(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )
    quiz_name = models.CharField(max_length=100)

    native_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="native_quizzes"
    )

    target_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="target_quizzes"
    )

    concepts = models.ManyToManyField(
        VocabularyConcept,
        related_name="quizzes"
    )


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class QuizAttempt(models.Model):
    class Direction(models.TextChoices): 
        FORWARD = "FORWARD", _("Source → Target") 
        REVERSE= "REVERSE", _("Target → Source")
    
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        default=Direction.FORWARD
    )
    
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

    concept = models.ForeignKey(
    VocabularyConcept,
    on_delete=models.CASCADE
)

    user_answer = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()