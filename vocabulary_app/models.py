from django.conf import settings
from django.db import models


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

    native_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="native_speakers",
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
                             on_delete=models.CASCADE,
                             related_name="vocabulary_categories",
                             )
    
    category_name = models.CharField(max_length=100, default="STANDARD")

    target_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="vocabulary_categories",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_language", "category_name"],
                name="unique_category_per_language",
            )
        ]

    def __str__(self):
        return f"{self.category_name}"

class VocabularyConcept(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocabulary_concepts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Concept {self.id}"

class VocabularyWord(models.Model):
    concept = models.ForeignKey(
        VocabularyConcept,
        on_delete=models.CASCADE,
        related_name="translations",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="translations",
    )

    category = models.ForeignKey(
        VocabularyCategory,
        on_delete=models.SET_NULL,
        related_name="words",
        null=True,
        blank=True,
    )

    word = models.CharField(max_length=255)
    tip = models.CharField(max_length=255, blank=True)
    sentence = models.TextField(blank=True)
    rank = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["concept", "language"],
                name="unique_translation_per_language",
            )
        ]

    def __str__(self):
        return f"{self.word} ({self.language})"