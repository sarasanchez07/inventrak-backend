# apps/movements/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.inventory.models import Inventory, Category, Product, BaseUnit, Presentation
from apps.movements.models import Movement
from decimal import Decimal
from apps.movements.services.movement_service import MovementService
from django.urls import reverse

User = get_user_model()

class MovementLogicTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # 1. Crear usuario para las pruebas
        self.user = User.objects.create_user(
            email="testuser@fundacion.com", 
            password="password123",
            role=User.Role.ADMIN
        )

        # 2. Configuración de Unidades y Presentación
        self.unit_pastilla = BaseUnit.objects.create(name="pastilla")
        self.pres_tableta = Presentation.objects.create(name="Tableta")
        
        # 3. CREAR EL INVENTARIO PRIMERO
        self.inventory = Inventory.objects.create(
            name="Farmacia Central",
            selected_option=1,
            has_concentration=True,
            has_presentation=True,
            has_quantity_per_presentation=True
        )
        self.inventory.allowed_units.add(self.unit_pastilla)
        self.inventory.allowed_presentations.add(self.pres_tableta)

        # 4. AHORA SÍ VINCULAR EL INVENTARIO AL USUARIO (Sistema de Islas)
        self.user.assigned_inventories.add(self.inventory)
        self.client.force_authenticate(user=self.user)
        
        self.category = Category.objects.create(name="Antibióticos", inventory=self.inventory)
    def test_product_creation_auto_generates_movement(self):
        """
        VERIFICACIÓN CLAVE: Al crear un producto, se debe generar un movimiento 
        de entrada automático por el stock inicial en UNIDADES BASE.
        """
        # Amoxaxilina: 20 tabletas x 20 pastillas = 400 pastillas iniciales
        # product.save() # No llamar a save directamente si queremos disparar lógica de Service
        # En tests de integración, es mejor usar el Service:
        from apps.inventory.services.product_services import ProductService
        product_data = {
            "name": "Amoxaxilina",
            "concentration": "500mg",
            "category": self.category,
            "inventory": self.inventory,
            "base_unit": self.unit_pastilla,
            "presentation": self.pres_tableta,
            "quantity_per_presentation": 20,
            "stock_initial_presentations": 20
        }
        product = ProductService.create_product(product_data, self.user)

        product.refresh_from_db()

        # 1. Verificar stock actual
        self.assertEqual(product.current_stock, Decimal("400.00"))

        # 2. Verificar que existe el movimiento de "Carga inicial"
        initial_movement = Movement.objects.filter(product=product, type='IN').first()
        self.assertIsNotNone(initial_movement)
        self.assertEqual(initial_movement.quantity, Decimal("400.00"))
        self.assertEqual(initial_movement.unit_type, 'BASE')
        self.assertEqual(
            initial_movement.user.email,
            self.user.email
        )

    def test_manual_out_movement_unit_base(self):
        """Prueba una salida manual de 5 unidades base (pastillas)"""
        from apps.inventory.services.product_services import ProductService
        product_data = {
            "name": "Amoxaxilina",
            "category": self.category,
            "inventory": self.inventory,
            "base_unit": self.unit_pastilla,
            "presentation": self.pres_tableta,
            "quantity_per_presentation": 20,
            "stock_initial_presentations": 20
        }
        product = ProductService.create_product(product_data, self.user)
        product.refresh_from_db()

        # CAMBIO: Ajusta esta URL según tu apps/movements/urls.py
        # Si usas router.register(r'', MovementViewSet), la URL es esta:
        # url = "/api/movements/register/" 
        url = reverse('movement-register')
        
        data = {
            "product": product.id,
            "type": "OUT",
            "quantity": 5,
            "unit_type": "BASE", 
            "reason": "Entrega a paciente"
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        product.refresh_from_db()
        self.assertEqual(product.current_stock, Decimal("395.00"))

    def test_recalculate_stock_consistency(self):
        """Verifica que el recálculo funcione con la carga inicial automática"""
        from apps.inventory.services.product_services import ProductService
        product_data = {
            "name": "Amoxaxilina",
            "category": self.category,
            "inventory": self.inventory,
            "base_unit": self.unit_pastilla,
            "presentation": self.pres_tableta,
            "quantity_per_presentation": 20,
            "stock_initial_presentations": 20 # Esto genera 400 pastillas
        }
        product = ProductService.create_product(product_data, self.user)
        product.refresh_from_db()

        # Registramos una salida de 20 pastillas
        MovementService.create_movement(
            product=product,
            user=self.user,
            movement_type="OUT",
            quantity=Decimal("20"),
            unit_type="BASE",
        )
        
        Movement.recalculate_product_stock(product)
        product.refresh_from_db()
        
        # CORRECCIÓN: 400 (inicial) - 20 (salida) = 380
        self.assertEqual(product.current_stock, Decimal("380.00"))

    def test_str_display_with_concentration(self):
        """Verifica el formato del nombre solicitado: Nombre (Concentración)"""
        product = Product(
            name="Metoclopramida",
            concentration="500mg",
            inventory=self.inventory
        )
        self.assertEqual(str(product), "Metoclopramida (500mg)")

    def test_insufficient_stock_validation(self):
        """Verifica que el sistema impida salidas mayores al stock disponible"""
        from apps.inventory.services.product_services import ProductService
        product_data = {
            "name": "Amoxaxilina",
            "category": self.category,
            "inventory": self.inventory,
            "base_unit": self.unit_pastilla,
            "presentation": self.pres_tableta,
            "quantity_per_presentation": 20,
            "stock_initial_presentations": 1 # Solo 20 pastillas
        }
        product = ProductService.create_product(product_data, self.user)

        url = reverse('movement-register')
        data = {
            "product": product.id,
            "type": "OUT",
            "quantity": 50, # Intento sacar 50 de 20
            "unit_type": "BASE"
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)