from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.inventory.models import Inventory, Category, Product
from apps.movements.models import Movement
from apps.movements.services.movement_service import MovementService
from decimal import Decimal

User = get_user_model()

class ReportSecurityTests(APITestCase):

    def setUp(self):
        # 1. Configuración de Base
        self.inventory = Inventory.objects.create(name="Farmacia", selected_option=1)
        self.category = Category.objects.create(name="General", inventory=self.inventory)
        self.product = Product.objects.create(
            name="Paracetamol", 
            inventory=self.inventory, 
            category=self.category,
            quantity_per_presentation=1
        )

        # 2. Usuarios
        self.admin = User.objects.create_user(
            email="admin@test.com", password="123", role=User.Role.ADMIN
        )
        self.staff_1 = User.objects.create_user(
            email="staff1@test.com", password="123", role="estudiante"
        )
        self.staff_2 = User.objects.create_user(
            email="staff2@test.com", password="123", role="estudiante"
        )

        # 3. Crear Movimientos (Mezclados)
        # Movimiento de Staff 1
        MovementService.create_movement(
            product=self.product,
            user=self.staff_1,
            movement_type="IN",
            quantity=Decimal("10.00"),
            unit_type="BASE",
            reason="Carga Staff 1"
        )
        # Movimiento de Staff 2
        MovementService.create_movement(
            product=self.product,
            user=self.staff_2,
            movement_type="IN",
            quantity=Decimal("5.00"),
            unit_type="BASE",
            reason="Carga Staff 2"
        )

        self.url = reverse('report-movements')

    def test_admin_can_see_all_movements(self):
        """Verifica que el Admin vea los movimientos de todos los usuarios"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debe ver 3 movimientos: Carga inicial (system) + Staff 1 + Staff 2
        self.assertGreaterEqual(len(response.data), 2)

    def test_staff_only_sees_their_own_movements(self):
        """Verifica que el Personal NO pueda ver movimientos ajenos (Regla de Seguridad)"""
        self.client.force_authenticate(user=self.staff_1)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo debe ver el movimiento que él mismo creó
        for movement in response.data:
            self.assertEqual(movement['user_full_name'], "staff1@test.com")
        
        # Verificar que no hay rastro del movimiento de Staff 2
        reasons = [m['reason'] for m in response.data]
        self.assertNotIn("Carga Staff 2", reasons)

    def test_filter_by_date_range(self):
        """Verifica que el filtro de fechas funcione correctamente"""
        self.client.force_authenticate(user=self.admin)
        
        # Filtro que incluye hoy
        import datetime
        today = datetime.date.today().isoformat()
        
        response = self.client.get(self.url, {
            'start_date': today,
            'end_date': today
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_export_format_pdf_status_code(self):
        """Verifica que la solicitud de PDF devuelva el Content-Type correcto"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?export=pdf")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_export_format_csv_status_code(self):
        """Verifica que la solicitud de CSV devuelva el Content-Type correcto"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?export=csv")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')