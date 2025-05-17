import os
import django

from fleet.models import FuelRecord, Vehicle
from fleet.serializers import FuelRecordSerializer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_core.settings')
django.setup()
from django.db.models import QuerySet, Q, Sum, Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta


class FuelRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing fuel records.
    """
    queryset = FuelRecord.objects.all()
    serializer_class = FuelRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vehicle']
    ordering_fields = ['refuel_date', 'created_at']
    ordering = ['-refuel_date']

    @action(detail=False, methods=['get'])
    def consumption_stats(self, request):
        """
        Get fuel consumption statistics.
        GET /api/fleet/fuel/consumption_stats/
        """
        # Filter for specific vehicle if requested
        vehicle_id = request.query_params.get('vehicle_id')
        days = request.query_params.get('days', 30)

        try:
            days = int(days)
            start_date = timezone.now() - timedelta(days=days)
        except ValueError:
            days = 30
            start_date = timezone.now() - timedelta(days=days)

        queryset = FuelRecord.objects.filter(refuel_date__gte=start_date)

        if vehicle_id:
            queryset = queryset.filter(vehicle__vehicle_id=vehicle_id)

        # Calculate total cost and amount for the period
        totals = queryset.aggregate(
            total_cost=Sum('cost'),
            total_amount=Sum('amount')
        )

        # Get stats by vehicle
        vehicle_stats = []
        if not vehicle_id:
            # Group by vehicle and aggregate
            vehicles = Vehicle.objects.filter(
                fuel_records__refuel_date__gte=start_date
            ).distinct()

            for vehicle in vehicles:
                vehicle_records = queryset.filter(vehicle=vehicle)

                vehicle_totals = vehicle_records.aggregate(
                    total_cost=Sum('cost'),
                    total_amount=Sum('amount'),
                    count=Count('id')
                )

                vehicle_stats.append({
                    'vehicle_id': vehicle.vehicle_id,
                    'name': vehicle.model,
                    'records_count': vehicle_totals['count'],
                    'total_cost': vehicle_totals['total_cost'],
                    'total_amount': vehicle_totals['total_amount']
                })

        return Response({
            'period_days': days,
            'total_cost': totals['total_cost'] or 0,
            'total_amount': totals['total_amount'] or 0,
            'vehicle_stats': vehicle_stats
        })
