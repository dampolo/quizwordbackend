from rest_framework import generics 
from .serializer import CustomerProfileSerializer

# This method show the whole profile from Customer
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    # Customer can see only his profile
    def get_object(self):
        return self.request.user