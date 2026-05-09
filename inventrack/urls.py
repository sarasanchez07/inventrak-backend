# inventrack/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse

def ping(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    # CAMBIA ESTO: de admin.site.status a admin.site.urls
    path('admin/', admin.site.urls), 
    
    # Asegúrate de que las rutas tengan el prefijo 'apps.'

    path('api/auth/', include('apps.authentication.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/movements/', include('apps.movements.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),


    # Documentación Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    #cron-job
    path('ping/', ping),
]