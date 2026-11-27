from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from auth_app.models import User
from company_app.models import Company
from invoice_app.invoice_number import GenerateInvoiceNumber
from invoice_app.models import Invoice, PaymentMethod, PaymentStatus, ServiceCatalog, Tax
from purchase_app.models import Purchase


class PurchaseService:
    @transaction.atomic
    def create_purchase(self, request, customer, service, discount=None):
        service = ServiceCatalog.objects.get(pk=service.pk)
        tax = Tax.objects.first()
        company = Company.objects.first()

        business = User.objects.filter(role=User.ProfileType.BUSINESS).first()
        if customer.role != User.ProfileType.CUSTOMER:
            raise ValidationError('Der Empfaenger muss ein Kunde sein.')

        gross_price = service.amount
        tax_percent = tax.percent if tax.active else Decimal('0.00')
        discount_percent = Decimal('0.00')
        
        if discount is not None:
            if not discount.active:
                raise ValidationError('Der Rabattcode ist nicht aktiv.')
            if discount.expires_at is not None and discount.expires_at <= timezone.now():
                raise ValidationError('Der Rabattcode ist abgelaufen.')
            discount_percent = Decimal(discount.percent_value)

        if not Decimal('0') <= discount_percent <= Decimal('100'):
            raise ValidationError(
                'Der Rabatt muss zwischen 0 und 100 Prozent liegen.')

        discount_amount = (gross_price * discount_percent / Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP,
        )

        total = (gross_price - discount_amount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP,
        )

        # Catalog prices include tax; extract its share from the discounted total.
        tax_amount = (total * tax_percent / (Decimal('100') + tax_percent)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP,
        )

        invoice = Invoice.objects.create(
            business=business,
            customer=customer,
            invoice_number=GenerateInvoiceNumber.generate_invoice_number(),
            invoice_status=PaymentStatus.UNPAID,
            payment_method=PaymentMethod.BANK_TRANSFER,
            abo_choice=service.abo_choice,
            discount=discount_percent,
            discount_amount_value=discount_amount,
            amount=gross_price,
            value_tax=tax_percent,
            value_tax_amount=tax_amount,
            user_customer_id=customer.id,
            user_customer_number=customer.customer_number,
            user_customer_first_name=customer.first_name,
            user_customer_last_name=customer.last_name,
            user_customer_street=customer.street,
            user_customer_street_number=customer.street_number,
            user_customer_postcode=customer.postcode,
            user_customer_city=customer.city,
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
        purchase = Purchase.objects.create(
            invoice=invoice,
            customer=customer,
            service=service,
            discount=discount,
            status=PaymentStatus.UNPAID,
            subtotal=gross_price,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            tax_percent=tax_percent,
            tax_amount=tax_amount,
            total=total,
            payment_method=PaymentMethod.BANK_TRANSFER,
        )
        if request is not None:
            transaction.on_commit(
                lambda: SendInvoiceEmail().send_invoice_email(request, invoice)
            )
        return purchase


class CreateInvoicePDF:
    def create_pdf(self, request, invoice):
        html_string = render_to_string('templates/invoice_course.html', {
            "invoice": invoice
        })

        from weasyprint import HTML

        html = HTML(
            string=html_string,
            base_url=request.build_absolute_uri()
        )

        # write_pdf belong to weasyprint
        pdf = html.write_pdf()

        # Only Invoice in PDF
        return pdf


# After purchase will send you the E-Mail with invoice
class SendInvoiceEmail:
    def send_invoice_email(self, request, invoice):
        from django.core.mail import EmailMessage
        from django.conf import settings

        customer = invoice.customer

        pdf_service = CreateInvoicePDF()
        pdf_file = pdf_service.create_pdf(request, invoice)

        # Build email
        body = {
            "first_name": customer.first_name,
        }

        html_answer = render_to_string(
            "templates/email_with_invoice.html", body)
        confirmation_message = EmailMessage(
            subject=f"Deine Rechnung {invoice.invoice_number}",
            body=html_answer,
            from_email=f"Start in Krypto <{settings.DEFAULT_FROM_EMAIL}>",
            to=[customer.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )

        confirmation_message.attach(
            f"invoice_{invoice.invoice_number}.pdf",
            pdf_file,
            "application/pdf"
        )

        confirmation_message.content_subtype = "html"
        confirmation_message.send()


class CheckPurchase:
    @staticmethod
    def check_purchase(customer, service_id):
        purchase = Purchase.objects.filter(
            customer=customer,
            service_id=service_id,
        ).first()
        if purchase:
            return Response(
                {'message': _('You already purchased this service.')},
                status=status.HTTP_409_CONFLICT,
            )
