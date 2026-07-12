from . import views

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    VocabularyCategoryViewSet,
    VocabularyWordViewSet,
    LanguageViewSet
)

router = DefaultRouter()
router.register(
    "categories",
    VocabularyCategoryViewSet,
    basename="vocabulary-category"
)
router.register(
    "words",
    VocabularyWordViewSet,
    basename="vocabulary-word"
)
router.register(r"languages", LanguageViewSet, basename="language")

urlpatterns = [
    path("", include(router.urls)),
]