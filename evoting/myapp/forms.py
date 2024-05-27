from django import forms
from .models import UserAccount, District, Announcement, Party
    
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

class createProfile(forms.Form):
    profile_name = forms.CharField(label="Profile Name", max_length=200)
    description = forms.CharField(label="Description",widget=forms.Textarea())

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
        fields = ['party', 'information']