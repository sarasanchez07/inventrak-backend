from django.urls import path
from .views.alert_views import AlertListView

urlpatterns = [
    path('', AlertListView.as_view(), name='alert-list'),
]
