from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (LanguageViewSet, UserLanguageViewSet,
                    VocabularyCategoryViewSet, VocabularyConceptViewSet,
                    VocabularyWordViewSet, VocabularySearchView)

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
router.register(
    r"concepts",
    VocabularyConceptViewSet,
    basename="concepts",
)

urlpatterns = [
    path("", include(router.urls)),
    path("user-languages/", UserLanguageViewSet.as_view(), name="user-languages"),
    path("vocabulary-search/", VocabularySearchView.as_view(), name="vocabulary-search",),
]