from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class ProfileType(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        BUSINESS = "business", _("Business")

    class TitleChoices(models.TextChoices):
        HERR = 'Herr', _('Herr')
        FRAU = 'Frau', _('Frau')
        DIVERS = 'Divers', _('Divers')

    # AbstractUser
    # username, first_name, last_name, email,
    title = models.CharField(max_length=20, choices=TitleChoices)
    customer_number = models.CharField(max_length=50, unique=True)

    # I overwrite email
    email = models.EmailField(max_length=150, unique=True)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)

    # Location
    street = models.CharField(max_length=200)
    street_number = models.CharField(max_length=10)
    postcode = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    phone = models.CharField(blank=True, max_length=20, default="")

    has_subscription = models.BooleanField(default=False)

    description = models.TextField(blank=True, default="")

    working_hours = models.CharField(max_length=50, blank=True, default="")

    role = models.CharField(
        max_length=10,
        choices=ProfileType,
        default=ProfileType.CUSTOMER
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # 1. Erst speichern → damit ID existiert
        super().save(*args, **kwargs)

        # 2. Nur beim ersten Speichern customer_number setzen
        if is_new and not self.customer_number:
            self.customer_number = f"QW{self.id:06d}"

            # 3. Nur dieses Feld updaten
            super().save(update_fields=["customer_number"])
    
    def __str__(self):
        return f"{self.username} {self.first_name}"