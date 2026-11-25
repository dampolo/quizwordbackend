from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from company_app.models import Company
from .permissions import IsSuperuser
from .serializer import CompanySerializer


class CompanyView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        company = Company.objects.first()
        if company is None:
            return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, context={'request': request})
        return Response(serializer.data)


    def post(self, request):
        if Company.objects.exists():
            return Response({'message': 'Company already exists'}, status=status.HTTP_409_CONFLICT)
        return self._save_company(request)


    def patch(self, request):
        return self._save_company(request, Company.objects.first())


    def delete(self, request):
        deleted, _ = Company.objects.all().delete()
        if not deleted:
            return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


    def _save_company(self, request, company=None):
        serializer = CompanySerializer(
            company, data=request.data, partial=company is not None,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        if company is None:
            try:
                with transaction.atomic():
                    serializer.save()
            except IntegrityError:
                if not Company.objects.exists():
                    raise
                return Response({'message': 'Company already exists'}, status=status.HTTP_409_CONFLICT)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer.save()
        return Response({'message': 'Die Daten wurden aktualisiert.'})
