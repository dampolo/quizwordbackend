from rest_framework import generics
from .serializer import CustomerProfileSerializer
from rest_framework.permissions import IsAuthenticated

# This method show the whole profile from Customer
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    serializer_class = CustomerProfileSerializer
    # Customer can see only his profile
    def get_object(self):
        return self.request.user