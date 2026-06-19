from django.db import models
from django.conf import settings


class VocabularyCategory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="STANDARD")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.source_word} → {self.target_word}"