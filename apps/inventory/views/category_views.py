# apps/inventory/views/category_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.inventory.models import Category, Product
from apps.inventory.serializers.category_serializers import CategorySerializer
from apps.inventory.serializers.product_serializers import ProductSerializer
from django.shortcuts import get_object_or_404
from apps.authentication.permissions import IsAdminOrAssignedStaff
from apps.authentication.models.user import User


class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista categorías con filtros para Admin y Personal"""
        user = request.user
        inventory_id = request.query_params.get('inventory_id')
        search = request.query_params.get('search')

        # 1. El Admin puede ver TODO por defecto
        if user.role == User.Role.ADMIN:
            categories = Category.objects.all()
        # 2. El Personal solo ve lo de sus inventarios asignados
        else:
            categories = Category.objects.filter(
                inventory__in=user.assigned_inventories.all()
            )

        # Filtro por inventario específico
        if inventory_id:
            categories = categories.filter(inventory_id=inventory_id)

        # Filtro por nombre de categoría (búsqueda)
        if search:
            categories = categories.filter(name__icontains=search)

        categories = categories.select_related('inventory').order_by('-created_at')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Crea categorías validando permisos de asignación"""
        inventory_id = request.data.get('inventory')
        user = request.user

        # Seguridad de "Islas": Validamos si el personal tiene acceso a ese inventario
        if user.role != User.Role.ADMIN:
            if not user.assigned_inventories.filter(id=inventory_id).exists():
                return Response(
                    {"error": "Acceso denegado. No tienes permiso para este inventario."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrAssignedStaff]

    def patch(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        self.check_object_permissions(request, category)

        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        self.check_object_permissions(request, category)

        if Product.objects.filter(category=category).exists():
            return Response(
                {"error": "No se puede eliminar una categoría con productos asociados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        category.delete()
        return Response(
            {"message": "Categoría eliminada."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CategoryProductsView(APIView):
    """Devuelve los productos que pertenecen a una categoría específica."""
    permission_classes = [IsAuthenticated, IsAdminOrAssignedStaff]

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        self.check_object_permissions(request, category)

        products = Product.objects.filter(category=category).select_related(
            'base_unit', 'presentation', 'category'
        )
        serializer = ProductSerializer(products, many=True)
        return Response({
            "category_name": category.name,
            "inventory_name": category.inventory.name,
            "products": serializer.data,
        })