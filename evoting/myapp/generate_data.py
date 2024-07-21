import csv
import random
from datetime import datetime, timedelta
from faker import Faker

def generate_user_csv(filename, num_users=10):
    fake = Faker()
    
    districts = ['Clementi', 'Jurong East']
    parties = ['PAP', 'DAP']
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['username', 'full_name', 'password', 'date_of_birth', 'role', 'district', 'party']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for _ in range(num_users):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}"
            
            writer.writerow({
                'username': username,
                'full_name': f"{first_name} {last_name}",
                'password': fake.password(length=12),
                'date_of_birth': fake.date_of_birth(minimum_age=45, maximum_age=80).strftime('%d/%m/%Y'),
                'role': 'Candidate',
                'district': random.choice(districts),
                'party': random.choice(parties)
            })

    print(f"CSV file '{filename}' has been generated with {num_users} user accounts.")

def generate_district_csv(filename):
    districts = [
            'Ang Mo Kio', 'Bedok', 'Bishan', 'Bukit Merah', 'Bukit Timah', 'Central', 'Clementi', 'Geylang',
            'Kallang/Whampoa', 'Marine Parade', 'Pasir Ris', 'Queenstown', 'Serangoon', 'Bukit Batok', 
            'Bukit Panjang', 'Choa Chu Kang', 'Hougang', 'Jurong East', 'Jurong West', 'Punggol', 
            'Sembawang', 'Sengkang', 'Tengah', 'Woodlands', 'Yishun'
        ]
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['district_name', 'num_of_people']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for district in districts:
            
            writer.writerow({
                'district_name': district,
                'num_of_people': 10
            })

    print(f"CSV file '{filename}' has been generated.")

# Usage
generate_user_csv('user_accounts.csv', num_users=20)
generate_district_csv('districts.csv')
