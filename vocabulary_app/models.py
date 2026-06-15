from django.db import models

from auth_app.models import User


class VocabularyCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="STANDARD")


class VocabularyWord(models.Model):
    category = models.ForeignKey(
        VocabularyCategory,
        on_delete=models.CASCADE,
        related_name="words"
    )

    source_word = models.CharField(max_length=255)
    target_word = models.CharField(max_length=255)

    source_tip = models.CharField(max_length=255, blank=True)
    target_tip = models.CharField(max_length=255, blank=True)

    source_sentence = models.TextField(blank=True)
    target_sentence = models.TextField(blank=True)

    source_rank = models.IntegerField(default=0)
    target_rank = models.IntegerField(default=0)