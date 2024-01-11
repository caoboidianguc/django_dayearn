from django.contrib import admin
from .models import Technician, Khach, Service, DayOff

admin.site.register(Technician)
admin.site.register(Khach)
admin.site.register(Service)
admin.site.register(DayOff)