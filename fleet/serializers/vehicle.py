from rest_framework import serializers
from fleet.models import Vehicle, VehicleLocation


class VehicleSerializer(serializers.ModelSerializer):
    location_is_stale = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'vehicle_id',
            'model',
            'capacity',
            'status',
            'fuel_type',
            'plate_number',
            'year_of_manufacture',
            'depot_id',
            'depot_latitude',
            'depot_longitude',
            'current_latitude',
            'current_longitude',
            'last_location_update',
            'max_speed',
            'fuel_efficiency',
            'created_at',
            'updated_at',
            'is_available',
            'location_is_stale'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_location_update']


class LocationPointSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    location_name = serializers.CharField()
    timestamp = serializers.DateTimeField()


class VehicleLocationDetailSerializer(serializers.Serializer):
    plate_number = serializers.CharField()
    truck_id = serializers.CharField(source='vehicle_id')
    model = serializers.CharField()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        history_qs = VehicleLocation.objects.filter(vehicle=obj).order_by('-timestamp')
        current_location = None
        location_history = []

        for i, loc in enumerate(history_qs):
            loc_data = {
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'timestamp': loc.timestamp,
                'location_name': self.get_mock_location_name(loc.latitude, loc.longitude)
            }

            if i == 0:
                current_location = loc_data
            else:
                location_history.append(loc_data)

        return {
            "current_location": current_location,
            "location_history": location_history
        }

    def get_mock_location_name(self, lat, lon):
        # This should be replaced with a geocoding service if needed
        if lat > 6.926:
            return "Colombo Fort"
        elif lat > 6.923:
            return "Slave Island"
        elif lat > 6.921:
            return "Kollupitiya"
        else:
            return "Bambalapitiya"

# 🔹 Base serializer for all cases
class VehicleDetailSerializer(VehicleSerializer):
    location_detail = serializers.SerializerMethodField()

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ['location_detail']

    def get_location_detail(self, obj):
        return VehicleLocationDetailSerializer(obj).data

class VehicleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['vehicle_id', 'plate_number', 'model', 'status']
