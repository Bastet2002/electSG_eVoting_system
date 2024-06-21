from django import forms
from django.core.exceptions import ValidationError
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
        if UserAccount.objects.filter(username=username).exists():
            raise ValidationError("User account with this Username already exists.")
        return username

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
        return profile_name

class CreateDistrict(forms.Form):
    district_names = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter district names separated by semicolons (;)'}),
    )

    def clean_district_names(self):
        district_names = self.cleaned_data.get('district_names')
        if not district_names:
            raise ValidationError("This field is required.")
        
        district_list = [name.strip() for name in district_names.split(';') if name.strip()]
        existing_districts = District.objects.filter(district_name__in=district_list).values_list('district_name', flat=True)
        if existing_districts:
            raise ValidationError(f"District(s) already exist: {', '.join(existing_districts)}")
        
        return district_names

class EditDistrict(forms.ModelForm):
    class Meta:
        model = District
        fields = ['district_name']

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
        if not self.instance.pk:
            if Party.objects.filter(party_name=party_name).exists():
                raise ValidationError("A party with this name already exists.")
        else:
            existing_party = Party.objects.filter(party_name=party_name).exclude(pk=self.instance.pk)
            if existing_party.exists():
                raise ValidationError("A party with this name already exists.")
        return party_name

#--------------------------------Candidate Forms---------------------------------------- 

class ElectionPosterForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['election_poster']
        widgets = {
            'election_poster': forms.FileInput(attrs={'accept': 'image/*'}),
        }

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
        }

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
