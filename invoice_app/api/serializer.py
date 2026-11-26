from django.db import transaction
from rest_framework import serializers

from auth_app.models import User
from company_app.models import Company
from invoice_app.invoice_number import GenerateInvoiceNumber
from invoice_app.models import Invoice, ServiceCatalog, Tax


class InvoiceSerializer(serializers.ModelSerializer):
    abo_choice = serializers.ChoiceField(choices=Invoice._meta.get_field('abo_choice').choices)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.ProfileType.CUSTOMER),
        write_only=True,
    )

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_type', 'invoice_number', 'invoice_status',
            'related_invoice',

            # customer snapshot
            'user_customer_id',
            'user_customer_first_name', 'user_customer_last_name', 'user_customer_street',
            'user_customer_street_number', 'user_customer_postcode', 'user_customer_city',


            # company snapshot
            'company_name', 'company_street', 'company_street_number', 'company_postcode',
            'company_city', 'company_tax_number', 'company_email', 'company_bank',
            'company_bank_account', 'company_swift_code', 'company_logo',

            # invoice totals
            'discount',
            'discount_amount_value',

            'amount',
            'value_tax',
            'value_tax_amount',

            # relations
            'customer', 'business',

            # system fields
            'created_at', 'updated_at', 'is_finalized',

            'payment_method',
            'abo_choice',

        ]

        # Read-only fields: CANNOT be set by frontend
        read_only_fields = [
            'id',
            'amount',
            'business',
            'invoice_status',
            'invoice_number',
            'created_at',
            'updated_at',
            'is_finalized',

            # Customer snapshot
            'user_customer_id',
            'user_customer_first_name', 'user_customer_last_name', 'user_customer_street',
            'user_customer_street_number', 'user_customer_postcode', 'user_customer_city',


            # Company snapshot
            'company_name',
            'company_street',
            'company_street_number',
            'company_postcode',
            'company_city',
            'company_tax_number',
            'company_email',
            'company_bank',
            'company_bank_account',
            'company_swift_code',
            'company_logo',

            # invoice totals
            'discount',
            'discount_amount_value',

        ]

    def validate(self, attrs):
        try:
            catalog = ServiceCatalog.objects.get(abo_choice=attrs['abo_choice'])
        except ServiceCatalog.DoesNotExist:
            raise serializers.ValidationError({
                'abo_choice': 'Bitte zuerst einen Preis fuer diesen Tarif hinterlegen.'
            })
        attrs['amount'] = catalog.amount
        return attrs


    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        current_user = request.user  # BUSINESS

        customer = validated_data.pop('customer')

        if current_user.role != User.ProfileType.BUSINESS:
            raise serializers.ValidationError(
                "Only business users can create invoices.")

        company = Company.objects.first()

        if company is None:
            raise serializers.ValidationError('Bitte zuerst die Firmendaten hinterlegen.')

        invoice = Invoice.objects.create(
            **validated_data,
            business=current_user,
            customer=customer,
            invoice_number=GenerateInvoiceNumber.generate_invoice_number(),

            # CUSTOMER SNAPSHOT
            user_customer_id=customer.id,
            user_customer_number=customer.customer_number,
            user_customer_first_name=customer.first_name,
            user_customer_last_name=customer.last_name,
            user_customer_street=customer.street,
            user_customer_street_number=customer.street_number,
            user_customer_postcode=customer.postcode,
            user_customer_city=customer.city,

            # COMPANY SNAPSHOT
            company_name=company.name,
            company_street=company.street,
            company_street_number=company.street_number,
            company_postcode=company.postcode,
            company_city=company.city,
            company_tax_number=company.tax_number,
            company_email=company.email,
            company_bank=company.bank,
            company_bank_account=company.bank_account,
            company_swift_code=company.swift_code,
            company_logo=company.logo,
        )

        return invoice


class ServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = ['id', 'abo_choice', 'amount']


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = ['id', 'name', 'percent', 'active']
        read_only_fields = ['id']

# Customer can see all his invoices.
class CustomerInvoiceSerializer(serializers.ModelSerializer):
    service_name = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'service_name', 'invoice_status', 'abo_choice','created_at']
        read_only_fields = ['id', 'invoice_number', 'service_name','invoice_status', 'abo_choice', 'created_at']

    def get_service_name(self, obj):
        return obj.get_abo_choice_display()
