import json
import unittest

from django.urls import reverse
from rest_framework.test import APITestCase
from shipments.models import Shipment
from shipments.tests.kafka_test_consumer import consume_messages


class ShipmentKafkaIntegrationTests(APITestCase):
    def setUp(self):
        self.shipment = Shipment.objects.create(
            shipment_id="SHIP-KAFKA-001",
            order_id="ORD-KAFKA-001",
            origin={"lat": 7.87, "lng": 80.77},
            destination={"lat": 6.92, "lng": 79.86},
            demand=5
        )

    @unittest.skip("Temporarily skipping this test")
    def test_dispatch_and_kafka_publish(self):
        # Schedule the shipment
        url_schedule = reverse("shipment-mark-scheduled", kwargs={"pk": self.shipment.pk})
        self.client.post(url_schedule, data={"scheduled_time": "2025-05-17T10:00:00Z"})

        # Dispatch the shipment
        url_dispatch = reverse("shipment-mark-dispatched", kwargs={"pk": self.shipment.pk})
        response = self.client.post(url_dispatch, data={"dispatch_time": "2025-05-17T10:15:00Z"})

        self.assertEqual(response.status_code, 200)

        # Consume Kafka messages
        messages = consume_messages("shipment.status.updated")

        dispatched = []
        for msg in messages:
            payload = json.loads(msg.value().decode("utf-8"))
            print("DEBUG Kafka:", payload)
            if payload["order_id"] == self.shipment.order_id and payload["status"] == "dispatched":
                dispatched.append(payload)

        self.assertTrue(dispatched, "Dispatched Kafka message not found.")
        self.assertEqual(dispatched[0]["shipment_id"], self.shipment.shipment_id)

    @unittest.skip("Temporarily skipping this test")
    def test_delivered_and_kafka_publish(self):
        # Full flow: schedule → dispatch → in_transit → deliver
        self.client.post(reverse("shipment-mark-scheduled", kwargs={"pk": self.shipment.pk}))
        self.client.post(reverse("shipment-mark-dispatched", kwargs={"pk": self.shipment.pk}))
        self.client.post(reverse("shipment-mark-in-transit", kwargs={"pk": self.shipment.pk}))
        response = self.client.post(
            reverse("shipment-mark-delivered", kwargs={"pk": self.shipment.pk}),
            data={"delivery_time": "2025-05-17T12:00:00Z"}
        )
        self.assertEqual(response.status_code, 200)

        # Consume Kafka messages
        messages = consume_messages("shipment.status.updated", timeout=15)

        found_dispatched = False
        found_delivered = False

        for msg in messages:
            payload = json.loads(msg.value().decode("utf-8"))
            print("DEBUG Kafka:", payload)
            if payload["order_id"] != self.shipment.order_id:
                continue
            if payload["status"] == "dispatched":
                found_dispatched = True
            elif payload["status"] == "delivered":
                found_delivered = True

        self.assertTrue(found_dispatched, "Dispatched Kafka message not found")
        self.assertTrue(found_delivered, "Delivered Kafka message not found")
