from django.urls import include, path
from . import views

urlpatterns = [
    path('profile-customer/', views.CustomerProfileView.as_view()),
    path(
        "change-username/",
        views.ChangeUsernameView.as_view(),
        name="change-username",
    ),
    path(
        "delete-account/",
        views.DeleteAccountView.as_view(),
        name="delete-account",
    )
]
