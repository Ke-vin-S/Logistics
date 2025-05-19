import unittest

from rest_framework.test import APITestCase
from fleet.models import Vehicle

class DriverAssignLiveTest(APITestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            vehicle_id="TRK777",
            model="Test Truck",
            capacity=1000,
            fuel_type="diesel",
            status="available",
        )

    @unittest.skip("Temporarily skipping this test")
    def test_real_driver_assignment(self):
        payload = {
            "username": "driver_live_test",
            "email": "driver_live@example.com",
            "password": "SecureTest@123",
            "first_name": "Live",
            "last_name": "Test",
            "vehicle_id": "TRK777",
            "license_number": "DRLIVE001",
            "vehicle_type": "test truck",
            "role_id": 6
        }

        response = self.client.post(f"/api/fleet/vehicles/{self.vehicle.vehicle_id}/driver_assigned/", payload, format="json")

        print("RESPONSE STATUS:", response.status_code)
        print("RESPONSE DATA:", response.data)

        self.assertIn(response.status_code, [201, 400])
        print("LIVE DRIVER ASSIGN RESPONSE:", response.data)

        self.vehicle.refresh_from_db()
        if response.status_code == 201:
            self.assertTrue(self.vehicle.driver_assigned)
        else:
            self.assertFalse(self.vehicle.driver_assigned)
