from rest_framework import serializers
from purchase_app.models import Purchase

# Customer can see all his orders/purchases
class CustomerPurchasesSerializer(serializers.ModelSerializer):
    invoice_number = serializers.SerializerMethodField()
    invoice_category = serializers.SerializerMethodField()
    course_id = serializers.CharField(source='course.id', read_only=True)

    class Meta:
        model = Purchase
        fields = ['id', 'course_id', 'invoice_number', 'customer', 'payment_method', 'invoice_category', 'discount', 'total', 'status', 'created_at' ]
        read_only_fields = ['id', 'course_id', 'invoice_number', 'customer', 'payment_method', 'invoice_category', 'discount', 'total', 'status', 'created_at' ]

    # Return invoice number "#00125" or None 
    def get_invoice_number(self, obj):
        if obj.invoice:
            return obj.invoice.invoice_number
        return None
    
    # Return Course, Service or None
    def get_invoice_category(self, obj):
        invoice = obj.invoice
        if invoice:
            return invoice.invoice_category
        return None
    