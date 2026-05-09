from rest_framework import serializers
from apps.inventory.models import Inventory, BaseUnit, Presentation

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'
        read_only_fields = ['has_concentration', 'has_presentation', 'has_quantity_per_presentation', 'has_expiration_date']