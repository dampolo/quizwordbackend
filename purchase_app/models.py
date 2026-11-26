from django.db import models
from auth_app.models import User
from invoice_app.models import Invoice, PaymentStatus, PaymentMethod, ServiceCatalog
from django.utils.translation import gettext_lazy as _



# -------------------------
# Bonus
# -------------------------
class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    percent_value = models.PositiveIntegerField(help_text="Rabatt % Wert")
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.percent_value}%)"



# -------------------------
# Buy
# -------------------------
class Purchase(models.Model):
    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase'
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases',
        limit_choices_to={'role': User.ProfileType.CUSTOMER}
    )


    service = models.ForeignKey(
        ServiceCatalog, on_delete=models.CASCADE, related_name='purchases')

    discount = models.ForeignKey(
        DiscountCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PAYPAL
    )

    # SNAPSHOT VALUES
    subtotal = models.DecimalField(max_digits=8, decimal_places=2)

    tax_percent = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2)

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=8, decimal_places=2)

    paypal_order_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.customer.first_name}, {self.customer.last_name}"