from django.urls import path, re_path, include
from ledger import views
from django.contrib.auth import views as xem


app_name = 'ledger'
urlpatterns = [
    path('', views.CustomerVisit.as_view(), name="index"),
    path('ledger/', views.AllEmployee.as_view(), name="home"),
    path('ledger/add_employee/', views.EmpCreate.as_view(), name="add_employee"),
    path('ledger/register/', views.TaoTaiKhoan.as_view(), name="register"),
    path('ledger/services/', views.AllServices.as_view(), name="services"),
    path('ledger/services/add_services/', views.AddService.as_view(), name="add_service"),
    path('ledger/employee_turn/<int:pk>/', views.EmployeeTurn.as_view(), name="tech_turn"),
]
