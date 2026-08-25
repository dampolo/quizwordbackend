from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


urlpatterns = [
    path('profile-customer/', views.CustomerProfileView.as_view()),
    path(
        "change-username/",
        views.ChangeUsernameView.as_view(),
        name="change-username",
    )
]
