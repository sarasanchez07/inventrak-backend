from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.inventory.models import Inventory
from apps.inventory.services.inventory_services import InventoryService
from apps.inventory.serializers import InventorySerializer
from apps.authentication.permissions import IsAdminUser, IsAdminOrAssignedStaff
from apps.authentication.models.user import User


class InventoryCreateView(APIView):
    permission_classes = [IsAdminUser]  # Solo Admin crea inventarios

    def post(self, request):
        # Usamos el servicio para aplicar la lógica de las 4 opciones
        inventory = InventoryService.create_inventory_with_config(request.data)
        serializer = InventorySerializer(inventory)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InventoryListView(APIView):
    """Lista inventarios según el rol del usuario."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == User.Role.ADMIN:
            inventories = Inventory.objects.all().order_by('name')
        else:
            inventories = user.assigned_inventories.all().order_by('name')

        serializer = InventorySerializer(inventories, many=True)
        return Response(serializer.data)


# Vista para "ENTRAR" y ver el mensaje de bienvenida (Nivel 2)
class InventoryDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAdminOrAssignedStaff()]

    def get(self, request, pk):
        inventory = get_object_or_404(Inventory, pk=pk)
        self.check_object_permissions(request, inventory)

        # Preparamos los datos legibles
        unidades = [{"id": u.id, "name": u.name} for u in inventory.allowed_units.all()]
        presentaciones = [{"id": p.id, "name": p.name} for p in inventory.allowed_presentations.all()]

        # Categorías vinculadas
        categorias = [{"id": c.id, "name": c.name} for c in inventory.categories.all()]

        return Response(
            {
                "id": inventory.id,
                "name": inventory.name,
                "message": f"Bienvenido al inventario {inventory.name}",
                "config": {
                    "tipo": inventory.get_selected_option_display(),
                    "selected_option": inventory.selected_option,
                    "switches": {
                        "concentracion": inventory.has_concentration,
                        "presentacion": inventory.has_presentation,
                        "cantidad_por_presentacion": inventory.has_quantity_per_presentation,
                        "vencimiento": inventory.has_expiration_date,
                    },
                    "catalogos": {
                        "unidades": unidades,
                        "presentaciones": presentaciones,
                    },
                },
                "categorias_registradas": categorias,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        """Actualiza la configuración del inventario (Admin solamente)."""
        inventory = get_object_or_404(Inventory, pk=pk)
        
        updated_inventory = InventoryService.update_inventory_config(inventory, request.data)
        
        # Reutilizamos la lógica del GET para devolver el objeto completo actualizado
        return self.get(request, pk)

    def delete(self, request, pk):
        """Elimina un inventario (Admin solamente)."""
        inventory = get_object_or_404(Inventory, pk=pk)
        inventory.delete()
        
        return Response({"message": "Inventario eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)