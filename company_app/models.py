from django.db import models


class Company(models.Model):
    # The database allows exactly one company profile.
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    name = models.CharField(max_length=200)
    street = models.CharField(max_length=200)
    street_number = models.CharField(max_length=10)
    postcode = models.CharField(max_length=5)
    city = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=200)
    tax_number = models.CharField(max_length=11)
    founding = models.CharField(max_length=4)
    email = models.EmailField(max_length=150)
    bank = models.CharField(max_length=200)
    bank_account = models.CharField(max_length=34)
    swift_code = models.CharField(max_length=11)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name='company_single_profile'),
        ]

    def __str__(self):
        return self.name
