from rest_framework import serializers
from invoice_app.models import Invoice, InvoiceService, ServiceCatalog, Tax
from company_app.models import Company
from auth_app.models import User
from invoice_app.invoice_number import GenerateInvoiceNumber


class InvoiceServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceService
        fields = ['id', 'service_name', 'provision_type',
                  'provision_fixed', 'provision_percent', 'provision_amount']


class InvoiceSerializer(serializers.ModelSerializer):
    services = InvoiceServiceSerializer(many=True,)
    customer = serializers.IntegerField(write_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_type', 'invoice_number', 'invoice_status',

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
            'provision', 
            'value_tax',
            'investitions_amount', 

            # relations
            'customer', 'business',

            # system fields
            'created_at', 'updated_at', 'is_finalized',

            'notes_template',
            'notes',
            'payment_method',
            'invoice_category',

            # SERVICES LAST
            'services',
        ]

        # Read-only fields: CANNOT be set by frontend
        read_only_fields = [
            'id',
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

            # Services
            'services',
        ]

    def create(self, validated_data):
        request = self.context['request']
        current_user = request.user  # BUSINESS

        services_data = validated_data.pop('services', [])

        customer_id = validated_data.pop('customer')
        customer = User.objects.get(id=customer_id)

        if current_user.role != User.ProfileType.BUSINESS:
            raise serializers.ValidationError(
                "Only business users can create invoices.")

        company = Company.objects.first()

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

        for service_data in services_data:
            InvoiceService.objects.create(
                invoice=invoice,
                **service_data
            )

        return invoice


class ServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = ['id', 'service_name', 'provision_type',
                  'provision_fixed', 'provision_percent']


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
        fields = ['id', 'invoice_number', 'service_name', 'invoice_status', 'invoice_category','created_at']    
        read_only_fields = ['id', 'invoice_number', 'service_name','invoice_status', 'invoice_category', 'created_at']

    def get_service_name(self, obj):
        service = obj.services.first()
        if service:
            return service.service_name
        return ""