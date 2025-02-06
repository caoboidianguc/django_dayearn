from django.urls import path, re_path, include
from ledger import views
from django.contrib.auth import views as xem
from django.conf import settings
from django.conf.urls.static import static


app_name = 'ledger'
urlpatterns = [
    path('', views.CustomerVisit.as_view(), name="index"),
    path('ledger/', views.AllEmployee.as_view(), name="all_employee"),
    path('ledger/add_employee/', views.EmpCreate.as_view(), name="add_employee"),
    path('ledger/register/', views.TaoTaiKhoan.as_view(), name="register"),
    path('ledger/services/', views.AllServices.as_view(), name="services"),
    path('ledger/services/add_services/', views.AddService.as_view(), name="add_service"),
    path('ledger/update_employee_status/', views.UpdateTech.as_view(), name="update_tech_status"),
    path('ledger/tech_vacation/<int:pk>/', views.TechVacationView.as_view(), name="vacation"),
    path('ledger/chat_room/<int:pk>/', views.ChatView.as_view(), name="chat_room"),
    path('ledger/chat_create/<int:pk>/', views.ChatCreateView.as_view(), name="chat_create"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
