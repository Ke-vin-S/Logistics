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

    def test_dispatch_and_kafka_publish(self):
        # Schedule first
        url_schedule = reverse("shipment-mark-scheduled", kwargs={"pk": self.shipment.pk})
        self.client.post(url_schedule, data={"scheduled_time": "2025-05-17T10:00:00Z"})

        # Dispatch
        url_dispatch = reverse("shipment-mark-dispatched", kwargs={"pk": self.shipment.pk})
        response = self.client.post(url_dispatch, data={"dispatch_time": "2025-05-17T10:15:00Z"})

        self.assertEqual(response.status_code, 200)

        messages = consume_messages("shipment.status.updated")

        dispatched = [
            msg.value for msg in messages
            if msg.value["shipment_id"] == self.shipment.shipment_id and msg.value["status"] == "dispatched"
        ]

        self.assertTrue(dispatched, "Dispatched Kafka message not found.")

        self.assertEqual(dispatched[0]["order_id"], self.shipment.order_id)


    def test_delivered_and_kafka_publish(self):
            # Schedule → Dispatch → In Transit → Deliver
            self.client.post(reverse("shipment-mark-scheduled", kwargs={"pk": self.shipment.pk}))
            self.client.post(reverse("shipment-mark-dispatched", kwargs={"pk": self.shipment.pk}))
            self.client.post(reverse("shipment-mark-in-transit", kwargs={"pk": self.shipment.pk}))
            url = reverse("shipment-mark-delivered", kwargs={"pk": self.shipment.pk})
            response = self.client.post(url, data={"delivery_time": "2025-05-17T12:00:00Z"})

            self.assertEqual(response.status_code, 200)

            messages = consume_messages("shipment.status.updated")

            self.assertTrue(any(m.value["status"] == "dispatched" for m in messages), "No dispatched message found")
            self.assertTrue(any(m.value["status"] == "delivered" for m in messages), "No delivered message found")

