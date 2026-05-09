from django.urls import path
from .views.movement_views import MovementCreateView, MovementDetailView, MovementListView

urlpatterns = [
    path('', MovementListView.as_view(), name='movement-list'),
    path('register/', MovementCreateView.as_view(), name='movement-register'),
    path('<int:pk>/', MovementDetailView.as_view(), name='movement-detail'),
]
