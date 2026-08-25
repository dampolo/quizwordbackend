from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializer import ChangeUsernameSerializer, CustomerProfileSerializer, DeleteAccountSerializer


# This method show the whole profile from Customer
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    serializer_class = CustomerProfileSerializer
    # Customer can see only his profile
    def get_object(self):
        return self.request.user

class ChangeUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangeUsernameSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.username = serializer.validated_data['username']
        user.save(update_fields=['username'])

        return Response({
            "detail": "Benutzername wurde erfolgreich geändert."
        })

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = DeleteAccountSerializer(
            data= request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        user = request.user
        user.delete()

        return Response(
            {'detail': 'Dein Konto wurde gelöscht.'},
            status=status.HTTP_204_OK
        )