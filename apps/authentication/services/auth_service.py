from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


class AuthService:
    """
    Servicio de autenticación.
    """

    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Autentica un usuario y genera tokens JWT.
    
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            dict: Tokens y datos del usuario
            
        Raises:
            ValueError: Si las credenciales son inválidas o el usuario está inactivo
        """
        user = authenticate(email=email, password=password)

        if not user:
            # Check if user is disabled
            inactive_user = User.objects.filter(email=email).first()
            if inactive_user and not inactive_user.is_active:
                 if inactive_user.check_password(password):
                     raise ValueError("Su cuenta ha sido desactivada. Por favor contacte al administrador.")

            raise ValueError("Credenciales inválidas")

        if not user.is_active:
            raise ValueError("Cuenta desactivada")

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "role": user.role,
            },
        }

    @staticmethod
    def send_password_reset_email(email):
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # En un entorno real, aquí pondrías la URL de tu frontend
            FRONTEND_URL = settings.FRONTEND_URL
            reset_url = f"{FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            send_mail(
                'Recuperación de Contraseña - InvenTrack',
                f'Haz clic en el siguiente enlace para restablecer tu clave: {reset_url}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        return True
