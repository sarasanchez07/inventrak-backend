from django.db import models
from django.conf import settings
from apps.inventory.models import Product
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError


class Movement(models.Model):

    _created_from_service = False

    MOVEMENT_TYPES = (
        ('IN', 'Entrada'),
        ('OUT', 'Salida'),
    )

    MOVEMENT_UNIT_TYPE = (
        ('BASE', 'Unidad base'),
        ('PRESENTATION', 'Presentación'),
    )

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements')
    # Guardamos el nombre del producto por si el objeto original se borra
    product_name_at_time = models.CharField(max_length=255, blank=True)
    # Guardamos LA CANTIDAD  del producto por si el objeto original se borra
    unit_name_at_time = models.CharField(max_length=50, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    # Guardamos el nombre del usuario por si se borra de la DB
    user_name_at_time = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    unit_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_UNIT_TYPE,
        default='BASE'
    )
    quantity = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0.01'))]
    )
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    original_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    resulting_stock = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='editor_movements'
    )

    is_cancelled = models.BooleanField(default=False, verbose_name="Anulado")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cancelled_movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_initial = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        # impedir creación fuera del service
        if not self.pk and not getattr(self, "_created_from_service", False):
            raise RuntimeError(
                "Movement must be created using MovementService"
            )

        # mantener datos históricos
        if self.product:
            self.product_name_at_time = self.product.name
            if self.product.base_unit:
                self.unit_name_at_time = self.product.base_unit.name

        if self.user:
            self.user_name_at_time = self.user.first_name if self.user.first_name else self.user.email

        self.full_clean()

        super().save(*args, **kwargs)
            

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    @staticmethod
    def recalculate_product_stock(product):

        movements = Movement.objects.filter(product=product, is_cancelled=False)

        total_in = Decimal("0")
        total_out = Decimal("0")

        for movement in movements:

            real_quantity = product.convert_to_base_unit(
                movement.quantity,
                is_presentation=(movement.unit_type == "PRESENTATION")
            )

            if movement.type == "IN":
                total_in += real_quantity
            elif movement.type == "OUT":
                total_out += real_quantity

        product.current_stock = total_in - total_out
        product.save()

    def clean(self):

        if not self.product and not self.product_name_at_time:
            raise ValidationError("El movimiento debe tener un producto o un registro histórico.")

        if self.quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")

    def __str__(self):
        # Esto es lo que aparecerá en el mensaje de éxito y en las listas
        return f"{self.type} - {self.product_name_at_time} ({self.quantity})"

    class Meta:
        ordering = ['-created_at']