import logging
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.inventory.models import Product
from ..serializers.movement_serializer import MovementSerializer
from ..models import Movement
from apps.movements.services.movement_service import MovementService

from apps.authentication.permissions import IsAdminUser, IsAdminOrOwner
from apps.authentication.models.user import User

class MovementCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        product_id = request.data.get('product')
        user = request.user

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "El producto no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Si es personal, validamos que tenga acceso al inventario del producto
        if user.role != User.Role.ADMIN:
            if not user.assigned_inventories.filter(id=product.inventory.id).exists():
                return Response(
                    {"error": "No tienes permiso para este inventario."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = MovementSerializer(data=request.data)

        if serializer.is_valid():
            try:
                movement = MovementService.create_movement(
                    product=product,
                    user=request.user,
                    movement_type=serializer.validated_data["type"],
                    quantity=serializer.validated_data["quantity"],
                    unit_type=serializer.validated_data.get("unit_type", "BASE"),
                    reason=serializer.validated_data.get("reason", ""),
                    notes=serializer.validated_data.get("notes", "")
                )

                return Response(
                    MovementSerializer(movement).data,
                    status=status.HTTP_201_CREATED
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Error inesperado: {e}", exc_info=True)
                return Response(
                    {"error": "Error interno del servidor. Contacte al administrador."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MovementDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAdminUser()]
        return [IsAdminOrOwner()]

    def patch(self, request, pk):
        try:
            movement = Movement.objects.get(pk=pk)
        except Movement.DoesNotExist:
            return Response(
                {"error": "Movimiento no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validamos objeto después de obtenerlo por si acaso (aunque get_permissions lo hace)
        self.check_object_permissions(request, movement)

        serializer = MovementSerializer(
            movement,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            try:
                new_product = None

                # 🔥 Si viene product en el request
                if "product" in serializer.validated_data:
                    product_id = serializer.validated_data["product"].id
                    new_product = Product.objects.get(pk=product_id)

                movement = MovementService.edit_movement(
                    movement=movement,
                    user=request.user,
                    product=new_product,  # 👈 AHORA SÍ
                    quantity=serializer.validated_data.get("quantity"),
                    reason=serializer.validated_data.get("reason"),
                    notes=serializer.validated_data.get("notes"),
                )

                movement.refresh_from_db()

                return Response(
                    MovementSerializer(movement).data
                )

            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Error inesperado: {e}", exc_info=True)
                return Response(
                    {"error": "Error interno del servidor. Contacte al administrador."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, pk):
        try:
            movement = Movement.objects.get(pk=pk)
        except Movement.DoesNotExist:
            return Response({"error": "Movimiento no encontrado."}, status=404)
        
        self.check_object_permissions(request, movement)

        serializer = MovementSerializer(movement)
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            movement = Movement.objects.get(pk=pk)
        except Movement.DoesNotExist:
            return Response(
                {"error": "Movimiento no encontrado."},
                status=404
            )
        
        self.check_object_permissions(request, movement)

        try:
            MovementService.cancel_movement(
                movement=movement,
                user=request.user
            )

            return Response(
                {"message": "Movimiento anulado correctamente."},
                status=status.HTTP_204_NO_CONTENT
            )

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado: {e}", exc_info=True)
            return Response(
                {"error": "Error interno del servidor. Contacte al administrador."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class MovementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get('product_id')
        inventory_id = request.query_params.get('inventory_id')
        search_user = request.query_params.get('search_user')
        movement_type = request.query_params.get('type')

        if request.user.role == User.Role.ADMIN:
            movements = Movement.objects.all()
        else:
            # El personal ve los movimientos de sus inventarios asignados
            movements = Movement.objects.filter(
                product__inventory__in=request.user.assigned_inventories.all()
            )
        
        if product_id:
            movements = movements.filter(product_id=product_id)
        
        if inventory_id:
            movements = movements.filter(product__inventory_id=inventory_id)

        if movement_type:
            movements = movements.filter(type=movement_type)

        if search_user:
            from django.db.models import Q
            movements = movements.filter(
                Q(user__email__icontains=search_user) | 
                Q(user__first_name__icontains=search_user) |
                Q(user__last_name__icontains=search_user)
            )

        movements = movements.order_by('-created_at')

        serializer = MovementSerializer(movements, many=True)
        return Response(serializer.data)