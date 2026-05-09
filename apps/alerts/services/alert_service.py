from django.utils import timezone
from datetime import timedelta
from apps.inventory.models import Product
from django.db.models import F

class AlertService:
    @staticmethod
    def get_dynamic_alerts(user, inventory_id=None):
        """
        Calcula alertas en tiempo real para el usuario:
        1. Stock bajo
        2. Vencimiento próximo (30 días)
        """
        from apps.inventory.permissions import InventoryPermissionService
        accessible_products = InventoryPermissionService.filter_products_for_user(user)
        
        if inventory_id:
            accessible_products = accessible_products.filter(inventory_id=inventory_id)
        
        alerts = []
        today = timezone.now().date()
        threshold_date = today + timedelta(days=30)
        
        # 1. Alertas de Stock Bajo
        # Filtramos productos donde current_stock <= stock_min_presentations * quantity_per_presentation
        low_stock_products = accessible_products.filter(
            current_stock__lte=F('stock_min_presentations') * F('quantity_per_presentation')
        ).select_related('inventory', 'base_unit')
        
        for p in low_stock_products:
            alerts.append({
                "product_id": p.id,
                "product_name": p.name,
                "current_stock": f"{p.current_stock} {p.base_unit.name if p.base_unit else ''}",
                "reason": "Stock Bajo",
                "type": "LOW_STOCK",
                "inventory": p.inventory.name
            })
            
        # 2. Alertas de Vencimiento
        # Solo productos en inventarios que manejan vencimiento
        expiring_products = accessible_products.filter(
            inventory__has_expiration_date=True,
            expiration_date__lte=threshold_date,
            expiration_date__isnull=False
        ).select_related('inventory', 'base_unit')
        
        for p in expiring_products:
            # Evitar duplicados (si ya tiene stock bajo, mostramos ambas o priorizamos?)
            # El usuario dice que salga el motivo, así que mostramos ambas si aplica
            alerts.append({
                "product_id": p.id,
                "product_name": p.name,
                "current_stock": f"{p.current_stock} {p.base_unit.name if p.base_unit else ''}",
                "reason": f"Vence el {p.expiration_date.strftime('%d/%m/%Y')}",
                "type": "EXPIRATION",
                "inventory": p.inventory.name
            })
            
        return alerts
