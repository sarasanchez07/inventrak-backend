from apps.movements.models import Movement
from apps.inventory.models import Product
from decimal import Decimal

def backfill_resulting_stock():
    products = Product.objects.all()
    print(f"Buscando stock histórico para {products.count()} productos...")
    
    for product in products:
        movements = Movement.objects.filter(product=product).order_by('created_at', 'id')
        current_running_stock = Decimal("0")
        
        for m in movements:
            if m.is_cancelled:
                # Los anulados no afectan el stock, pero guardamos el acumulado hasta ese punto
                m.resulting_stock = current_running_stock
            else:
                # Convertimos a unidad base
                qty = product.convert_to_base_unit(
                    m.quantity, 
                    is_presentation=(m.unit_type == "PRESENTATION")
                )
                
                if m.type == "IN":
                    current_running_stock += qty
                else:
                    current_running_stock -= qty
                
                m.resulting_stock = current_running_stock
            
            m._created_from_service = True # Evitar RuntimeError en el model save
            m.save()
            
        print(f"Producto {product.name}: Stock final recalculado {current_running_stock} vs DB {product.current_stock}")

if __name__ == "__main__":
    backfill_resulting_stock()
