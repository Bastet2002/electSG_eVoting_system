from django import forms
from .models import UserAccount, District
    
roles = [
    ('user', 'User'),
    ('candidate', 'Candidate'),
    ('admin', 'Admin'),
]

# election_districts = [
#     ('yio chu kang', 'Yio Chu Kang'),
#     ('ang mo kio', 'Ang Mo Kio'),
#     ('bishan', 'Bishan'),
# ]

election_status = [
    ('polling day', 'Polling Day'),
    ('cool off day'), ('Cool Off Day'),
]

class createNewUser(forms.ModelForm):  # Class names typically start with a capital letter
    class Meta:
        model = UserAccount
        fields = ['name', 'date_of_birth', 'user_id', 'password', 'district', 'role']
        widgets = {
            'password': forms.PasswordInput(),
        }


class createProfile(forms.Form):
    profile_name = forms.CharField(label="Profile Name", max_length=200)
    description = forms.CharField(label="Description",widget=forms.Textarea())

class addDistrict(forms.Form):
    district_names = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter district names separated by semicolons (;)'}),
        #help_text="Enter multiple district names separated by semicolons (;)"
    )

class editDistrict(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name']


class createAnnouncement(forms.Form):
    header = forms.CharField(label="Header", max_length=200)
    content = forms.CharField(label="Content", widget=forms.Textarea)