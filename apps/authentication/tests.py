from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.inventory.models import Inventory
from django.contrib.auth import get_user_model # Usa siempre esta función

# Esta es la única forma segura de llamar al usuario
User = get_user_model() 

class AuthenticationTests(APITestCase):

    def setUp(self):
        # Crear inventarios de prueba
        self.inventory_1 = Inventory.objects.create(name="Alimentos", selected_option=2)
        
        # Crear un Administrador
        self.admin_user = User.objects.create_user(
            email="admin@fundacion.org",
            password="password123",
            role=User.Role.ADMIN,
            first_name="Admin"
        )
        
        # Crear Personal con acceso restringido
        self.staff_user = User.objects.create_user(
            email="staff@fundacion.org",
            password="password123",
            role="estudiante", # Nivel 2
            first_name="Staff"
        )
        self.staff_user.assigned_inventories.add(self.inventory_1) # Asignar isla

    def test_login_success(self):
        """Verifica que un usuario pueda obtener sus tokens JWT"""
        url = reverse('login')
        data = {"email": "admin@fundacion.org", "password": "password123"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data) # Verifica que entregue la 'llave'

    def test_admin_can_create_personnel(self):
        """Verifica que solo el Admin pueda registrar personal nuevo"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('personnel-create')
        data = {
            "first_name": "Nuevo Trabajador",
            "email": "nuevo@fundacion.org",
            "password": "securepassword",
            "role": "estudiante",
            "assigned_inventories": [self.inventory_1.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_cannot_create_personnel(self):
        """Verifica que el personal NO pueda registrar a otros (Seguridad de Nivel 1)"""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('personnel-create')
        data = {"email": "intruso@fundacion.org", "password": "123"}
        
        response = self.client.post(url, data)
        # Debe retornar 403 porque no es Admin
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_user(self):
        """Verifica que el Admin pueda eliminar personal"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-detail', kwargs={'pk': self.staff_user.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.staff_user.id).exists())

    def test_edit_user_partial(self):
        """Verifica la edición parcial (PATCH) del nombre de un usuario"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-detail', kwargs={'pk': self.staff_user.id})
        data = {"first_name": "Staff Actualizado"}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.staff_user.refresh_from_db()
        self.assertEqual(self.staff_user.first_name, "Staff Actualizado")