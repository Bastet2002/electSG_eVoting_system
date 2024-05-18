from django.db import models

# Create your models here.
# models.py
from django.db import models

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class UserAccount(models.Model):
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    user_id = models.IntegerField(unique=True)
    password = models.CharField(max_length=200)
    # district = models.CharField(max_length=100, choices=[
    #     ('yio chu kang', 'Yio Chu Kang'),
    #     ('ang mo kio', 'Ang Mo Kio'),
    #     ('bishan', 'Bishan'),
    # ])
    district = models.ForeignKey('District', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('candidate', 'Candidate'),
        ('admin', 'Admin'),
    ])

    def __str__(self):
        return self.name


class ElectionPhase(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name
