from django.urls import path, include
from .views import InvoiceServiceView, InvoiceView, ServiceCatalogView, TaxAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'invoices', InvoiceView, basename='invoices')
router.register(r'invoice-services', InvoiceServiceView, basename='invoice-services')
router.register(r'service-catalog', ServiceCatalogView, basename='service-catalog')

urlpatterns = [
    path('', include(router.urls)),
    path('tax/', TaxAPIView.as_view(), name="tax"),
]