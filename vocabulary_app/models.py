from django.db import models
from django.conf import settings


class Language(models.Model):
    language_name = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        ordering = ["language_name"]

    def __str__(self):
        return f"{self.language_name}"
    
class UserLanguages(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_languages",
    )

    learning_languages = models.ManyToManyField(
        Language,
        related_name="learners",
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username}"


class VocabularyCategory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100, default="STANDARD")

    target_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="vocabulary_categories",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_language", "name"],
                name="unique_category_per_language",
            )
        ]
    ordering = ["name"]

    def __str__(self):
        return f"{self.name}"


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
