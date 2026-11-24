from django.urls import path

from .views import TranslateView, VerbConjugationView

urlpatterns = [
    path("translate/", TranslateView.as_view(), name="translate"),
     path(
        "conjugation/<str:language>/<str:verb>/",
        VerbConjugationView.as_view(),
        name="verb-conjugation",
    ),
]