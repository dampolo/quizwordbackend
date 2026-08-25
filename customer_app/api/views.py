from rest_framework import generics
from .serializer import CustomerProfileSerializer, ChangeUsernameSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

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