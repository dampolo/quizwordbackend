from django.contrib import admin

from .models import InvoiceService


@admin.register(InvoiceService)
class InvoiceServiceAdmin(admin.ModelAdmin):
    list_display = ("abo_choice", "price")
