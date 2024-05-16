from django.db import models

# Create your models here.
# models.py
from django.db import models

class UserAccount(models.Model):
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    user_id = models.IntegerField(unique=True)
    password = models.CharField(max_length=200)
    district = models.CharField(max_length=100, choices=[
        ('yio chu kang', 'Yio Chu Kang'),
        ('ang mo kio', 'Ang Mo Kio'),
        ('bishan', 'Bishan'),
    ])
    role = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('candidate', 'Candidate'),
        ('admin', 'Admin'),
    ])

    def __str__(self):
        return self.name
