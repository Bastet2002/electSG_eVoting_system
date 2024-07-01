from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.core.exceptions import ValidationError
import json

# SINGPASS_USER Model
class SingpassUser(models.Model):
    singpass_id = models.CharField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    phone_num = models.CharField(max_length=20)
    district = models.CharField(max_length=20)

# PROFILE Model
class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    profile_name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.profile_name

# DISTRICT Model
class District(models.Model):
    district_id = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=255)

    def __str__(self):
        return self.district_name

class UserAccountManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)
    
# USERACCOUNT Model
class UserAccount(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    role = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True)
    party = models.ForeignKey('Party', on_delete=models.SET_NULL, null=True, blank=True)
    
    USERNAME_FIELD = 'username'  # Use username as the unique identifier
    REQUIRED_FIELDS = ['full_name', 'date_of_birth', 'password']

    objects = UserAccountManager()

    def __str__(self):
        return self.username

# CANDIDATE_PUBLIC_KEY Model
class CandidatePublicKey(models.Model):
    candidate = models.OneToOneField('UserAccount', on_delete=models.CASCADE, primary_key=True)
    pkv = models.CharField(max_length=64)
    pks = models.CharField(max_length=64)

# # Define the validation function
# def validate_file_size(file):
#     max_size_mb = 5  # Set maximum file size to 5 MB
#     if file.size > max_size_mb * 1024 * 1024:
#         raise ValidationError(f"File size should not exceed {max_size_mb} MB")
    
# CANDIDATE_PROFILE Model
class CandidateProfile(models.Model):
    candidate = models.OneToOneField('UserAccount', on_delete=models.CASCADE, primary_key=True)
    profile_picture = models.ImageField(upload_to='candidate_pictures/')
    election_poster = models.ImageField(upload_to='election_posters/')
    candidate_statement = models.TextField()

    def clean(self):
        max_size_mb = 5  # Set maximum file size to 5 MB

        # Validate profile_picture size
        if self.profile_picture:
            if self.profile_picture.size > max_size_mb * 1024 * 1024:
                raise ValidationError(f"Profile picture size should not exceed {max_size_mb} MB")

        # Validate election_poster size
        if self.election_poster:
            if self.election_poster.size > max_size_mb * 1024 * 1024:
                raise ValidationError(f"Election poster size should not exceed {max_size_mb} MB")
            
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.candidate_id.user.username + "'s Candidate Profile"
    
@receiver(post_delete, sender=CandidateProfile)
def delete_candidateprofile_images(sender, instance, **kwargs):
    # Delete associated images if they exist
    if instance.election_poster:
        instance.election_poster.delete(save=False)
    if instance.profile_picture:
        instance.profile_picture.delete(save=False)

# VOTE_RESULTS Model
class VoteResults(models.Model):
    candidate = models.OneToOneField('UserAccount', on_delete=models.CASCADE, primary_key=True)
    total_vote = models.IntegerField()

    def clean(self):
        if self.total_vote < 0:
            raise ValidationError("Total vote cannot be negative.")
        if self.total_vote > 1000000:  # Example threshold for a very large vote count
            raise ValidationError("Total vote is unrealistically large.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# PARTY Model
class Party(models.Model):
    party_id = models.AutoField(primary_key=True)
    party_name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.party_name

# ANNOUNCEMENT Model
class Announcement(models.Model):
    announcement_id = models.AutoField(primary_key=True)
    header = models.CharField(max_length=255)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.header

# ELECTION_PHASE Model
class ElectionPhase(models.Model):
    phase_id = models.AutoField(primary_key=True)
    phase_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.phase_name

# VOTE_RECORDS Model
class VoteRecords(models.Model):
    key_image = models.CharField(max_length=64, primary_key=True)
    district = models.ForeignKey('District', on_delete=models.CASCADE)
    transaction_record = models.JSONField()

    def save(self, *args, **kwargs):
        if isinstance(self.transaction_record, str):
            try:
                json.loads(self.transaction_record)
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON in transaction_record')
        super().save(*args, **kwargs)

# VOTING_CURRENCY Model
class VotingCurrency(models.Model):
    id = models.AutoField(primary_key=True)
    district = models.ForeignKey('District', on_delete=models.CASCADE)
    stealth_address = models.CharField(max_length=64, unique=True)
    commitment_record = models.JSONField()

# VOTER Model
class Voter(models.Model):
    voter_id = models.AutoField(primary_key=True)
    district = models.ForeignKey('District', on_delete=models.CASCADE)
    hash_from_info = models.CharField(max_length=128, unique=True, null=True)
    pkv = models.CharField(max_length=64)
    last_login = models.DateTimeField(null=True, blank=True)  # Add this field

    @property
    def is_authenticated(self):
        return True
