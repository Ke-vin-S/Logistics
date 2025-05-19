import unittest
from decimal import Decimal
from unittest.mock import patch

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

    def test_filter_by_driver_assigned_true(self):
        self.vehicle1.driver_assigned = True
        self.vehicle1.save()

        response = self.client.get('/api/fleet/vehicles/?driver_assigned=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["vehicles"]), 1)
        self.assertEqual(response.data["vehicles"][0]["vehicle_id"], "TRK001")

    def test_filter_by_driver_assigned_false(self):
        self.vehicle1.driver_assigned = True
        self.vehicle1.save()
        self.vehicle2.driver_assigned = False
        self.vehicle2.save()
        self.vehicle3.driver_assigned = False
        self.vehicle3.save()

        response = self.client.get('/api/fleet/vehicles/?driver_assigned=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vehicle_ids = [v["vehicle_id"] for v in response.data["vehicles"]]
        self.assertIn("TRK002", vehicle_ids)
        self.assertIn("TRK003", vehicle_ids)
        self.assertNotIn("TRK001", vehicle_ids)

    @patch("fleet.views.vehicle.requests.post")
    def test_assign_driver_success(self, mock_post):
        """Test successful driver assignment and forwarding to auth service."""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "success": True,
            "message": "User created"
        }

        payload = {
            "username": "driver1",
            "email": "d1@gmail.com",
            "password": "Induwara@123",
            "first_name": "Test",
            "last_name": "Driver",
            "vehicle_id": "TRK001",
            "license_number": "1678v",
            "vehicle_type": "suzuki carry",
            "role_id": 6
        }

        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/driver_assigned/", payload, format="json")

        print(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["vehicle_id"], self.vehicle1.vehicle_id)
        self.assertTrue(response.data["driver_assigned"])

        self.vehicle1.refresh_from_db()
        self.assertTrue(self.vehicle1.driver_assigned)

        mock_post.assert_called_once()
        self.assertIn("/api/v1/register", mock_post.call_args[0][0])

    @unittest.skip("Temporarily skipping this test")
    @patch("fleet.views.vehicle.requests.post")
    def test_assign_driver_failure_from_auth(self, mock_post):
        """Test driver registration fails but doesn't update vehicle."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"error": "Email already exists"}

        payload = {
            "username": "driver1",
            "email": "d1@gmail.com",
            "password": "Induwara@123",
            "first_name": "Test",
            "last_name": "Driver",
            "vehicle_id": "TRK001",
            "license_number": "1678v",
            "vehicle_type": "suzuki carry",
            "role_id": 6
        }

        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/driver_assigned/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.vehicle1.refresh_from_db()
        self.assertFalse(self.vehicle1.driver_assigned)

    @patch("fleet.views.vehicle.requests.post")
    def test_assign_driver_auth_service_unreachable(self, mock_post):
        """Simulate network error while contacting user service."""
        from requests.exceptions import RequestException
        mock_post.side_effect = RequestException("Connection refused")

        payload = {
            "username": "driver1",
            "email": "d1@gmail.com",
            "password": "Induwara@123",
            "first_name": "Test",
            "last_name": "Driver",
            "vehicle_id": "TRK001",
            "license_number": "1678v",
            "vehicle_type": "suzuki carry",
            "role_id": 6
        }

        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/driver_assigned/", payload,
                                    format="json")
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.data)
        self.vehicle1.refresh_from_db()
        self.assertFalse(self.vehicle1.driver_assigned)

    def test_unassign_driver_success(self):
        """Test successful unassignment of a driver."""
        self.vehicle1.driver_assigned = True
        self.vehicle1.save()

        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/unassign_driver/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["vehicle_id"], "TRK001")
        self.assertFalse(response.data["driver_assigned"])

        self.vehicle1.refresh_from_db()
        self.assertFalse(self.vehicle1.driver_assigned)

    def test_unassign_driver_already_unassigned(self):
        """Test that unassigning an already unassigned vehicle works gracefully."""
        self.vehicle1.driver_assigned = False
        self.vehicle1.save()

        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle1.vehicle_id}/unassign_driver/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Driver already unassigned.")
        self.vehicle1.refresh_from_db()
        self.assertFalse(self.vehicle1.driver_assigned)
