"""
URL configuration for dayearn project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.views.generic.base import RedirectView


urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/ledger/images/dayearn.ico', permanent=False)),
    path('', include('ledger.urls')),
    re_path('accounts/', include("django.contrib.auth.urls")),
    path('sieuadmin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('dathen/', include('datHen.urls')),
    path('payment/', include('payment.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
