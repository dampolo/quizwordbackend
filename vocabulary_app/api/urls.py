from . import views

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    VocabularyCategoryViewSet,
    VocabularyWordViewSet,
    LanguageViewSet,
    UserLanguageViewSet
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
router.register(r"languages", LanguageViewSet, basename="languages")

urlpatterns = [
    path("", include(router.urls)),
    path("user-languages/", UserLanguageViewSet.as_view(), name="user-languages"),
]