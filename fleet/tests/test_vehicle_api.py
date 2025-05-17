from decimal import Decimal

from rest_framework.test import APIClient
from django.test import TestCase
from rest_framework import status
from fleet.models import Vehicle, VehicleLocation


class VehicleAPITest(TestCase):
    """Integration tests for Vehicle API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.vehicle1 = Vehicle.objects.create(
            vehicle_id="TRK001", model="Truck 1", capacity=1000,
            status="available", fuel_type="diesel"
        )
        self.vehicle2 = Vehicle.objects.create(
            vehicle_id="TRK002", model="Truck 2", capacity=500,
            status="maintenance", fuel_type="petrol"
        )
        self.vehicle3 = Vehicle.objects.create(
            vehicle_id="TRK003", model="Truck 3", capacity=750,
            status="assigned", fuel_type="diesel"
        )

    def test_list_summary_fields(self):
        response = self.client.get('/api/fleet/vehicles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("vehicles", response.data)
        self.assertEqual(len(response.data["vehicles"]), 3)
        for item in response.data["vehicles"]:
            self.assertIn("vehicle_id", item)
            self.assertIn("model", item)
            self.assertIn("plate_number", item)
            self.assertIn("status", item)
            self.assertNotIn("capacity", item)

    def test_filter_by_status(self):
        response = self.client.get('/api/fleet/vehicles/', {'status': 'assigned'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["vehicles"]), 1)
        self.assertEqual(response.data["vehicles"][0]['vehicle_id'], "TRK003")

    def test_filter_by_min_capacity(self):
        response = self.client.get('/api/fleet/vehicles/', {'min_capacity': 800})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["vehicles"]), 1)
        self.assertEqual(response.data["vehicles"][0]['vehicle_id'], "TRK001")

    def test_filter_by_fuel_type(self):
        response = self.client.get('/api/fleet/vehicles/', {'fuel_type': 'diesel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vehicle_ids = [v['vehicle_id'] for v in response.data["vehicles"]]
        self.assertIn("TRK001", vehicle_ids)
        self.assertIn("TRK003", vehicle_ids)

    def test_create_vehicle_successfully(self):
        """POST /api/fleet/vehicles/ should create a new vehicle."""
        payload = {
            "vehicle_id": "TRK004",
            "model": "Truck 4",
            "capacity": 1200,
            "status": "available",
            "fuel_type": "electric",
            "plate_number": "XYZ789"
        }
        response = self.client.post('/api/fleet/vehicles/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["vehicle_id"], "TRK004")
        self.assertEqual(response.data["fuel_type"], "electric")

    def test_patch_update_vehicle_status(self):
        """PATCH /api/fleet/vehicles/{id}/ should update vehicle status."""
        response = self.client.patch(
            f'/api/fleet/vehicles/{self.vehicle1.vehicle_id}/',
            {"status": "maintenance"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "maintenance")

    def test_update_vehicle_location(self):
        """POST /api/fleet/vehicles/{id}/update_location/ should update location and create history."""
        payload = {
            "latitude": 42.123456,
            "longitude": -71.654321,
            "speed": 65.5
        }
        response = self.client.post(
            f'/api/fleet/vehicles/{self.vehicle1.vehicle_id}/update_location/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle1.refresh_from_db()
        self.assertAlmostEqual(float(self.vehicle1.current_latitude), 42.123456)
        self.assertAlmostEqual(float(self.vehicle1.current_longitude), -71.654321)

        # Verify historical tracking
        history = VehicleLocation.objects.filter(vehicle=self.vehicle1)
        self.assertEqual(history.count(), 1)
        self.assertAlmostEqual(float(history[0].speed), 65.5)
        self.assertAlmostEqual(float(history[0].latitude), 42.123456)

    def test_invalid_status_filter(self):
        response = self.client.get('/api/fleet/vehicles/', {'status': 'nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ordering_by_updated_at(self):
        """Test that vehicles can be ordered by updated_at even if it's not returned."""
        response = self.client.get("/api/fleet/vehicles/?ordering=-updated_at")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("vehicles", response.data)
        self.assertTrue(len(response.data["vehicles"]) >= 1)
        self.assertIn("vehicle_id", response.data["vehicles"][0])  # Confirm summary structure

    def test_mark_vehicle_available(self):
        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle3.vehicle_id}/mark_available/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle3.refresh_from_db()
        self.assertEqual(self.vehicle3.status, 'available')

    def test_mark_vehicle_assigned(self):
        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/mark_assigned/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.status, 'assigned')

    def test_change_status_to_available(self):
        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle2.vehicle_id}/change_status/", {
            "status": "available"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle2.refresh_from_db()
        self.assertEqual(self.vehicle2.status, "available")

    def test_change_status_invalid(self):
        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/change_status/", {
            "status": "nonexistent"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_location_overview_success(self):
        # Create location history for vehicle1
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9271, longitude=79.8612)
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9250, longitude=79.8600)
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9225, longitude=79.8590)

        response = self.client.get(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/location_overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["truck_id"], "TRK001")
        self.assertIn("status", data)
        self.assertIn("current_location", data["status"])
        self.assertIn("location_history", data["status"])

        self.assertEqual(len(data["status"]["location_history"]), 2)
        self.assertEqual(data["status"]["current_location"]["latitude"], Decimal('6.922500'))

    def test_location_overview_empty_history(self):
        response = self.client.get(f"/api/fleet/vehicles/{self.vehicle2.vehicle_id}/location_overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.data["status"]["current_location"])
        self.assertEqual(response.data["status"]["location_history"], [])

    def test_location_overview_history_ordering(self):
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9200, longitude=79.8580)
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9250, longitude=79.8600)
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9271, longitude=79.8612)

        response = self.client.get(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/location_overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        locs = response.data["status"]["location_history"]
        self.assertGreaterEqual(locs[0]["timestamp"], locs[-1]["timestamp"])

    def test_location_overview_has_mock_location_names(self):
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9271, longitude=79.8612)
        VehicleLocation.objects.create(vehicle=self.vehicle1, latitude=6.9225, longitude=79.8590)

        response = self.client.get(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/location_overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        current = response.data["status"]["current_location"]
        history = response.data["status"]["location_history"]

        self.assertIn("location_name", current)
        self.assertIn("location_name", history[0])
        self.assertTrue(current["location_name"])  # mock name string
