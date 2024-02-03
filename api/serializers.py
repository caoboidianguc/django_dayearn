from rest_framework import serializers
from ledger.models import Technician, Khach, Service


class TechnicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technician
        fields = '__all__'
        
        
# class ServiceSerializer(serializers.ModelSerializer):
#     service = serializers.CharField(max_length=30)
#     price = serializers.FloatField(source='gia')
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('service', 'price', 'time_perform','description')


class KhachSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(read_only=True, many=True)
    technician = TechnicSerializer()
    class Meta:
        model = Khach
        fields = ('id','full_name', 'phone', 'email','time_at','day_comes', 'points', 'desc', 'services', 'technician')
        
        
