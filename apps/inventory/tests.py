from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.inventory.models import Inventory, Category, Product, BaseUnit, Presentation

User = get_user_model()

class InventoryTests(APITestCase):

    def setUp(self):
        # 1. Configuración de Catálogos
        self.unit_kg = BaseUnit.objects.create(name="Kg")
        self.pres_bolsa = Presentation.objects.create(name="Bolsa")

        # 2. Crear Inventarios (Islas)
        self.inv_alimentos = Inventory.objects.create(
            name="Alimentos", 
            selected_option=2, # Opción Alimentos
            has_expiration_date=True
        )
        self.inv_alimentos.allowed_units.add(self.unit_kg)
        self.inv_alimentos.allowed_presentations.add(self.pres_bolsa)

        self.inv_objetos = Inventory.objects.create(
            name="Objetos", 
            selected_option=3
        )

        # 3. Crear Categoría
        self.cat_granos = Category.objects.create(name="Granos", inventory=self.inv_alimentos)

        # 4. Crear Usuarios
        self.admin = User.objects.create_user(email="admin@test.com", password="123", role=User.Role.ADMIN)
        self.staff_alimentos = User.objects.create_user(email="staff@test.com", password="123", role="estudiante")
        self.staff_alimentos.assigned_inventories.add(self.inv_alimentos)

    def test_staff_list_only_assigned_products(self):
        """Verifica que el personal solo vea productos de su inventario asignado"""
        # Crear un producto en cada inventario
        Product.objects.create(name="Arroz", inventory=self.inv_alimentos, category=self.cat_granos)
        cat_obj = Category.objects.create(name="Herramientas", inventory=self.inv_objetos)
        Product.objects.create(name="Martillo", inventory=self.inv_objetos, category=cat_obj)

        self.client.force_authenticate(user=self.staff_alimentos)
        url = reverse('product-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo debe ver 1 producto (Arroz), no 2
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Arroz")

    def test_staff_cannot_create_category_in_other_inventory(self):
        """Verifica el bloqueo de seguridad si el personal intenta 'saltar' a otra isla"""
        self.client.force_authenticate(user=self.staff_alimentos)
        url = reverse('category-list-create')
        data = {"name": "Nueva Cat Maliciosa", "inventory": self.inv_objetos.id}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_validation_error_date(self):
        """Verifica que falle si se envía una fecha inexistente (como el error del 31 de abril)"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-list')
        data = {
            "name": "Producto Error Fecha",
            "inventory": self.inv_alimentos.id,
            "category": self.cat_granos.id,
            "expiration_date": "2026-04-31" # Fecha inválida
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expiration_date", response.data)

    def test_admin_can_delete_category_without_products(self):
        """Verifica que se pueda eliminar una categoría vacía, pero no una con stock"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('category-detail', kwargs={'pk': self.cat_granos.id})
        
        # Primero intentamos con un producto asociado
        Product.objects.create(name="Frijol", inventory=self.inv_alimentos, category=self.cat_granos)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Ahora eliminamos el producto y luego la categoría
        Product.objects.all().delete()
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)