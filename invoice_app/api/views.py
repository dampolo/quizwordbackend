import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from rest_framework import mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from auth_app.models import User
from company_app.models import Company
from invoice_app.models import (Invoice, InvoiceService, PaymentStatus,
                                ServiceCatalog, Tax)

from .serializer import (InvoiceSerializer, InvoiceServiceSerializer,
                         ServiceCatalogSerializer, TaxSerializer)


class InvoiceView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        invoice = self.get_object()

        new_status = request.data.get("invoice_status")

        # Validate input
        valid_statuses = dict(PaymentStatus.choices).keys()
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Invalid payment_status. Allowed: {list(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        invoice.invoice_status = new_status
        invoice.save(update_fields=['invoice_status'])

        return Response(
            {"status": f"Payment status updated to: {new_status}"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny] )
    def preview(self, request, pk=None):
        invoice = self.get_object()

        return render(request, 'templates/invoice.html', {
            "invoice": invoice
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def pdf(self, request, pk='None'):
        invoice = self.get_object()

        html_string= render_to_string('templates/invoice.html', {
            "invoice": invoice
        })

        from weasyprint import HTML

        html = HTML(
            string=html_string,
            base_url=request.build_absolute_uri()
        )
        
        pdf=html.write_pdf()
        
        # check the option
        # /api/invoices/12/pdf/?download=true ---> download the invoice automaticly
        # /api/invoices/12/pdf/ ---> only view the invoice
        download = request.query_params.get('download')

        disposition_type = 'attachment' if download else 'inline'
        
        response=HttpResponse(pdf, content_type='application/pdf')

        response['Content-Disposition'] = (
            f'{disposition_type}; filename="invoice_{invoice.id}_{invoice.invoice_number}.pdf"'
        )
        
        return response    

# Service will be added to invoice
class InvoiceServiceView(ReadOnlyModelViewSet):
    queryset = InvoiceService.objects.all()
    serializer_class = InvoiceServiceSerializer

# Admin can put Premium and Pro
class ServiceCatalogView(ModelViewSet):
    queryset = ServiceCatalog.objects.all()
    serializer_class = ServiceCatalogSerializer
    permission_classes = [permissions.IsAdminUser]



class TaxAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        tax, created = Tax.objects.get_or_create(pk=1)
        serializer = TaxSerializer(tax)
        return Response(serializer.data)
    
    def patch(self, request):
        tax, created = Tax.objects.get_or_create(pk=1)

        serializer = TaxSerializer (
            tax, 
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
