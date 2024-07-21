# myapp/management/commands/insert_singpass_users.py

from django.core.management.base import BaseCommand
from myapp.models import SingpassUser
from faker import Faker
from django.contrib.auth.hashers import make_password
import random
import string

class Command(BaseCommand):
    help = 'Insert mock data into SingpassUser model'

    def generate_singpass_id(self):
        start_letter = random.choice(string.ascii_uppercase)
        end_letter = random.choice(string.ascii_uppercase)
        middle_digits = ''.join(random.choices(string.digits, k=7))
        return f"{start_letter}{middle_digits}{end_letter}"
    
    #testing purpose
    def generate_strings(self, base='A1234567', count=26):
        result = []
        for letter in string.ascii_uppercase[:count]:
            result.append(f"{base}{letter}")
        return result

    def handle(self, *args, **kwargs):
        # Example usage
        fake = Faker()
        generated_strings = self.generate_strings()
        for id in generated_strings:
            SingpassUser.objects.create(
                singpass_id=id,
                password=make_password('123'),
                full_name=fake.name(),
                date_of_birth='1980-01-01',
                phone_num='09876543',
                district='Clementi'
            )
            
        fake = Faker()
        mock_data = []

        # List of specific districts
        districts = [
            'Ang Mo Kio', 'Bedok', 'Bishan', 'Bukit Merah', 'Bukit Timah', 'Central', 'Clementi', 'Geylang',
            'Kallang/Whampoa', 'Marine Parade', 'Pasir Ris', 'Queenstown', 'Serangoon', 'Bukit Batok', 
            'Bukit Panjang', 'Choa Chu Kang', 'Hougang', 'Jurong East', 'Jurong West', 'Punggol', 
            'Sembawang', 'Sengkang', 'Tengah', 'Woodlands', 'Yishun'
        ]

        # Generate 1000 mock SingpassUser records
        for _ in range(10):
            phone_num = fake.phone_number()
            # Ensure phone_num is at most 20 characters
            if len(phone_num) > 20:
                phone_num = phone_num[:20]

            mock_data.append(SingpassUser(
                singpass_id=self.generate_singpass_id(),
                password=make_password(fake.password(length=10)),
                full_name=fake.name(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=100),
                phone_num=phone_num,
                district=random.choice(districts)
            ))

        # SingpassUser.objects.bulk_create(mock_data)
        self.stdout.write(self.style.SUCCESS('Successfully inserted mock SingpassUser data'))

        
