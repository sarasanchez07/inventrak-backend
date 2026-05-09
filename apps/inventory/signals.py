from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.conf import settings
from django.db import transaction

from apps.inventory.models import Product
from apps.movements.services.movement_service import MovementService


# Signal removed. Initial stock logic moved to ProductService.
