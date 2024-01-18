from django.urls import path
from datHen import views

app_name = "datHen"
urlpatterns = [
    path('all/', views.DatHenView.as_view(), name='listHen' ),
    path('schedule/', views.KhachLayHen.as_view(), name='schedule' ),
    path('get_client/', views.FindClient.as_view(), name='find_client' ),
    path('existclient/<int:pk>/', views.ExistFound.as_view(), name='exist_found' ),
    path('first_step/', views.FirstStep.as_view(), name='first_step' ),
    path('third_step/', views.ThirdStep.as_view(), name='third_step' ),
    path('tech/<int:pk>/', views.Second.as_view(), name='technician_detail' ),
]
