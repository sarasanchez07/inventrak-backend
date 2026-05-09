from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.inventory.models import Product, Inventory
from apps.movements.models import Movement
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Q
from apps.inventory.permissions import InventoryPermissionService
from apps.authentication.models.user import User

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        inventory_id = request.query_params.get('inventory_id')
        
        # 1. Base query for products based on role
        products_qs = InventoryPermissionService.filter_products_for_user(user)
        
        if inventory_id:
            products_qs = products_qs.filter(inventory_id=inventory_id)
            total_products = products_qs.count()
            
            # Movements for this specific inventory
            movements_qs = Movement.objects.filter(product__inventory_id=inventory_id)
            # If not admin, ensure they have permission to see this inventory
            if user.role != User.Role.ADMIN:
                if not user.assigned_inventories.filter(id=inventory_id).exists():
                     return Response({"error": "No tienes acceso a este inventario"}, status=403)
            
            total_movements = movements_qs.count()
            inventories = Inventory.objects.filter(id=inventory_id)
        else:
            # 2. General Global/Assigned view
            total_products = products_qs.count()
            
            if user.role == User.Role.ADMIN:
                total_movements = Movement.objects.count()
                inventories = Inventory.objects.all()
            else:
                assigned_inventories = user.assigned_inventories.all()
                total_movements = Movement.objects.filter(product__inventory__in=assigned_inventories).count()
                inventories = assigned_inventories

        inventory_data = []
        for inv in inventories:
            inventory_data.append({
                "id": inv.id,
                "name": inv.name,
                "description": inv.description,
                "created_at": inv.created_at,
                "products_count": inv.product_set.count() if hasattr(inv, 'product_set') else Product.objects.filter(inventory=inv).count(),
                "config": {
                    "switches": {
                        "concentracion": inv.has_concentration,
                        "presentacion": inv.has_presentation,
                        "cantidad_por_presentacion": inv.has_quantity_per_presentation,
                        "vencimiento": inv.has_expiration_date,
                    },
                    "catalogos": {
                        "unidades": [{"id": u.id, "name": u.name} for u in inv.allowed_units.all()],
                        "presentaciones": [{"id": p.id, "name": p.name} for p in inv.allowed_presentations.all()],
                    }
                }
            })

        # 3. Stock Status counts
        today = timezone.now().date()
        threshold_date = today + timedelta(days=30)

        # Low stock (Priority 1)
        low_stock_condition = Q(current_stock__lte=F('stock_min_presentations') * F('quantity_per_presentation'))
        low_stock_count = products_qs.filter(low_stock_condition).count()

        # Expiring soon (Priority 2: Expiring but NOT low stock for the segment width, 
        # though usually users want the total expiring count)
        expiring_condition = Q(inventory__has_expiration_date=True, expiration_date__lte=threshold_date, expiration_date__isnull=False)
        
        # This is for the bar segments
        expiring_only_count = products_qs.filter(expiring_condition).exclude(low_stock_condition).count()
        # This is for the total count if needed
        total_expiring_count = products_qs.filter(expiring_condition).count()

        # Normal stock
        normal_stock_count = total_products - (low_stock_count + expiring_only_count)

        return Response({
            "total_products": total_products,
            "total_movements": total_movements,
            "low_stock_count": low_stock_count,
            "expiring_count": total_expiring_count,
            "expiring_only_count": expiring_only_count,
            "normal_stock_count": normal_stock_count,
            "inventories": inventory_data,
            "role": user.role
        })
