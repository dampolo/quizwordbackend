from rest_framework import serializers

from purchase_app.models import Purchase


class CustomerPurchasesSerializer(serializers.ModelSerializer):
    invoice_number = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.get_abo_choice_display', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'invoice', 'invoice_number', 'customer', 'service', 'service_name',
            'payment_method', 'payment_method_id', 'discount', 'discount_amount', 'discount_percentage',
            'base_net_amount', 'net_amount', 'tax_percentage', 'tax_amount',
            'gross_price', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_invoice_number(self, obj):
        if obj.invoice is not None:
            return obj.invoice.invoice_number
        return None
