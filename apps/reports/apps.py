from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'  # Nombre completo para el path
    label = 'reports'      # Etiqueta única para migraciones y modelos