from django.test import TestCase
from django.utils import timezone
from shipments.models import Shipment
from django.core.exceptions import ValidationError

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
        self.shipment.mark_scheduled(scheduled_time=timezone.now())
        self.assertEqual(self.shipment.status, 'scheduled')
        self.assertIsNotNone(self.shipment.scheduled_dispatch)

    def test_dispatch_from_scheduled(self):
        self.shipment.mark_scheduled()
        self.shipment.mark_dispatched()
        self.assertEqual(self.shipment.status, 'dispatched')
        self.assertIsNotNone(self.shipment.actual_dispatch)

    def test_invalid_dispatch_from_pending(self):
        with self.assertRaises(ValidationError):
            self.shipment.mark_dispatched()

    def test_in_transit_from_dispatched(self):
        self.shipment.mark_scheduled()
        self.shipment.mark_dispatched()
        self.shipment.mark_in_transit()
        self.assertEqual(self.shipment.status, 'in_transit')

    def test_delivered_from_in_transit(self):
        self.shipment.mark_scheduled()
        self.shipment.mark_dispatched()
        self.shipment.mark_in_transit()
        self.shipment.mark_delivered()
        self.assertEqual(self.shipment.status, 'delivered')
        self.assertIsNotNone(self.shipment.delivery_time)

    def test_invalid_delivered_from_pending(self):
        with self.assertRaises(ValidationError):
            self.shipment.mark_delivered()

    def test_failed_from_active_states(self):
        self.shipment.mark_failed()
        self.assertEqual(self.shipment.status, 'failed')

    def test_invalid_failed_from_delivered(self):
        self.shipment.mark_scheduled()
        self.shipment.mark_dispatched()
        self.shipment.mark_in_transit()
        self.shipment.mark_delivered()
        with self.assertRaises(ValidationError):
            self.shipment.mark_failed()
