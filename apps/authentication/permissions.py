from rest_framework import permissions
from apps.authentication.models.user import User

class IsAdminUser(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con el rol 'admin'.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', None) == User.Role.ADMIN
        )

class IsStaffUser(permissions.BasePermission):
    """
    Permite acceso a cualquier usuario que NO sea admin (Personal Staff).
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', None) != User.Role.ADMIN
        )

class IsAdminOrOwner(permissions.BasePermission):
    """
    Permite acceso si es admin o si el objeto pertenece al usuario.
    """
    def has_object_permission(self, request, view, obj):
        # Admin lo ve todo
        if getattr(request.user, 'role', None) == User.Role.ADMIN:
            return True
        # El staff solo lo suyo
        return getattr(obj, 'user', None) == request.user

class IsAdminOrAssignedStaff(permissions.BasePermission):
    """
    Permite acceso si es admin o si es staff asignado a un inventario/producto.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, 'role', None) == User.Role.ADMIN:
            return True
            
        # Dependiendo del objeto, buscamos el inventario
        from apps.inventory.models import Inventory
        
        inventory = None
        if isinstance(obj, Inventory):
            inventory = obj
        elif hasattr(obj, 'inventory'):
            inventory = obj.inventory
        elif hasattr(obj, 'product') and obj.product:
            inventory = obj.product.inventory
        
        if inventory:
            return user.assigned_inventories.filter(id=inventory.id).exists()
        return False
