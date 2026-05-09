from django.urls import path
from apps.authentication.views.login_view import LoginView
from apps.authentication.views.personnel_view import PersonnelCreateView, UserDetailView
# Corrige estas importaciones:
from apps.authentication.views.password_reset_view import (
    PasswordResetRequestView, 
    PasswordResetConfirmView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    # Cambia PasswordResetView por PasswordResetRequestView
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path('personnel/create/', PersonnelCreateView.as_view(), name='personnel-create'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]