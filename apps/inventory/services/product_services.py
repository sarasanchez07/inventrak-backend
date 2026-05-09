# apps/inventory/services/product_service.py

from django.db import transaction
from apps.inventory.models import Product
from apps.movements.models import Movement

from apps.movements.services.movement_service import MovementService
from decimal import Decimal

class ProductService:
    @staticmethod
    @transaction.atomic
    def create_product(validated_data, user):
        """
        Crea un producto y registra automáticamente el movimiento inicial si corresponde.
        """
        # 1. Creamos el producto
        product = Product.objects.create(**validated_data)
        
        # 2. Calculamos y registramos el movimiento inicial si hay stock
        stock_initial_presentations = validated_data.get('stock_initial_presentations', 0)
        
        if stock_initial_presentations > 0:
            quantity_per_presentation = validated_data.get('quantity_per_presentation', 1)
            initial_stock = Decimal(str(stock_initial_presentations)) * Decimal(str(quantity_per_presentation))
            
            # Delegamos la creación del movimiento al servicio correspondiente
            MovementService.create_initial_movement(
                product=product,
                quantity=initial_stock,
                user=user # Pasamos el usuario que crea el producto si queremos auditoría real
            )
            
        return product