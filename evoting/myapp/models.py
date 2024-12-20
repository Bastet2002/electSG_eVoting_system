from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.core.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
import json, os
from .media_storage import select_storage
from django.core.validators import FileExtensionValidator, validate_image_file_extension

# SINGPASS_USER Model
class SingpassUser(models.Model):
    singpass_id = models.CharField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    phone_num = models.CharField(max_length=20)
    district = models.CharField(max_length=20)
    salt = models.CharField(max_length=64, null=True)

# PROFILE Model
class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    profile_name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def clean(self):
        if self.profile_name:
            if len(self.profile_name) > 20:
                raise ValidationError({"profile_name": "Profile name cannot exceed 20 characters."})
            
            # Get all existing profile names, excluding the current instance
            existing_profiles = Profile.objects.exclude(pk=self.pk).values_list('profile_name', flat=True)
            # Check if the new profile name contains or is contained by any existing name
            for existing_name in existing_profiles:
                if ((existing_name.lower() in self.profile_name.lower() or self.profile_name.lower() in existing_name.lower())):
                    raise ValidationError({"profile_name": f"Profile name '{self.profile_name}' is too similar to existing profile '{existing_name}'."})
                
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.profile_name

# DISTRICT Model
class District(models.Model):
    district_id = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=255)
    num_of_people = models.IntegerField()

    def clean_district_name(self):
        if self.district_name:
            if len(self.district_name) > 30:
                raise ValidationError({"district_name": "District name cannot exceed 30 characters."})
            
            if District.objects.filter(district_name__iexact=self.district_name).exclude(pk=self.pk).exists():
                raise ValidationError({"district_name": f"District with this name '{self.district_name}' already exist."})
    
    def clean_num_of_people(self):
        if self.num_of_people:
            if self.num_of_people <= 0:
                raise ValidationError({"num_of_people": "Number of people cannot be zero or negative number."})
        
    def full_clean(self, *args, **kwargs):
        errors = {}
        try:
            super().full_clean(*args, **kwargs)
        except ValidationError as e:
            errors = e.error_dict

        for field in self._meta.fields:
            clean_method = getattr(self, f'clean_{field.name}', None)
            if clean_method:
                try:
                    clean_method()
                except ValidationError as e:
                    errors[field.name] = e.messages

        if errors:
            raise ValidationError(errors)
        
    def save(self, *args, **kwargs):
        self.full_clean()
        self.district_name = self.district_name.upper()
        super().save(*args, **kwargs)

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
    first_login = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'username'  # Use username as the unique identifier
    REQUIRED_FIELDS = ['full_name', 'date_of_birth', 'password', 'role']

    objects = UserAccountManager()

    def clean(self):
        super().clean()
        if self.date_of_birth and self.role and self.role.profile_name.lower() == 'candidate':
            if self.date_of_birth > date.today() - relativedelta(years=21):
                raise ValidationError({"date_of_birth": "Candidate must be at least 21 years old."})
            if not self.party:
                raise ValidationError({'party': 'Party is required for Candidates'})
            if not self.district:
                raise ValidationError({'district': 'District is required for Candidates'})

    def clean_username(self):
        if self.username:
            if len(self.username) > 25:
                raise ValidationError({"username": "Username cannot exceed 15 characters."})
            if UserAccount.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                raise ValidationError({"username": f"User account with this username '{self.username}' already exists."})

    def clean_password(self):
        if self.password:
            if (len(self.password) < 8 or 
            not any(char.isdigit() for char in self.password) or 
            not any(char.islower() for char in self.password) or 
            not any(char.isupper() for char in self.password) or 
            not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/~' for char in self.password)):
                raise ValidationError({"password": "Password must be at least 8 characters long and contain at least one number, one lowercase letter, one uppercase letter, and one special character."})
            
    def clean_role(self):
        if self.role is None:
            raise ValidationError({"role": "This field is required."})

    def full_clean(self, *args, **kwargs):
        errors = {}
        try:
            super().full_clean(*args, **kwargs)
        except ValidationError as e:
            errors = e.error_dict

        for field in self._meta.fields:
            clean_method = getattr(self, f'clean_{field.name}', None)
            if clean_method:
                try:
                    clean_method()
                except ValidationError as e:
                    errors[field.name] = e.messages

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

# CANDIDATE_PUBLIC_KEY Model
class CandidatePublicKey(models.Model):
    candidate = models.OneToOneField('UserAccount', on_delete=models.CASCADE, primary_key=True)
    pkv = models.CharField(max_length=64)
    pks = models.CharField(max_length=64)
    
# CANDIDATE_PROFILE Model
class CandidateProfile(models.Model):
    candidate = models.OneToOneField('UserAccount', on_delete=models.CASCADE, primary_key=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, storage=select_storage())
    election_poster = models.ImageField(upload_to='election_posters/', blank=True, null=True, storage=select_storage())
    candidate_statement = models.TextField(blank=True, null=True)

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
        # Check if this is an update (object already exists in DB)
        if self.pk:
            try:
            # Get the old instance from the database
                old_instance = CandidateProfile.objects.get(pk=self.pk)
            
                if old_instance.profile_picture and self.profile_picture and old_instance.profile_picture != self.profile_picture:
                    old_instance.profile_picture.delete(save=False)
                # Check if the election_poster field is updated
                if old_instance.election_poster and self.election_poster and old_instance.election_poster != self.election_poster:
                    old_instance.election_poster.delete(save=False)
            except CandidateProfile.DoesNotExist:
                pass

        self.full_clean()
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
        if self.total_vote:
            if self.total_vote < 0:
                raise ValidationError("Total vote cannot be negative.")
            if self.total_vote > 1000000:  # Example threshold for a very large vote count
                raise ValidationError("Total vote is unrealistically large.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# PARTY Model
class Party(models.Model):
    party_id = models.AutoField(primary_key=True)
    party_name = models.CharField(max_length=255)
    description = models.TextField()

    def clean(self):
        if self.party_name:
            if len(self.party_name) > 50:
                raise ValidationError({"party_name": "Party name cannot exceed 50 characters."})
            if Party.objects.filter(party_name=self.party_name).exclude(pk=self.pk).exists():
                raise ValidationError({"party_name": f"Party with this name '{self.party_name}' already exists."})
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
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

    def clean(self):
        if self.is_active:
            active_phases = ElectionPhase.objects.filter(is_active=True)
            if self.pk:
                active_phases = active_phases.exclude(pk=self.pk)
            if active_phases.exists():
                raise ValidationError('There can be only one active election phase.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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


# WebAuthn register
class WebauthnRegistration(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    challenge = models.CharField(max_length=9000, blank=True, null=True)

# WebAuthn credentials
class WebauthnCredentials(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="webauthn_credentials")
    credential_id = models.CharField(max_length=9000, blank=True, null=True)
    credential_public_key = models.CharField(max_length=9000, blank=True, null=True)
    current_sign_count = models.IntegerField(default=0)
    is_master = models.BooleanField(default=False)  # New to mark a master device

    def __str__(self):
        return f"WebAuthn Credential for {self.user.username}"