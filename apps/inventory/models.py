# apps/inventory/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import transaction
from django.conf import settings

class BaseUnit(models.Model):
    name = models.CharField(max_length=50) # mg, ml, kg, unidad, etc.
    def __str__(self): return self.name

class Presentation(models.Model):
    name = models.CharField(max_length=50) # Frasco, Bolsa, Caja, etc.
    def __str__(self): return self.name

class Inventory(models.Model):
    def __str__(self):
        return self.name
    
    OPTION_CHOICES = [
        (1, '(Mg, Ml, g, Pastilla) perfecto para medicamentos'),
        (2, '(Kg, Lb, unidad) perfecto para alimentos'),
        (3, '(Unidades exactas) perfecto para objetos '),
        (4, 'Personalizado'),
    ]
    
    name = models.CharField(max_length=100, unique=True) # Nombre del inventario
    description = models.TextField(blank=True) # Descripcion del inventario
    created_at = models.DateTimeField(auto_now_add=True) # Fecha de creacion automatica
    selected_option = models.IntegerField(choices=OPTION_CHOICES) # selector con las opciones de unidades

    # checbox de configuración 
    has_concentration = models.BooleanField(default=False) # El inventario va a tener concentracion en sus productos
    has_presentation = models.BooleanField(default=False)   # El inventario va a tener presentaciones para sus productos
    has_quantity_per_presentation = models.BooleanField(default=False) # Al tener presetacion el sistema activa eso de cantidad por presentacion
    has_expiration_date = models.BooleanField(default=False) # Los productso de su inventario tiene fecha de vencimiento

    allowed_units = models.ManyToManyField(BaseUnit, blank=True) #Personalizar Unidades
    allowed_presentations = models.ManyToManyField(Presentation, blank=True) #Personalizar Configuracion

    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=100)
    # Esta línea es el "ancla": vincula la categoría a UN solo inventario
    inventory = models.ForeignKey(
        'Inventory', 
        on_delete=models.CASCADE, 
        related_name='categories' # Esto permite el acceso desde el inventario
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        # Opcional: Evita nombres de categorías duplicados dentro del mismo inventario
        unique_together = ('name', 'inventory') 

    def __str__(self):
        return f"{self.name} - {self.inventory.name}"
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category_name_at_time = models.CharField(max_length=100, blank=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Creado por"
    )
    
    # Campos opcionales que se activan según el inventario
    concentration = models.CharField(max_length=50, blank=True, null=True)
    base_unit = models.ForeignKey(BaseUnit, on_delete=models.SET_NULL, null=True)
    presentation = models.ForeignKey(Presentation, on_delete=models.SET_NULL, null=True)
    expiration_date = models.DateField(blank=True, null=True)

    quantity_per_presentation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("1.00"))]
    )

    stock_initial_presentations = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Stock (siempre visible)
    stock_min_presentations = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):
        # Mantenemos registro histórico de la categoría
        if self.category:
            self.category_name_at_time = self.category.name

        # Capturamos el usuario si viene del Admin o un servicio
        created_by_user = kwargs.pop('created_by_user', None)
        if created_by_user:
            self.created_by = created_by_user
        super().save(*args, **kwargs)

    def get_stock_display(self, custom_stock=None):
        # Si no hay unidad base asignada, devolver solo el número
        unit_name = self.base_unit.name if self.base_unit else "unidades"
        
        stock_to_display = custom_stock if custom_stock is not None else self.current_stock

        if not self.quantity_per_presentation or not self.presentation:
            return f"{stock_to_display} {unit_name}"

        total_units = int(stock_to_display)
        units_per_pres = int(self.quantity_per_presentation)

        presentations = total_units // units_per_pres
        remaining_units = total_units % units_per_pres

        if remaining_units > 0:
            return f"{presentations} {self.presentation.name} + {remaining_units} {unit_name}"
        
        return f"{presentations} {self.presentation.name}"
    
    def get_total_units(self):
        """
        Retorna el stock actual en unidades base.
        """
        return self.current_stock

    def get_presentations_available(self):
        """
        Convierte el stock total en:
        - cantidad de presentaciones completas
        - unidades sobrantes

        Ejemplo:
        580 unidades con 30 por presentación
        -> 19 presentaciones y 10 unidades
        """

        if not self.quantity_per_presentation:
            return {
                "presentations": 0,
                "units": self.current_stock
            }

        total_units = int(self.current_stock)
        units_per_pres = int(self.quantity_per_presentation)

        presentations = total_units // units_per_pres
        remaining_units = total_units % units_per_pres

        return {
            "presentations": presentations,
            "units": remaining_units
        }

    def has_low_stock(self):

        min_base = (
            self.stock_min_presentations *
            self.quantity_per_presentation
        )

        return self.current_stock <= min_base
    
    def convert_to_base_unit(self, quantity, is_presentation=False):

        if is_presentation:
            return quantity * self.quantity_per_presentation

        return quantity
    
    def __str__(self):
        # 1. Si el inventario usa concentración y el producto la tiene, prioridad a la concentración
        if self.inventory.has_concentration and self.concentration:
            return f"{self.name} ({self.concentration})"
        
        # 2. Si no tiene concentración, mostramos la unidad base (ej: Arroz (kg))
        unit = self.base_unit.name if self.base_unit else "Sin unidad"
        return f"{self.name} ({unit})"