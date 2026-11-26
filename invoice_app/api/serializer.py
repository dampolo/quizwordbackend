from django.db import transaction
from rest_framework import serializers

from auth_app.models import User
from company_app.models import Company
from invoice_app.invoice_number import GenerateInvoiceNumber
from invoice_app.models import Invoice, InvoiceService, ServiceCatalog, Tax


class InvoiceServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceService
        fields = ['id', 'invoice', 'abo_choice', 'amount']
        read_only_fields = ['amount']

    def validate(self, attrs):
        if self.instance is not None and 'invoice' in attrs:
            if attrs['invoice'].pk != self.instance.invoice_id:
                raise serializers.ValidationError({
                    'invoice': 'Die Rechnung einer Position kann nicht gewechselt werden.'
                })
        if self.instance is None or 'abo_choice' in attrs:
            plan = attrs.get('abo_choice')
            try:
                catalog = ServiceCatalog.objects.get(abo_choice=plan)
            except ServiceCatalog.DoesNotExist:
                raise serializers.ValidationError({
                    'abo_choice': 'Für diesen Tarif wurde noch kein Preis hinterlegt.'
                })
            if self.instance is None or plan != self.instance.abo_choice:
                attrs['amount'] = catalog.amount
        return attrs


    @transaction.atomic
    def create(self, validated_data):
        service = super().create(validated_data)
        Invoice.objects.filter(pk=service.invoice_id).update(
            abo_choice=service.abo_choice,
            amount=service.amount,
        )
        return service


    @transaction.atomic
    def update(self, instance, validated_data):
        service = super().update(instance, validated_data)
        Invoice.objects.filter(pk=service.invoice_id).update(
            abo_choice=service.abo_choice,
            amount=service.amount,
        )
        return service


class NestedInvoiceServiceSerializer(InvoiceServiceSerializer):
    class Meta(InvoiceServiceSerializer.Meta):
        fields = ['id', 'abo_choice', 'amount']


class InvoiceSerializer(serializers.ModelSerializer):
    services = NestedInvoiceServiceSerializer(
        many=True,
        allow_empty=False,
        max_length=1,
    )
    customer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.ProfileType.CUSTOMER),
        write_only=True,
    )

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
            'value_tax',
            'value_tax_amount',

            # relations
            'customer', 'business',

            # system fields
            'created_at', 'updated_at', 'is_finalized',

            'notes_template',
            'notes',
            'payment_method',
            'abo_choice',

            # SERVICES LAST
            'services',
        ]

        # Read-only fields: CANNOT be set by frontend
        read_only_fields = [
            'id',
            'abo_choice',
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

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        current_user = request.user  # BUSINESS

        services_data = validated_data.pop('services')
        service_data = services_data[0]
        validated_data['abo_choice'] = service_data['abo_choice']
        validated_data['amount'] = service_data['amount']

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

        InvoiceService.objects.create(invoice=invoice, **service_data)

        return invoice


    @transaction.atomic
    def update(self, instance, validated_data):
        services_data = validated_data.pop('services', None)
        if services_data is not None:
            service_data = services_data[0]
            service = instance.services.first()
            if service is not None and service.abo_choice == service_data['abo_choice']:
                service_data['amount'] = service.amount
            validated_data['abo_choice'] = service_data['abo_choice']
            validated_data['amount'] = service_data['amount']
        instance = super().update(instance, validated_data)
        if services_data is not None:
            instance.services.update_or_create(
                defaults=service_data,
                invoice=instance,
            )
        return instance


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
        service = obj.services.first()
        if service:
            return service.get_abo_choice_display()
        return ""
