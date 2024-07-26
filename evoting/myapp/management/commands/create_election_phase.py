# myapp/management/commands/create_initial_data.py
from django.core.management.base import BaseCommand
from myapp.models import ElectionPhase

class Command(BaseCommand):
    help = 'Create initial election phase data'

    def handle(self, *args, **kwargs):
        # Create election phase if not already present
        if not ElectionPhase.objects.filter(phase_name='Campaigning Day').exists():
            ElectionPhase.objects.create(
                phase_name='Not Started',
                is_active=True
            )
        if not ElectionPhase.objects.filter(phase_name='Campaigning Day').exists():
            ElectionPhase.objects.create(
                phase_name='Campaigning Day',
                is_active=False
            )
        if not ElectionPhase.objects.filter(phase_name='Cooling Off Day').exists():
            ElectionPhase.objects.create(
                phase_name='Cooling Off Day',
                is_active=False
            )
        if not ElectionPhase.objects.filter(phase_name='Polling Day').exists():
            ElectionPhase.objects.create(
                phase_name='Polling Day',
                is_active=False
            )
        if not ElectionPhase.objects.filter(phase_name='End Election').exists():
            ElectionPhase.objects.create(
                phase_name='End Election',
                is_active=False
            )