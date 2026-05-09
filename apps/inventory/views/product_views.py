from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.inventory.models import Product
from apps.inventory.serializers.product_serializers import ProductSerializer
from apps.inventory.services.product_services import ProductService
from apps.authentication.permissions import IsAdminOrAssignedStaff
from apps.inventory.permissions import InventoryPermissionService

class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        user = request.user
        inventory_id = request.query_params.get('inventory_id')
        search = request.query_params.get('search')
        
        # 1. Base de la consulta según el ROL
        products = InventoryPermissionService.filter_products_for_user(user)
        # 2. Filtros adicionales (opcionales)
        if inventory_id:
            # Si el personal asignado a varios inventarios quiere ver solo uno
            products = products.filter(inventory_id=inventory_id)
        
        if search:
            products = products.filter(name__icontains=search)

        category_id = request.query_params.get('category_id')
        if category_id:
            products = products.filter(category_id=category_id)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):

        inventory_id = request.data.get('inventory')
        user = request.user

        # 1. El Admin tiene permiso total
        if not InventoryPermissionService.can_create_in_inventory(
            request.user,
            inventory_id
        ):
            return Response(
                {
                    "error": "Acceso denegado. No tienes permiso para operar en este inventario."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = ProductService.create_product(
                validated_data=serializer.validated_data,
                user=request.user
            )

            output = ProductSerializer(product)
            return Response(output.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProductDetailView(APIView):
    permission_classes = [IsAdminOrAssignedStaff]

    def patch(self, request, pk):
        """Para editar campos específicos como la presentación"""
        product = get_object_or_404(Product, pk=pk)
        self.check_object_permissions(request, product)

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        self.check_object_permissions(request, product)

        product.delete()
        return Response({"message": "Producto eliminado"}, status=status.HTTP_204_NO_CONTENT)