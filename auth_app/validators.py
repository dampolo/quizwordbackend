import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        errors = []
        if len(password) < 10:
            errors.append(_("Your password must contain at least 10 characters."))
        if not re.search(r'[A-Z]', password):
            errors.append(_("At least one uppercase letter is required."))
        if not re.search(r'[a-z]', password):
            errors.append(_("At least one lowercase letter is required."))
        if not re.search(r'[0-9]', password):
            errors.append(_("At least one digit is required."))
        if not re.search(r'[@$!%+\-/*?&]', password):
            errors.append(_("At least one special character is required (@ $ ! % + - / * ? &)."))
        if re.search(r'\s', password):
            errors.append(_("Password must not contain any spaces."))        
        if errors:
            raise ValidationError(errors)
        
    def get_help_text(self):
        return _(
            "Your password must meet the following requirements:",
            "- At least 10 characters long",
            "- At least one uppercase letter (A-Z)",
            "- At least one lowercase letter (a-z)",
            "- At least one digit (0-9)",
            "- At least one special character (@ $ ! % + - / * ? &)",
            "- No spaces"
        )