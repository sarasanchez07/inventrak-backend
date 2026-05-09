from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class PersonnelService:
    @staticmethod
    @transaction.atomic
    def create_personnel(data):
        # Extraer inventarios para procesarlos por separado
        inventory_ids = data.pop('assigned_inventories', [])
        password = data.pop('password')
        
        # Crear el usuario (el 'username' puede ser el email en tu modelo)
        user = User.objects.create(**data)
        user.set_password(password)
        user.save()

        # Asignar inventarios si existen
        if inventory_ids:
            user.assigned_inventories.set(inventory_ids)
            
        return user