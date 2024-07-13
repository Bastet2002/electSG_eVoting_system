from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
from .models import UserAccount, District, Announcement, Party, Profile, CandidateProfile, ElectionPhase

class CreateNewUser(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = ['username', 'full_name', 'date_of_birth', 'password', 'role', 'party', 'district']
        widgets = {
            'password': forms.PasswordInput(),
            'date_of_birth': forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) > 15:
            raise ValidationError("Username cannot exceed 15 characters.")
        if UserAccount.objects.filter(username=username).exists():
            raise ValidationError("User account with this Username already exists.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.islower() for char in password) or not any(char.isupper() for char in password):
            raise ValidationError(f"Password must be at least 8 characters long. Contain at least one number, one lower and upper case.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        role = cleaned_data.get('role')
        if role and role.profile_name.lower() == 'candidate':
            if date_of_birth > date.today() - relativedelta(years=45):
                self.add_error('date_of_birth', "Candidate must be at least 45 years old.")
        return cleaned_data

class EditUser(forms.ModelForm):
    class Meta:
        model = UserAccount
        exclude = ['password', 'role', 'last_login']
        widgets = {
            'date_of_birth': forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_phase = ElectionPhase.objects.filter(is_active=True).first()
        if current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
            self.fields['district'].disabled = True
            self.fields['party'].disabled = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Check if the username is being updated and if it's already taken by another user
            if username and username != instance.username and UserAccount.objects.filter(username=username).exists():
                raise ValidationError("User account with this Username already exists.")
        if len(username) > 15:
            raise ValidationError("Username cannot exceed 15 characters.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        role = cleaned_data.get('role')
        print(role)
        if role and role.profile_name.lower() == 'candidate':
            if date_of_birth > date.today() - relativedelta(years=45):
                self.add_error('date_of_birth', "Candidate must be at least 45 years old.")
        return cleaned_data

class CreateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.profile_name in ['Candidate', 'Admin']:
            self.fields['profile_name'].disabled = True
            self.fields['description'].disabled = True

    def clean_profile_name(self):
        profile_name = self.cleaned_data.get('profile_name')
        forbidden_names = ['candidate', 'admin']
        if profile_name.lower() in forbidden_names:
            raise ValidationError("This profile name is not allowed or already exists.")
        if len(profile_name) > 20:
            raise ValidationError("Profile name cannot exceed 20 characters.")
        return profile_name

class CreateDistrict(forms.Form):
    district_names = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter district names separated by semicolons (;)'}),
    )

    def clean_district_names(self):
        district_names = self.cleaned_data.get('district_names')
        
        district_list = [name.strip() for name in district_names.split(';') if name.strip()]
        for name in district_list:
            if len(name) > 30:
                raise ValidationError(f"District name '{name}' exceeds 30 characters limit.")

        existing_districts = []
        for name in district_list:
            if District.objects.filter(district_name__iexact=name).exists():
                existing_districts.append(name)
        if existing_districts:
            raise ValidationError(f"District(s) already exist: {', '.join(existing_districts)}")
        
        return district_names

class EditDistrict(forms.ModelForm):
    class Meta:
        model = District
        fields = ['district_name']

    def clean_district_name(self):
        district_name = self.cleaned_data.get('district_name')

        if len(district_name) > 30:
            raise ValidationError("District name cannot exceed 30 characters.")

        if District.objects.filter(district_name__iexact=district_name).exists():
            raise ValidationError(f"District with this name already exist.")
        
        return district_name

class CreateAnnouncement(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['header', 'content']

class CreateParty(forms.ModelForm):
    class Meta:
        model = Party
        fields = ['party_name']

    def clean_party_name(self):
        party_name = self.cleaned_data.get('party_name')
        if len(party_name) > 50:
            raise ValidationError("Party name cannot exceed 50 characters.")
        if not self.instance.pk:
            if Party.objects.filter(party_name=party_name).exists():
                raise ValidationError("A party with this name already exists.")
        else:
            existing_party = Party.objects.filter(party_name=party_name).exclude(pk=self.instance.pk)
            if existing_party.exists():
                raise ValidationError("A party with this name already exists.")
        return party_name

class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if len(new_password) < 8:
            raise forms.ValidationError("Password must have more than 8 characters.")
        if not any(char.isdigit() for char in new_password):
            raise forms.ValidationError("Password must contain at least one number.")
        if not any(char.isupper() for char in new_password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in new_password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        if not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/~' for char in new_password):
            raise forms.ValidationError("Password must contain at least one special character.")
        if len(new_password) > 100:
            raise forms.ValidationError("Password must not exceed 100 characters.")
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Confirm password does not match new password.")

#--------------------------------Candidate Forms---------------------------------------- 
class ElectionPosterForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['election_poster']
        widgets = {
            'election_poster': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_election_poster(self):
        election_poster = self.cleaned_data.get('election_poster')
        max_size_mb = 5  # Set maximum file size to 5 MB

        # Validate election_poster size
        if election_poster.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"Election poster size should not exceed {max_size_mb} MB")
        return election_poster

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        max_size_mb = 5  # Set maximum file size to 5 MB

        # Validate profile_picture size
        if profile_picture.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"Profile picture size should not exceed {max_size_mb} MB")
        return profile_picture

class CandidateStatementForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['candidate_statement']
        widgets = {
            'candidate_statement': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            instance = kwargs.pop('instance')
            self.fields['candidate_statement'].initial = instance.candidate_statement
