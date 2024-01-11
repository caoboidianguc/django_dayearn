from django.urls import path
from .views import TechView, KhachView, ServiceView



app_name = 'api'
urlpatterns = [
    path('tech/', TechView.as_view(), name='techView'),
    path('khach/', KhachView.as_view(), name='khachView'),
]

# should create a general view which directed inform to specific api ->
# path('', generalView, name='general')