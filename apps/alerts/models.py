from django.db import models
from apps.inventory.models import Product

class Alert(models.Model):
    ALERT_TYPES = (
        ('LOW_STOCK', 'Stock Bajo'),
        ('EXPIRATION', 'Vencimiento Próximo'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.product.name}"
