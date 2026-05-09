from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.inventory.models import Inventory, Category, Product, BaseUnit
from apps.alerts.services.alert_service import AlertService
from django.contrib.auth import get_user_model

User = get_user_model()

class AlertSystemTest(TestCase):
    def setUp(self):
        self.inventory = Inventory.objects.create(
            name="Test Inventory", 
            selected_option=1,
            has_expiration_date=True
        )
        self.category = Category.objects.create(name="Test Category", inventory=self.inventory)
        self.unit = BaseUnit.objects.create(name="unidad")
        
        self.user = User.objects.create_user(
            email="alert@test.com",
            password="password123",
            role=User.Role.ADMIN
        )

    def test_low_stock_dynamic_alert(self):
        # Producto con stock bajo (5 <= 10 * 1)
        Product.objects.create(
            name="Bajo Stock",
            category=self.category,
            inventory=self.inventory,
            base_unit=self.unit,
            stock_min_presentations=10,
            quantity_per_presentation=1,
            current_stock=5
        )
        
        alerts = AlertService.get_dynamic_alerts(self.user)
        
        # Debe haber al menos una alerta de tipo LOW_STOCK
        low_stock_alerts = [a for a in alerts if a['type'] == 'LOW_STOCK']
        self.assertTrue(len(low_stock_alerts) > 0)
        self.assertEqual(low_stock_alerts[0]['product_name'], "Bajo Stock")
        self.assertEqual(low_stock_alerts[0]['reason'], "Stock Bajo")

    def test_expiration_dynamic_alert(self):
        # Producto que vence en 15 días (dentro del umbral de 30)
        expiry_date = timezone.now().date() + timedelta(days=15)
        Product.objects.create(
            name="Vence Pronto",
            category=self.category,
            inventory=self.inventory,
            base_unit=self.unit,
            expiration_date=expiry_date,
            quantity_per_presentation=1,
            current_stock=100
        )
        
        alerts = AlertService.get_dynamic_alerts(self.user)
        
        # Debe haber al menos una alerta de tipo EXPIRATION
        expiration_alerts = [a for a in alerts if a['type'] == 'EXPIRATION']
        self.assertTrue(len(expiration_alerts) > 0)
        self.assertEqual(expiration_alerts[0]['product_name'], "Vence Pronto")
        self.assertIn("Vence el", expiration_alerts[0]['reason'])

    def test_no_alerts_when_stock_is_ok(self):
        # Producto con stock suficiente y sin vencimiento próximo
        expiry_date = timezone.now().date() + timedelta(days=60)
        Product.objects.create(
            name="Todo OK",
            category=self.category,
            inventory=self.inventory,
            base_unit=self.unit,
            expiration_date=expiry_date,
            stock_min_presentations=10,
            quantity_per_presentation=1,
            current_stock=50
        )
        
        alerts = AlertService.get_dynamic_alerts(self.user)
        
        # No debe haber alertas para este producto
        product_alerts = [a for a in alerts if a['product_name'] == "Todo OK"]
        self.assertEqual(len(product_alerts), 0)
