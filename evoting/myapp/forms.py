from django import forms

roles = [
    ('user', 'User'),
    ('candidate', 'Candidate'),
    ('admin', 'Admin'),
]

election_districts = [
    ('yio chu kang', 'Yio Chu Kang'),
    ('ang mo kio', 'Ang Mo Kio'),
    ('bishan', 'Bishan'),
]

election_status = [
    ('polling day', 'Polling Day'),
    ('cool off day'), ('Cool Off Day'),
]

class createNewUser(forms.Form):
    name = forms.CharField(label="Name", max_length=200)
    date_of_birth = forms.DateField(label="Date of Birth")
    id = forms.IntegerField(label="ID")
    password = forms.CharField(label="Password", max_length=200, widget=forms.PasswordInput)
    district = forms.CharField(label="District", widget=forms.Select(choices=election_districts))
    role = forms.CharField(label="Role", widget=forms.Select(choices=roles))

class createProfile(forms.Form):
    profile_name = forms.CharField(label="Profile Name", max_length=200)
    description = forms.CharField(label="Description",widget=forms.Textarea())

class addDistrict(forms.Form):
    district_name = forms.CharField(label="District",widget=forms.Textarea())
    comments = forms.CharField(label="Comments", required=False)

class createAnnouncement(forms.Form):
    header = forms.CharField(label="Header", max_length=200)
    content = forms.CharField(label="Content", widget=forms.Textarea)