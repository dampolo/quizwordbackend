from django.contrib import admin

from .models import ServiceCatalog


@admin.register(ServiceCatalog)
class ServiceCatalogAdmin(admin.ModelAdmin):
    list_display = ("abo_choice", "amount")
