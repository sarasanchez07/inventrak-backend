from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from apps.authentication.services.auth_service import AuthService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({"error": "Por favor ingrese un correo electrónico válido."}, status=status.HTTP_400_BAD_REQUEST)
            
        # El sistema valida si el correo ya está en la BD
        if User.objects.filter(email=email).exists():
            AuthService.send_password_reset_email(email)
            return Response(
                {"message": "Se han enviado las instrucciones de recuperación al correo (si existe).", "exists": True},
                status=status.HTTP_200_OK
            )
        else:
            # Para evitar enumeración de usuarios, normalmente se devuelve el mismo mensaje,
            # pero mantendremos el comportamiento actual si el frontend depende de ello.
            return Response(
                {"error": "Ese correo no está registrado en el sistema."},
                status=status.HTTP_404_NOT_FOUND
            )

class PasswordResetConfirmView(APIView):
    """
    Vista para actualizar directamente la contraseña una vez el correo ha sido validado en el frontend.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get('uidb64')
        token = request.data.get('token')
        new_password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not uidb64 or not token or not new_password or not confirm_password:
            return Response(
                {"error": "Todos los campos obligatorios son requeridos (token y contraseñas)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "Las contraseñas no coinciden."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if not default_token_generator.check_token(user, token):
                return Response(
                    {"error": "El enlace de recuperación es inválido o ha expirado."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Contraseña actualizada con éxito. Ya puedes iniciar sesión."}, 
                status=status.HTTP_200_OK
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Ese correo no está registrado en el sistema."}, 
                status=status.HTTP_404_NOT_FOUND
            )