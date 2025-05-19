from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from kafka_client.producer import publish_event


def update_shipment_status(shipment, new_status, timestamp=None):
    allowed_transitions = {
        'pending': ['scheduled', 'failed'],
        'scheduled': ['dispatched', 'failed', 'pending'],
        'dispatched': ['delivered', 'failed'],
    }

    current = shipment.status
    if new_status not in allowed_transitions.get(current, []):
        raise ValidationError(f"Cannot move from {current} to {new_status}.")

    with transaction.atomic():
        now = timezone.now()
        shipment.status = new_status

        if new_status == 'scheduled':
            shipment.scheduled_dispatch = timestamp or now
        elif new_status == 'dispatched':
            shipment.actual_dispatch = timestamp or now
        elif new_status == 'delivered':
            shipment.delivery_time = timestamp or now

        shipment.save(update_fields=['status', 'scheduled_dispatch', 'actual_dispatch', 'delivery_time', 'updated_at'])

        if new_status in ['delivered', 'failed', 'dispatched']:
            publish_event(
                topic="shipment.status.updated",
                key=str(shipment.order_id),
                payload={
                    "shipment_id": shipment.shipment_id,
                    "order_id": shipment.order_id,
                    "status": new_status,
                    "timestamp": now.isoformat()
                }
            )
