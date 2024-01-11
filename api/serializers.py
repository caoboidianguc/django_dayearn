from rest_framework import serializers
from ledger.models import Technician, Khach, Service


class TechnicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technician
        fields = ('name', 'phone', 'owner')
        
        
# class ServiceSerializer(serializers.ModelSerializer):
#     dichVu = serializers.CharField(max_length=30)
#     price = serializers.FloatField(source='gia')
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('dichVu', 'gia')


class KhachSerializer(serializers.ModelSerializer):
    services = ServiceSerializer()
    technician = TechnicSerializer()
    class Meta:
        model = Khach
        fields = ('full_name', 'phone', 'email', 'diem', 'desc', 'services', 'technician')
        
        
