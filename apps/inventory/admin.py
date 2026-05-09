from django.contrib import admin
from .models import Inventory, Category, Product, BaseUnit, Presentation

# Registro simple para catálogos
admin.site.register(BaseUnit)
admin.site.register(Presentation)

# Registro con buscador y filtros para Inventarios
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'selected_option', 'created_at')
    search_fields = ('name',)

# Registro para Categorías
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'inventory')
    list_filter = ('inventory',)
    search_fields = ('name',)

# Registro para Productos (el más detallado)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'inventory', 'get_stock_display', 'expiration_date')
    readonly_fields = ('current_stock',)
    list_filter = ('inventory', 'category')
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        # Aquí pasamos el usuario del Admin al modelo
        obj.save(created_by_user=request.user)  

    def get_stock_display(self, obj):
        return obj.get_stock_display()

    get_stock_display.short_description = "Stock Actual"