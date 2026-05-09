from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Movement
from apps.movements.services.movement_service import MovementService



@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "is_initial",
        "product_name_at_time",
        "type",
        "quantity_display",
        "get_unit_fixed",
        "status_display",
        "is_edited",
        "user",
        "created_at",
    )

    readonly_fields = (
        "product_name_at_time",
        "is_initial",
        "is_edited",
        "original_quantity",
        "edited_by",
        "unit_name_at_time",
        "cancelled_at",
        "cancelled_by", 
    )

    list_filter = (
        "type",
        "unit_type",
        "created_at",
        "user",
        "is_edited",
        "is_cancelled",
    )

    search_fields = (
        "product_name_at_time",
        "reason",
        "notes",
    )

    ordering = ("-created_at",)

    actions = ["cancel_movements"]

    # ✅ Crear usando el Service
    def save_model(self, request, obj, form, change):

        if not change:
            # ---- CREAR ----
            movement = MovementService.create_movement(
                product=obj.product,
                user=request.user,
                movement_type=obj.type,
                quantity=obj.quantity,
                unit_type=obj.unit_type,
                reason=obj.reason,
            )
            obj.pk = movement.pk
            return

        # ---- EDITAR ----
        original = Movement.objects.get(pk=obj.pk)

        # 🚨 SI ESTÁ MARCANDO COMO ANULADO
        if not original.is_cancelled and obj.is_cancelled:
            MovementService.cancel_movement(
                movement=original,
                user=request.user,
            )
            return

        # ---- EDICIÓN NORMAL ----
        MovementService.edit_movement(
            movement=original,
            user=request.user,
            quantity=obj.quantity if obj.quantity != original.quantity else None,
            product=obj.product if obj.product != original.product else None,
            reason=obj.reason if obj.reason != original.reason else None,
        )

    # Permisos (según lo que decidieron)
    def has_change_permission(self, request, obj=None):
        from apps.authentication.models.user import User
        return request.user.role in [User.Role.ADMIN, "personal"]

    def has_add_permission(self, request):
        from apps.authentication.models.user import User
        return request.user.role in [User.Role.ADMIN, "personal"]

    def has_delete_permission(self, request, obj=None):
        from apps.authentication.models.user import User
        return request.user.role == User.Role.ADMIN

    # -------- Visual helpers --------

    def get_unit_fixed(self, obj):
        if obj.unit_name_at_time:
            return obj.unit_name_at_time

        if obj.product and obj.product.base_unit:
            return obj.product.base_unit.name

        return "N/A"

    get_unit_fixed.short_description = "Unidad"

    def quantity_display(self, obj):
        if obj.is_edited and obj.original_quantity:
            return format_html(
                '<span title="Originalmente era: {}" style="color: #ff9800; cursor: help;">{}</span>',
                obj.original_quantity,
                obj.quantity,
            )
        return obj.quantity

    quantity_display.short_description = "Cantidad"

    def status_display(self, obj):
        if obj.is_cancelled:
            return format_html(
                '<span style="color: red; font-weight: bold;">Anulado</span>'
            )

        if not obj.product:
            return format_html(
                '<span style="color: #666; font-weight: bold;">Inactivo</span>'
            )

        return format_html('<span style="color: green;">Activo</span>')

    status_display.short_description = "Estado"

    # -------- Cancelación usando Service --------

    @admin.action(description="Anular movimientos seleccionados")
    def cancel_movements(self, request, queryset):

        for movement in queryset:
            try:
                MovementService.cancel_movement(
                    movement=movement,
                    user=request.user,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error al anular movimiento {movement.id}: {str(e)}",
                    level="ERROR",
                )