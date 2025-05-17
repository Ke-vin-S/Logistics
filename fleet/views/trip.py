import os
import django

from fleet.models import TripRecord, Vehicle
from fleet.serializers import TripRecordSerializer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_core.settings')
django.setup()
from django.db.models import QuerySet, Q, Sum, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta

class TripRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing trip records.
    """
    queryset = TripRecord.objects.all()
    serializer_class = TripRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vehicle']
    ordering_fields = ['start_time', 'created_at']
    ordering = ['-start_time']

    @action(detail=True, methods=['post'])
    def end_trip(self, request, pk=None):
        """
        End a trip by setting end time and odometer.
        POST /api/fleet/trips/{id}/end_trip/
        """
        trip = self.get_object()

        if trip.end_time:
            return Response(
                {'error': 'This trip has already ended'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract end trip data
        end_time = request.data.get('end_time')
        end_odometer = request.data.get('end_odometer')
        end_latitude = request.data.get('end_latitude')
        end_longitude = request.data.get('end_longitude')
        notes = request.data.get('notes')

        # Validate required fields
        if not end_time or not end_odometer:
            return Response(
                {'error': 'End time and end odometer are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Parse end_time if it's a string
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)

            end_odometer = int(end_odometer)

            # Ensure the end odometer is greater than the start odometer
            if end_odometer <= trip.start_odometer:
                return Response(
                    {'error': 'End odometer must be greater than start odometer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update trip record
            trip.end_time = end_time
            trip.end_odometer = end_odometer

            if end_latitude and end_longitude:
                trip.end_latitude = end_latitude
                trip.end_longitude = end_longitude

            if notes:
                if trip.notes:
                    trip.notes += f"\n\nEnd trip notes: {notes}"
                else:
                    trip.notes = notes

            trip.save()

            # If we have coordinates, update the vehicle location too
            if end_latitude and end_longitude:
                trip.vehicle.update_location(end_latitude, end_longitude)

            return Response(TripRecordSerializer(trip).data)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get trip statistics.
        GET /api/fleet/trips/stats/
        """
        # Filter parameters
        vehicle_id = request.query_params.get('vehicle_id')
        days = request.query_params.get('days', 30)

        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            start_date = timezone.now() - timedelta(days=days)

        # Base queryset
        queryset = TripRecord.objects.filter(
            start_time__gte=start_date,
            end_time__isnull=False  # Only include completed trips
        )

        if vehicle_id:
            queryset = queryset.filter(vehicle__vehicle_id=vehicle_id)

        # Calculate total distance and duration
        total_distance = 0
        total_duration = 0

        # We need to iterate through the records to use the properties
        for trip in queryset:
            if trip.distance:
                total_distance += trip.distance
            if trip.duration:
                total_duration += trip.duration

        # Count total trips
        total_trips = queryset.count()

        # Average trip length and duration
        avg_distance = total_distance / total_trips if total_trips > 0 else 0
        avg_duration = total_duration / total_trips if total_trips > 0 else 0

        # Vehicle-specific stats if not filtering for a specific vehicle
        vehicle_stats = []
        if not vehicle_id:
            vehicles = Vehicle.objects.filter(
                trip_records__start_time__gte=start_date,
                trip_records__end_time__isnull=False
            ).distinct()

            for vehicle in vehicles:
                vehicle_trips = queryset.filter(vehicle=vehicle)

                v_total_distance = 0
                v_total_duration = 0

                for trip in vehicle_trips:
                    if trip.distance:
                        v_total_distance += trip.distance
                    if trip.duration:
                        v_total_duration += trip.duration

                v_trip_count = vehicle_trips.count()

                vehicle_stats.append({
                    'vehicle_id': vehicle.vehicle_id,
                    'name': vehicle.model,
                    'trip_count': v_trip_count,
                    'total_distance': v_total_distance,
                    'total_duration': v_total_duration,
                    'avg_distance': v_total_distance / v_trip_count if v_trip_count > 0 else 0,
                    'avg_duration': v_total_duration / v_trip_count if v_trip_count > 0 else 0
                })

        return Response({
            'period_days': days,
            'total_trips': total_trips,
            'total_distance': total_distance,
            'total_duration': total_duration,
            'avg_distance': avg_distance,
            'avg_duration': avg_duration,
            'vehicle_stats': vehicle_stats
        })
