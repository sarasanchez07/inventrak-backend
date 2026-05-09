from django.apps import AppConfig

class MovementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Debe coincidir exactamente con la ruta de la carpeta
    name = 'apps.movements' 
    # El label debe ser único para evitar conflictos en migraciones
    label = 'movements'