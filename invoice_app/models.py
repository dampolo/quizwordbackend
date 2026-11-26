from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth_app.models import User


class PaymentMethod(models.TextChoices):
    PAYPAL = 'paypal', _('PayPal')
    BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
    PAYU = 'payu', _('payU')
    STRIPE = 'stripe', _('stripe')


class AboChoice(models.TextChoices):
    PREMIUM = "premium", _("Premium")
    PRO = "pro", _("Pro")


class TextSnippet(models.Model):
    key = models.CharField(max_length=100, unique=True)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.key


class InvoiceType(models.TextChoices):
    INVOICE = 'invoice', _('Invoice')
    CREDIT_NOTE = 'credit_note', _('Credit Note')


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')       # created but not yet due
    UNPAID = 'unpaid', _('Unpaid')         # overdue / not paid
    PAID = 'paid', _('Paid')               # payment received
    CANCELED = 'canceled', _('Canceled')   # invoice is canceled (storno)


class Invoice(models.Model):

    invoice_number = models.CharField(max_length=50, unique=True)

    invoice_type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        default=InvoiceType.INVOICE
    )

    invoice_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PAYPAL
    )

    abo_choice = models.CharField(
        max_length=20,
        choices=AboChoice.choices,
        default=AboChoice.PREMIUM
    )

    # create the invocie
    business = models.ForeignKey(
        User,
        related_name="issued_invoices",
        on_delete=models.PROTECT,
        limit_choices_to={'role': User.ProfileType.BUSINESS}
    )

    # Receive the invoice
    customer = models.ForeignKey(
        User,
        related_name="received_invoices",
        on_delete=models.PROTECT,
        limit_choices_to={'role': User.ProfileType.CUSTOMER}
    )

    # --- CUSTOMER SNAPSHOT ---
    user_customer_id = models.IntegerField()
    user_customer_number = models.CharField(max_length=10)
    user_customer_first_name = models.CharField(max_length=100)
    user_customer_last_name = models.CharField(max_length=100)
    user_customer_street = models.CharField(max_length=200)
    user_customer_street_number = models.CharField(max_length=10)
    user_customer_postcode = models.CharField(max_length=20)
    user_customer_city = models.CharField(max_length=100)

    # --- COMPANY SNAPSHOT ---
    company_name = models.CharField(max_length=255)
    company_street = models.CharField(max_length=255)
    company_street_number = models.CharField(max_length=20)
    company_postcode = models.CharField(max_length=10)
    company_city = models.CharField(max_length=100)
    company_tax_number = models.CharField(max_length=50)
    company_email = models.EmailField()
    company_bank = models.CharField(max_length=100)
    company_bank_account = models.CharField(max_length=34)
    company_swift_code = models.CharField(max_length=20)
    company_logo = models.ImageField(
        upload_to='invoice_company_logos/', null=True, blank=True)

    # --- STATUS INFO ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_finalized = models.BooleanField(default=False)

    # --- INVOICE TOTALS ---
    # Discount
    discount = models.DecimalField(
        decimal_places=2, max_digits=10, default=0)  # %
    discount_amount_value = models.DecimalField(
        decimal_places=2, max_digits=10, default=0)  # €
    # Amount
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    value_tax = models.DecimalField(decimal_places=2, max_digits=10)
    value_tax_amount = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f"Invoice {self.invoice_number}"

# Service for user, Premium or Pro
class InvoiceService(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name="services",
        on_delete=models.PROTECT
    )

    abo_choice = models.CharField(
        max_length=20,
        choices=AboChoice.choices,
    )

    # PRICE for this line item
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['invoice'],
                name='invoice_single_service',
            ),
            models.CheckConstraint(
                condition=models.Q(abo_choice__in=["premium", "pro"]),
                name="invoice_service_valid_choice",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="invoice_service_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.get_abo_choice_display()}: {self.amount} €"

# Admin can add new service to catalog
class ServiceCatalog(models.Model):
    abo_choice = models.CharField(
        max_length=20,
        choices=AboChoice.choices,
        unique=True,
    )

    # PRICE for this line item
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(abo_choice__in=["premium", "pro"]),
                name="service_catalog_valid_choice",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="service_catalog_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.get_abo_choice_display()}: {self.amount} €"


class Tax(models.Model):
    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False
    )

    name = models.CharField(max_length=20, default="MwSt")
    percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=19.00)
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Erzwingt immer nur ID = 1
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.percent}%)"
