from django.contrib import admin

from .models import InvoiceService, ServiceCatalog


@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    list_display = ("abo_choice", "amount")


@admin.register(InvoiceService)
class InvoiceServiceAdmin(admin.ModelAdmin):
    list_display = ("invoice", "abo_choice", "amount")
