from rest_framework import serializers
from ..models import Movement
from rest_framework.exceptions import ValidationError
from apps.movements.services.movement_service import MovementService

class MovementSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    # Para mostrar la unidad base en la tabla
    unit_name = serializers.ReadOnlyField(source='unit_name_at_time')
    edited_by = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.SerializerMethodField()
    display_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Movement
        fields = [
            'id', 'product', 'product_name', 'unit_name', 'user_name', 
            'type', 'quantity', 'reason', 'notes', 'created_at', 'is_edited', 'original_quantity', 'edited_by','unit_name_at_time', 'status','unit_type', 'display_quantity',
            'user_name_at_time'
        ]
        read_only_fields = ['user', 'is_edited', 'original_quantity', 'edited_by']
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.first_name if obj.user.first_name else obj.user.email
        return obj.user_name_at_time

    def get_product_name(self, obj):
        # Si el producto existe, devuelve su nombre actual, si no, el histórico
        return obj.product.name if obj.product else obj.product_name_at_time
    
    def get_unit_name(self, obj):
        # Si tiene respaldo histórico, usarlo (ideal para productos borrados)
        if obj.unit_name_at_time:
            return obj.unit_name_at_time
        # Si no hay respaldo pero el producto existe, sacarlo del producto
        if obj.product and obj.product.base_unit:
            return obj.product.base_unit.name
        return "N/A"
    
    def get_status(self, obj):
        """Esta es la lógica que tenías en el Admin, ahora disponible para la API"""
        if obj.is_cancelled:
            return "Anulado"
        if not obj.product:
            return "Inactivo"
        return "Activo"
    
    def get_display_quantity(self, obj):

        # PRESENTACIÓN
        if obj.unit_type == "PRESENTATION":

            if obj.product:
                # intenta obtener el nombre real del campo
                presentation = getattr(obj.product, "presentation", None)

                if presentation:
                    return f"{obj.quantity} {presentation}"

            return f"{obj.quantity} Presentación"

        # BASE
        if obj.product and obj.product.base_unit:
            return f"{obj.quantity} {obj.product.base_unit.name}"

        return f"{obj.quantity}"
    
    def validate(self, data):
        """
        Validación global del Serializer.
        Aquí verificamos que si es una salida, haya stock suficiente.
        """
        product = data.get('product') or getattr(self.instance, 'product', None)
        m_type = data.get('type')
        quantity = data.get('quantity') or getattr(self.instance, 'quantity', None)
        unit_type = data.get('unit_type', 'BASE')

        # Si el producto no existe (por seguridad)
        if not product:
            raise serializers.ValidationError({
                "product": "El movimiento no tiene producto asociado."
            })

        # No permitir editar movimientos anulados
        if self.instance and self.instance.is_cancelled:
            raise serializers.ValidationError({
                "error": "No se puede editar un movimiento anulado."
            })

        # Solo validamos stock en SALIDAS (OUT)
        if m_type == 'OUT':
            # 1. Convertimos la cantidad pedida a unidades base
            requested_qty = product.convert_to_base_unit(
                quantity, 
                is_presentation=(unit_type == 'PRESENTATION')
            )

            # 2. Verificamos contra el stock actual del producto
            if requested_qty > product.current_stock:
                raise serializers.ValidationError({
                    "quantity": f"Stock insuficiente. Disponible: {product.current_stock} unidades base."
                })

        return data

    def update(self, instance, validated_data):
        #El momvimiento inicial no puede ser editado
        if instance.is_initial:
            raise ValidationError(
                "El movimiento inicial no puede ser editado."
            )
        
        #No puede agregar una cantidad menor a 0
        new_quantity = validated_data.get('quantity', instance.quantity)

        if new_quantity <= 0:
            raise ValidationError(
                "La cantidad debe ser mayor a 0."
            )
    
        # 1. Obtenemos el usuario de la petición (quien está logueado en Postman/App)
        request = self.context.get("request")
        user = request.user if request else None

        # Delegar TODA la lógica al service
        return MovementService.edit_movement(
            movement=instance,
            user=user,
            quantity=new_quantity,
            reason=validated_data.get("reason")
        )