from rest_framework import serializers
from ..models import Alert
from apps.inventory.serializers.product_serializers import ProductSerializer

class AlertSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 
            'type', 
            'message', 
            'is_resolved', 
            'created_at', 
            'product',
            'product_details'
        ]
