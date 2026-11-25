from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from company_app.models import Company
from .serializer import CompanySerializer

class CompanyView(APIView):
    def get(self, request):
        company = Company.objects.first()
        if not company:
            return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(company, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        company = Company.objects.first()
        #Create a new company if none exists
        if not company:
            serializer = CompanySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Otherwise, update the existing company
        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Die Daten wurden aktualisiert."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
