from django.db import transaction
from rest_framework.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP

from apps.inventory.models import Product
from apps.movements.models import Movement
from django.contrib.auth import get_user_model  
from django.db.models import F
User = get_user_model()
from django.utils import timezone

from django.db import transaction
from apps.inventory.models import Inventory


class MovementService:

    @staticmethod
    @transaction.atomic
    def create_movement(
        *,
        product,
        user,
        movement_type,
        quantity,
        unit_type,
        reason="",
        notes=""
    ):

        product = Product.objects.select_for_update().get(pk=product.pk)
        raw_quantity = Decimal(str(quantity))

        real_quantity = product.convert_to_base_unit(
            raw_quantity,
            is_presentation=(unit_type == "PRESENTATION")
        )

        if real_quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0.")
        
        # ---- calcular nuevo stock de salida ----
        if movement_type == "OUT":
            if product.current_stock < real_quantity:
                raise ValidationError(
                    f"Stock insuficiente. Disponible: {product.current_stock}"
                )
            product.current_stock = F("current_stock") - real_quantity

        else:  # IN
            product.current_stock = F("current_stock") + real_quantity

        product.save(update_fields=["current_stock"])
        product.refresh_from_db()

        # ---- crear movimiento ----
        movement = Movement(
            product=product,
            product_name_at_time=product.name,
            user=user,
            type=movement_type,
            quantity=quantity,
            unit_type=unit_type,
            reason=reason,
            notes=notes,
        )

        movement._created_from_service = True
        movement.resulting_stock = product.current_stock
        movement.save()

        return movement
    
    @staticmethod
    def get_system_user():
        user, created = User.objects.get_or_create(
            email="system@inventrak.local",
            defaults={
                "password": "!",
                "role": "ADMIN",
                "is_active": False,
                "is_system": True,
            }
        )
        if not created and (user.is_active or not user.is_system):
            user.is_active = False
            user.is_system = True
            user.save(update_fields=["is_active", "is_system"])
        return user
    
    @staticmethod
    @transaction.atomic
    def create_initial_movement(product, quantity, user=None):

        if user is None:
            user = MovementService.get_system_user()

        product = Product.objects.select_for_update().get(pk=product.pk)

        quantity = Decimal(str(quantity)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # ✅ stock inicial se SETEA, no se suma
        product.current_stock = quantity
        product.save(update_fields=["current_stock"])

        movement = Movement(
            product=product,
            product_name_at_time=product.name,
            user=user,
            type="IN",
            quantity=quantity,
            unit_type="BASE",
            reason="Carga inicial de inventario",
            is_initial=True,
        )
        movement._created_from_service = True
        movement.resulting_stock = product.current_stock
        movement.save()

        

    @staticmethod
    @transaction.atomic
    def edit_movement(*, movement, user, product=None, quantity=None, reason=None, notes=None):

        movement = Movement.objects.select_for_update().get(pk=movement.pk)

        if movement.is_initial:
            raise ValidationError("El movimiento inicial no puede ser editado.")
    
        original_product = Product.objects.select_for_update().get(pk=movement.product.pk)

        old_raw_qty = Decimal(str(movement.quantity))

        old_real_qty = movement.product.convert_to_base_unit(
            old_raw_qty,
            is_presentation=(movement.unit_type == "PRESENTATION")
        )
        movement_type = movement.type

        # CASO 1: CAMBIO DE PRODUCTO
        if product and product != movement.product:

            new_product = Product.objects.select_for_update().get(pk=product.pk)

            # 1️Revertir impacto del producto original
            if movement_type == "OUT":
                original_product.current_stock = F("current_stock") + old_real_qty
            else:
                original_product.current_stock = F("current_stock") - old_real_qty

            original_product.save(update_fields=["current_stock"])

            # 2️ Aplicar impacto al nuevo producto
            if movement_type == "OUT":
                new_product.current_stock = F("current_stock") - old_real_qty
            else:
                new_product.current_stock = F("current_stock") + old_real_qty

            new_product.save(update_fields=["current_stock"])

            movement.product = new_product
            movement.product_name_at_time = new_product.name

        # CASO 2: CAMBIO DE CANTIDAD
        if quantity is not None:
            new_raw_qty = Decimal(str(quantity))
            new_real_qty = original_product.convert_to_base_unit(
                new_raw_qty,
                is_presentation=(movement.unit_type == "PRESENTATION")
            )

            if new_real_qty <= 0:
                raise ValidationError("La cantidad debe ser mayor a 0.")

            # 1️⃣ Calcular la diferencia (Delta)
            # Si es OUT: delta = vieja_cantidad - nueva_cantidad
            # Ejemplo: Salió 4, ahora sale 7. Delta = 4 - 7 = -3. (Restamos 3 al stock)
            # Ejemplo: Salió 10, ahora sale 2. Delta = 10 - 2 = +8. (Sumamos 8 al stock)
            
            # Si es IN: delta = nueva_cantidad - vieja_cantidad
            # Ejemplo: Entró 5, ahora entra 8. Delta = 8 - 5 = +3. (Sumamos 3 al stock)
            
            if movement_type == "OUT":
                delta = old_real_qty - new_real_qty
            else:
                delta = new_real_qty - old_real_qty

            # 2️⃣ Validar si el stock resultante sería negativo (solo para el neto)
            original_product.refresh_from_db()
            if original_product.current_stock + delta < 0:
                raise ValidationError(f"No se puede realizar esta modificación porque el stock quedaría en negativo. Disponible actual: {original_product.current_stock}, Ajuste necesario: {delta}")

            # 3️⃣ Aplicar el delta de una sola vez
            original_product.current_stock = F("current_stock") + delta
            original_product.save(update_fields=["current_stock"])
            original_product.refresh_from_db()

            movement.quantity = new_raw_qty

        # Auditoría
        if not movement.is_edited:
            movement.original_quantity = old_real_qty
            movement.is_edited = True

        if reason is not None:
            movement.reason = reason
            
        if notes is not None:
            movement.notes = notes

        movement.edited_by = user
        movement.resulting_stock = original_product.current_stock
        movement.save()

        return movement
            

    @staticmethod
    @transaction.atomic
    def cancel_movement(*, movement, user):

        movement = Movement.objects.select_for_update().get(pk=movement.pk)
        product = Product.objects.select_for_update().get(pk=movement.product.pk)

        if movement.is_cancelled:
            raise ValidationError("El movimiento ya está anulado.")

        # Convertimos la cantidad a unidad base para restaurar el stock correctamente
        real_qty = product.convert_to_base_unit(
            Decimal(str(movement.quantity)),
            is_presentation=(movement.unit_type == "PRESENTATION")
        )

        # Revertir impacto en stock
        if movement.type == "IN":
            if product.current_stock < real_qty:
                raise ValidationError("No se puede anular porque el stock quedaría negativo.")
            product.current_stock = F("current_stock") - real_qty
        else:  # OUT
            product.current_stock = F("current_stock") + real_qty

        product.save(update_fields=["current_stock"])
        product.refresh_from_db()

        movement.is_cancelled = True
        movement.cancelled_by = user
        movement.cancelled_at = timezone.now()
        movement.resulting_stock = product.current_stock
        
        # Nota automática de anulación
        note_msg = "MOVIMIENTO ANULADO"
        if movement.notes:
            movement.notes = f"{movement.notes} | {note_msg}"
        else:
            movement.notes = note_msg

        movement.save(update_fields=["is_cancelled", "cancelled_by", "cancelled_at", "resulting_stock", "notes"])

        return movement