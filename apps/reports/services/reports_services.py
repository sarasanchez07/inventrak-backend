from apps.movements.models import Movement
from apps.inventory.permissions import InventoryPermissionService
from decimal import Decimal

class ReportService:
    @staticmethod
    def get_filtered_movements(user, start_date=None, end_date=None, movement_type=None, inventory_id=None, product_id=None):
        """
        Versión ultra-robusta de filtrado de movimientos.
        """
        queryset = Movement.objects.select_related('product', 'user', 'product__inventory')

        # 1. Seguridad: El personal solo ve movimientos de sus inventarios asignados.
        if user.role != 'admin':
            queryset = queryset.filter(product__inventory__staff=user)

        # 2. Filtro por Producto (Fundamental para el Modal)
        def is_valid(val):
            return val and str(val).lower() not in ['all', '', 'none', 'undefined', 'null']

        if is_valid(product_id):
            queryset = queryset.filter(product_id=product_id)

        # 3. Filtro por Inventario
        if is_valid(inventory_id):
            queryset = queryset.filter(product__inventory_id=inventory_id)

        # 4. Filtro por Rango de fechas
        if is_valid(start_date) and is_valid(end_date):
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])

        # 5. Filtro por Tipo de movimiento (CORRECCIÓN CRÍTICA)
        if is_valid(movement_type):
            m_type_str = str(movement_type).upper()
            if m_type_str == 'CANCELLED':
                queryset = queryset.filter(is_cancelled=True)
            elif m_type_str in ['IN', 'OUT']:
                queryset = queryset.filter(type=m_type_str, is_cancelled=False)
            # Si es 'ALL' o invalido, no filtra por tipo (muestra todo)

        return queryset.order_by('-created_at').distinct()