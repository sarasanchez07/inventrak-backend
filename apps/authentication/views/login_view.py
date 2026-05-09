from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.authentication.services.auth_service import AuthService
from drf_spectacular.utils import extend_schema
from apps.authentication.serializers.login_serializer import LoginSerializer

class LoginView(APIView):
    # Todos pueden intentar inciar sesion
    permission_classes = [AllowAny] 

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginSerializer} 
    )
    def post(self, request):
        #Pide el correo y la contraseña son las credenciales establecidas 
        # si hace parte del personal sus credenciales son las que le da el admin
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "El correo y la contraseña son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Llamamos al servicio que ahora devuelve rol e inventarios para acceder al dashboard correcto
            data = AuthService.login(email=email, password=password)
            return Response(data, status=status.HTTP_200_OK)
        
        except ValueError as e:
            # menejo de errores "Credenciales inválidas" para ingresar al sistema
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception:
            return Response(
                {"error": "Ocurrió un error inesperado en el servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )