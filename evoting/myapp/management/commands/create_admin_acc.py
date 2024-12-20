# myapp/management/commands/create_admin_acc.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapp.models import UserAccount, Profile
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create initial admin account'

    def handle(self, *args, **kwargs):
        admin_profile = Profile.objects.get_or_create(profile_name='Admin')
        # Create admin account if not already present
        if not UserAccount.objects.filter(username='admin1').exists():
            UserAccount.objects.create(
                username='admin1',
                full_name='John Doe',
                date_of_birth='1980-01-01',
                password=make_password('Admin1Password$!'),  
                role=admin_profile[0]
            )
        if not UserAccount.objects.filter(username='admin2').exists():
            UserAccount.objects.create(
            username='admin2',
            full_name='Mary James',
            date_of_birth='1980-01-01',
            password=make_password('Admin2Password$!'),  
            role=admin_profile[0]
            )
        if not UserAccount.objects.filter(username='admin3').exists():
            UserAccount.objects.create(
            username='admin3',
            full_name='Chandler',
            date_of_birth='1980-01-01',
            password=make_password('Admin3Password$!'),  
            role=admin_profile[0]
            )

        
        logger.info('Admin account creation completed')
            
