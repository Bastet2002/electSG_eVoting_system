from django import forms
from .models import UserAccount, District, Announcement, Party, Profile
    
roles = [
    ('user', 'User'),
    ('candidate', 'Candidate'),
    ('admin', 'Admin'),
]

election_status = [
    ('polling day', 'Polling Day'),
    ('cool off day'), ('Cool Off Day'),
]

class createNewUser(forms.ModelForm):  # Class names typically start with a capital letter
    class Meta:
        model = UserAccount
        fields = ['username', 'name', 'date_of_birth', 'password', 'party', 'district', 'role']
        widgets = {
            'password': forms.PasswordInput(),
        }

class editUser(forms.ModelForm):
    class Meta:
        model = UserAccount
        exclude = ['password']
        
class CreateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_name', 'description']

class createDistrict(forms.Form):
    district_names = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter district names separated by semicolons (;)'}),
    )

class editDistrict(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name']


class createAnnouncement(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['header', 'content']


class createParty(forms.ModelForm):
    class Meta:
        model = Party
        fields = ['party']
        
        
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