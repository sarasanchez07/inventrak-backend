from rest_framework import serializers
from apps.inventory.models import Category


class CategorySerializer(serializers.ModelSerializer):
    inventory_name = serializers.ReadOnlyField(source='inventory.name')

    class Meta:
        model = Category
        fields = ['id', 'name', 'inventory', 'inventory_name', 'created_at']

    def validate(self, attrs):
        """
        Valida unicidad de nombre dentro del mismo inventario.
        """
        name = attrs.get('name')
        inventory = attrs.get('inventory')

        if name and inventory:
            qs = Category.objects.filter(name__iexact=name, inventory=inventory)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": "Ya existe una categoría con ese nombre en este inventario."}
                )

        return attrs
