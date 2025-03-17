from django.urls import path, re_path, include
from ledger import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'ledger'
urlpatterns = [
    path('', views.CustomerVisit.as_view(), name="index"),
    path('ledger/', views.AllEmployee.as_view(), name="all_employee"),
    path('ledger/add_employee/', views.EmpCreate.as_view(), name="add_employee"),
    path('ledger/register/', views.TaoTaiKhoan.as_view(), name="register"),
    path('ledger/services/', views.AllServices.as_view(), name="services"),
    path('ledger/services/detail/<int:pk>/', views.ServiceDetail.as_view(), name="service_detail"),
    path('ledger/services/add_services/', views.AddService.as_view(), name="add_service"),
    path('ledger/update_employee_status/', views.UpdateTech.as_view(), name="update_tech_status"),
    path('ledger/tech_vacation/<int:pk>/', views.TechVacationView.as_view(), name="vacation"),
    path('ledger/chat_room/<int:pk>/', views.ChatView.as_view(), name="chat_room"),
    path('ledger/chat_room/detail/<int:pk>/', views.ChatDetailView.as_view(), name="chat_detail"),
    path('ledger/user_chat_room/', views.UserChatView.as_view(), name="user_chat_room"),
    path('ledger/chat/<int:pk>/create/', views.ChatCreateView.as_view(), name="chat_create"),
    path('ledger/user_chat_create/', views.UserChatCreateView.as_view(), name="user_chat_create"),
    path('ledger/user_chat_room/detail/<int:pk>/', views.UserChatDetailView.as_view(), name="user_chat_detail"),
    path('ledger/walkin/', views.ClientWalkinView.as_view(), name='walkin' ),
    path('ledger/chat/<int:chat_id>/like/', views.ChatLikeView.as_view(), name='chat_like'),
    path('ledger/chat_user/<int:chat_id>/like/', views.ChatUserLikeView.as_view(), name='user_chat_like'),
    path('ledger/chat/<int:pk>/delete/', views.chat_delete, name='chat_delete'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
