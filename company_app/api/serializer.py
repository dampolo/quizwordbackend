from rest_framework import serializers
from company_app.models import Company
from auth_app.models import User
import re
from datetime import datetime

class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = [
            'logo',
            'name',
            'street',
            'street_number',
            'postcode',
            'city',
            'owner_name',
            'tax_number',
            'founding',
            'email',
            'bank',
            'bank_account',
            'swift_code',
        ]
    
    def get_logo(self, company):
        request = self.context.get('request')

        if not company.logo:
            return None

        return request.build_absolute_uri(company.logo.url)

    def validate_postcode(self, value):
        pattern = re.compile(r'^[0-9]{4,5}$')
        if not pattern.match(value):
            raise serializers.ValidationError(
                'Postcode must be 4 or 5 digits.'
                )
        return value
    
    def validate_city(self, value):
        pattern = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ÿ\s-]+$')
        if not pattern.match(value):
            raise serializers.ValidationError(
            "City may contain only letters, spaces, and hyphens."
        )
        return value
    
    def validate_tax_number(self, value):
        pattern = re.compile(r'^DE[0-9]{9}$')
        if not pattern.match(value):
            raise serializers.ValidationError(
            "Tax number must start with 'DE' followed by 9 digits. Example: DE123456789."
        )
        return value            

    def validate_founding(self, value):
        pattern = re.compile(r'^[0-9]{4}$')
        if not pattern.match(value):
            raise serializers.ValidationError(
                "Founding year must be a 4-digit number (e.g., 1998)."
        )

        year = int(value)

        if year < 1800:
            raise serializers.ValidationError("Founding year cannot be earlier than 1800.")

        current_year = datetime.now().year

        if year > current_year:
            raise serializers.ValidationError(f"Founding year cannot be later than {current_year}.")
        
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists() and Company.objects.filter(email=value).exists:
            raise serializers.ValidationError("This email exists already.")
        return value
    
    def validate_swift_code(self, value):
        pattern = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?$')
        if not pattern.match(value):
            raise serializers.ValidationError(
            "Invalid SWIFT/BIC format. Example: DEUTDEFF or NEDSZAJJXXX."
        )
        return value
        
    def validate_bank_account(self, value):
        pattern = re.compile(r'^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$')
        if not pattern.match(value):
            raise serializers.ValidationError(
            "Invalid IBAN format. Example: DE44500105175407324931"
        )
        return value

    def validate(self, attrs):
        for key, value in attrs.items():
            if isinstance(value, str) and not value.strip():
                raise serializers.ValidationError({key: 'This field cannot be empty.'})
        return attrs