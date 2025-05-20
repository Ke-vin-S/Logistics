from django.core.management.base import BaseCommand
from assignment.services.assignment_planner import AssignmentPlanner
from fleet.models import Vehicle
from shipments.models import Shipment

class Command(BaseCommand):
    help = 'Triggers assignment planning'

    def handle(self, *args, **kwargs):
        vehicles = Vehicle.objects.filter(status='available', driver_assigned=True)
        shipments = Shipment.objects.filter(status='pending')
        planner = AssignmentPlanner(vehicles, shipments)
        planner.plan_assignments()
