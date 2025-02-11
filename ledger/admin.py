from django.contrib import admin
from .models import Technician, Khach, Service

admin.site.register(Technician)

admin.site.register(Service)
admin.site.register(Khach)
# class KhachAdmin(admin.ModelAdmin):
#     actions = ['custom_delete_selected']
#     def custom_delete_selected(self, request, queryset):
#         for obj in queryset:
#             obj.technician = None
#             obj.services.clear()
#             obj.save()
#         queryset.delete()
#     custom_delete_selected.short_description = "Delete selected Khach entries safely"
