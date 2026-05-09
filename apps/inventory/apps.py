# apps/inventory/apps.py
from django.apps import AppConfig
from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory' # <--- IMPORTANTE: Debe incluir el prefijo 'apps.'

    def ready(self):
        import apps.inventory.signals