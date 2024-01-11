from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TechnicSerializer, KhachSerializer, ServiceSerializer
from ledger.models import Technician, Khach, Service


class TechView(generics.CreateAPIView):
    queryset = Technician.objects.all()
    serializer_class = TechnicSerializer
    
    
# @api_view()
# def khach(request):
#     items = Khach.objects.all()
#     serialized_item = KhachSerializer(items, many=True)
#     return Response(serialized_item.data)
class KhachView(generics.ListAPIView):
    queryset = Khach.objects.all()
    serializer_class = KhachSerializer
    
class ServiceView(generics.CreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer