from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    shipment_id = models.CharField(max_length=32, unique=True)
    order_id = models.CharField(max_length=32)  # Reference to order service

    origin = models.JSONField()
    destination = models.JSONField()

    demand = models.PositiveIntegerField(help_text="Amount of load required for this shipment (e.g., in kg or units)", default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_dispatch = models.DateTimeField(null=True, blank=True)
    actual_dispatch = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    assigned_vehicle_id = models.CharField(max_length=36, null=True, blank=True)  # Optional

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.shipment_id} ({self.status})"
