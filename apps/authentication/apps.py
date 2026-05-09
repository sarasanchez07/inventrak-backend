# apps/authentication/apps.py
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication" # Nombre completo para el path
    label = "authentication"     # Etiqueta para las migraciones y modelos