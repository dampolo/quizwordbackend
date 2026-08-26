from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

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

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)