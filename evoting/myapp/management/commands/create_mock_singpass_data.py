# myapp/management/commands/create_mock_singpass_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapp.models import SingpassUser

class Command(BaseCommand):
    help = 'Create initial singpass data'

    def handle(self, *args, **kwargs):
        # Create election phase if not already present
        if not SingpassUser.objects.filter(singpass_id='A1234567B').exists():
            hashed_password = make_password('123456')
            SingpassUser.objects.create(
                singpass_id='A1234567B',
                password=hashed_password,
                full_name='James Mary',
                date_of_birth='1980-01-01',
                phone_num='09876543',
                district='Clementi'
            )
        if not SingpassUser.objects.filter(singpass_id='A1234567C').exists():
            hashed_password = make_password('123456')
            SingpassUser.objects.create(
                singpass_id='A1234567C',
                password=hashed_password,
                full_name='James Parker',
                date_of_birth='1980-01-01',
                phone_num='09876543',
                district='Jurong East'
            )
            
