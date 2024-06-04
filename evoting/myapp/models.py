from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver
from django.db.models.signals import post_delete

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class UserAccountManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)

class UserAccount(AbstractBaseUser):
    username = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    password = models.CharField(max_length=200)
    party = models.ForeignKey('Party', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True)
    # role = models.CharField(max_length=50, choices=[
    #     ('user', 'User'),
    #     ('candidate', 'Candidate'),
    #     ('admin', 'Admin'),
    # ])
    role = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True, blank=True)
    USERNAME_FIELD = 'username'  # Use username as the unique identifier
    REQUIRED_FIELDS = ['name', 'date_of_birth', 'password']

    objects = UserAccountManager()

    def __str__(self):
        return self.username


class Profile(models.Model):
    profile_name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.profile_name
    
class ElectionPhase(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Announcement(models.Model):
    header = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.header

class Party(models.Model):
    party = models.CharField(max_length=200)
    information = models.TextField()

    def __str__(self):
        return self.party

#-------------------Candidate--------------------------
class CandidateProfile(models.Model):
    user_account = models.OneToOneField('UserAccount', on_delete=models.CASCADE)
    election_poster = models.ImageField(upload_to='election_posters/', blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    candidate_statement = models.TextField(blank=True)

    def __str__(self):
        return self.user_account.user.username + "'s Candidate Profile"
    
@receiver(post_delete, sender=CandidateProfile)
def delete_candidateprofile_images(sender, instance, **kwargs):
    # Delete associated images if they exist
    if instance.election_poster:
        instance.election_poster.delete(save=False)
    if instance.profile_picture:
        instance.profile_picture.delete(save=False)