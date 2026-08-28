from django.urls import include, path

from . import views

urlpatterns = [
    path("support/", SupportView.as_view(), name="apply"),
]