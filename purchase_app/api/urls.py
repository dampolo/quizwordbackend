from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    path('my-purchases/', views.CustomerPurchasesAPI.as_view(), name='my-purchases'),
    path('check-purchase/<int:service_id>/', views.CheckPurchaseView.as_view(), name='check-purchase')
]