from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapp.models import TemporaryVoter, District

class Command(BaseCommand):
    help = 'Create a temporary voter'

    def handle(self, *args, **kwargs):
        district = District.objects.first()  # You can select any district
        if not district:
            self.stdout.write(self.style.ERROR('No district found. Please create a district first.'))
            return

        voter = TemporaryVoter.objects.create(
            username='temp_voter',
            name='Temporary Voter',
            date_of_birth='2000-01-01',
            password=make_password('temp_password'),
            district=district
        )
        self.stdout.write(self.style.SUCCESS(f'Temporary voter created with username: {voter.username} and password: temp_password'))
