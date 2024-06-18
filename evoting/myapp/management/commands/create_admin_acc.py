# myapp/management/commands/create_admin_acc.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapp.models import UserAccount, Profile

class Command(BaseCommand):
    help = 'Create initial admin account'

    def handle(self, *args, **kwargs):
        admin_profile = Profile.objects.get_or_create(profile_name='Admin')
        # Create admin account if not already present
        if not UserAccount.objects.filter(role__profile_name='Admin').exists():
            UserAccount.objects.create(
                username='admin1',
                full_name='John Doe',
                date_of_birth='1980-01-01',
                password=make_password('123'),  
                role=admin_profile[0]
            )
       
            
