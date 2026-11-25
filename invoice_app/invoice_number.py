from invoice_app.models import Invoice


class GenerateInvoiceNumber:
    @staticmethod
    def generate_invoice_number():
        """
        Generate a new sequential invoice number with the format: #000001

        The function:
        - Extracts the numeric part from existing invoice numbers (after #')
        - Finds the highest existing number
        - Increments it by 1
        - Returns the new number formatted with leading zeros
        """
        from django.db.models import Max
        from django.db.models.functions import Substr, Cast
        from django.db.models import IntegerField

        # Annotate each customer with the numeric portion of customer_number
        # Example: "#000123" → 123
        last_invoice = (
            Invoice.objects
            .annotate(num=Cast(Substr('invoice_number', 3), IntegerField()))
            .aggregate(max_num=Max('num'))['max_num']
        )

        # If at least one number exists, increment it; otherwise start at 1
        next_number = (last_invoice + 1) if last_invoice else 1

        # Format result as # + 6-digit zero-padded number
        return f"#{next_number:06d}"
