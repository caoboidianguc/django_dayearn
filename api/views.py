from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TechnicSerializer, KhachSerializer, ServiceSerializer
from ledger.models import Technician, Khach, Service, TakeTurn



class AllTechView(generics.ListCreateAPIView):
    queryset = Technician.objects.all()
    serializer_class = TechnicSerializer

# generics.RetrieveUpdateAPIView => GET PUT PATCH
class SingleTech(generics.RetrieveUpdateAPIView):
    queryset = Technician.objects.all()
    serializer_class = TechnicSerializer
    
    
# @api_view()
# def khach(request):
#     items = Khach.objects.all()
#     serialized_item = KhachSerializer(items, many=True)
#     return Response(serialized_item.data)
class SingleKhach(generics.RetrieveUpdateAPIView):
    queryset = Khach.objects.all()
    serializer_class = KhachSerializer
    
class AllKhachView(generics.ListCreateAPIView):
    queryset = Khach.objects.all()
    serializer_class = KhachSerializer    

# generics.ListCreateAPIView => get, post
class ServiceView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    
    
    