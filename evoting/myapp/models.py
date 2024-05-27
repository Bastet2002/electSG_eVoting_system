from django.db import models

# Create your models here.
# models.py
from django.db import models

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class UserAccount(models.Model):
    username = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    password = models.CharField(max_length=200)
    party = models.ForeignKey('Party', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('candidate', 'Candidate'),
        ('admin', 'Admin'),
    ])

    def __str__(self):
        return self.username


class ElectionPhase(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Announcement(models.Model):
    header = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.header

class Party(models.Model):
    party = models.CharField(max_length=200)
    information = models.TextField()

    def __str__(self):
        return self.party
