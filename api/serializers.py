from rest_framework import serializers
from ledger.models import Technician, Khach, Service
import bleach
from datetime import timedelta, date
import datetime


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
        extra_kwargs = {
            'price': {'min_value': 1}
        }


class KhachSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True)
    technician = TechnicSerializer()
    class Meta:
        model = Khach
        fields = '__all__'
        
    def validate(self, attrs):
        attrs['full_name'] = bleach.clean(attrs['full_name'])
        attrs['desc'] = bleach.clean(attrs['desc'])
        muoi = datetime.now() + timedelta(minutes=13)
        if (attrs['day_comes'] == date.today() and attrs['time_at'] < datetime.time(hour=muoi.hour, minute=muoi.minute)):
            raise serializers.ValidationError("Can't make 10 minute ahead!")
        return super().validate(attrs)
  