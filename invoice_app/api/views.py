from rest_framework.viewsets import ModelViewSet
from .serializer import InvoiceSerializer, InvoiceServiceSerializer, ServiceCatalogSerializer, TaxSerializer
from invoice_app.models import Invoice, InvoiceService, ServiceCatalog, Tax, PaymentStatus
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import render
from company_app.models import Company
from auth_app.models import User
from rest_framework import status
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
import os
from rest_framework import permissions 
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

# You can onyl see the list of the invoices but you cannot change the invoice
class InvoiceView(ModelViewSet):
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
        invoice.save()

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

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny] )
    def preview_course(self, request, pk=None):
        invoice = self.get_object()

        return render(request, 'templates/invoice_course.html', {
            "invoice": invoice
        })


    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def pdf(self, request, pk='None'):
        invoice = self.get_object()

        html_string= render_to_string('templates/invoice.html', {
            "invoice": invoice
        })

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
    
class InvoiceServiceView(ModelViewSet):
    queryset = InvoiceService.objects.all()
    serializer_class = InvoiceServiceSerializer


class ServiceCatalogView(ModelViewSet):
    queryset = ServiceCatalog.objects.all()
    serializer_class = ServiceCatalogSerializer

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):

        data = request.data

        errors = []
        saved = []

        with transaction.atomic():
            for index, item in enumerate(data):
                item_id = item.get('id')

                instance = None

                if item_id is not None:
                    instance = ServiceCatalog.objects.filter(
                        pk=item_id).first()

                serializer = self.get_serializer(
                    instance=instance,
                    data=item,
                    partial=False,
                )

                if serializer.is_valid():
                    obj = serializer.save()
                    saved.append(ServiceCatalogSerializer(obj).data)
                else:
                    errors.append(
                        {
                            'index': index,
                            'error': serializer.errors
                        }
                    )

            if errors:
                transaction.set_rollback(True)
                return Response(
                    {
                        'status': 'failed',
                        'message': 'Validation failed. No changes were applied.',
                        'errors': errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                'status': 'OK',
                'count': len(saved),
                'results': saved,
            },
            status=status.HTTP_200_OK,
        )

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
