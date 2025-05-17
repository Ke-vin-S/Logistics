from .vehicle import (
    VehicleSerializer,
    VehicleSummarySerializer,
    VehicleLocationDetailSerializer,
    LocationPointSerializer
)

from django.conf import settings

# Always import base detail serializer
from .vehicle import VehicleDetailSerializer as BaseVehicleDetailSerializer

# If extended mode is enabled, override VehicleDetailSerializer
if settings.ENABLE_FLEET_EXTENDED_MODELS:
    from .maintenance import (
        MaintenanceRecordSerializer,
        MaintenanceScheduleSerializer
    )
    from .fuel import FuelRecordSerializer
    from .trip import TripRecordSerializer
    from rest_framework import serializers

    class VehicleDetailSerializer(BaseVehicleDetailSerializer):
        maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)
        fuel_records = serializers.SerializerMethodField()
        trip_records = serializers.SerializerMethodField()

        class Meta(BaseVehicleDetailSerializer.Meta):
            fields = BaseVehicleDetailSerializer.Meta.fields + [
                'maintenance_records', 'fuel_records', 'trip_records'
            ]

        def get_fuel_records(self, obj):
            records = obj.fuel_records.all()[:5]
            return FuelRecordSerializer(records, many=True).data

        def get_trip_records(self, obj):
            records = obj.trip_records.all()[:5]
            return TripRecordSerializer(records, many=True).data
else:
    VehicleDetailSerializer = BaseVehicleDetailSerializer
