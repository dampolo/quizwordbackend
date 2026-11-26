from rest_framework import generics
from purchase_app.api import serializer
from purchase_app import models
from rest_framework import permissions
from purchase_app.services import CheckPurchase
from rest_framework.response import Response
from rest_framework.views import APIView, View
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status


# User can see all his purchases
class CustomerPurchasesAPI(generics.ListAPIView):
    serializer_class = serializer.CustomerPurchasesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return models.Purchase.objects.filter(customer=self.request.user)


class CheckPurchaseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, service_id):

        response = CheckPurchase.check_purchase(
            request.user,
            service_id
        )

        if response:
            return response

        return Response(
            status=status.HTTP_200_OK
        )
