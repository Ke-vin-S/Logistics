from django.test import TestCase
from django.utils import timezone
from shipments.models import Shipment
from django.core.exceptions import ValidationError

from shipments.services.status_services import update_shipment_status


class ShipmentModelTests(TestCase):
    def setUp(self):
        self.shipment = Shipment.objects.create(
            shipment_id="SHIP100",
            order_id="ORD100",
            origin={"lat": 7.8731, "lng": 80.7718},
            destination={"lat": 6.9271, "lng": 79.8612},
            demand=10
        )

    def test_schedule_from_pending(self):
        scheduled_time = timezone.now()
        update_shipment_status(self.shipment, 'scheduled', scheduled_time)
        self.assertEqual(self.shipment.status, 'scheduled')
        self.assertEqual(self.shipment.scheduled_dispatch, scheduled_time)

    def test_dispatch_from_scheduled(self):
        update_shipment_status(self.shipment, 'scheduled')
        update_shipment_status(self.shipment, 'dispatched')
        self.assertEqual(self.shipment.status, 'dispatched')
        self.assertIsNotNone(self.shipment.actual_dispatch)

    def test_invalid_dispatch_from_pending(self):
        with self.assertRaises(ValidationError):
            update_shipment_status(self.shipment, 'dispatched')

    def test_delivered_from_in_transit(self):
        update_shipment_status(self.shipment, 'scheduled')
        update_shipment_status(self.shipment, 'dispatched')
        update_shipment_status(self.shipment, 'delivered')
        self.assertEqual(self.shipment.status, 'delivered')
        self.assertIsNotNone(self.shipment.delivery_time)

    def test_invalid_delivered_from_pending(self):
        with self.assertRaises(ValidationError):
            update_shipment_status(self.shipment, 'delivered')

    def test_failed_from_active_states(self):
        update_shipment_status(self.shipment, 'failed')
        self.assertEqual(self.shipment.status, 'failed')

    def test_invalid_failed_from_delivered(self):
        update_shipment_status(self.shipment, 'scheduled')
        update_shipment_status(self.shipment, 'dispatched')
        update_shipment_status(self.shipment, 'delivered')
        with self.assertRaises(ValidationError):
            update_shipment_status(self.shipment, 'failed')
