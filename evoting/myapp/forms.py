from django import forms
from .models import UserAccount, District, Announcement, Party, Profile, ElectionPhase

class CreateNewUser(forms.ModelForm):  # Class names typically start with a capital letter
    class Meta:
        model = UserAccount
        fields = ['username', 'full_name', 'date_of_birth', 'password', 'role', 'party', 'district']
        widgets = {
            'password': forms.PasswordInput(),
            'date_of_birth': forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        }

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
        if current_phase and current_phase.name in ['Cooling Off Day', 'Polling Day']:
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
            raise forms.ValidationError("This profile name is not allowed or already exists.")
        return profile_name

class CreateDistrict(forms.Form):
    district_names = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter district names separated by semicolons (;)'}),
    )

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
        
#--------------------------------Candidate Forms---------------------------------------- 
from .models import CandidateProfile 
 
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