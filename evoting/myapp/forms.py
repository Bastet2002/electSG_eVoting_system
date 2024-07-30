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
    
    def __init__(self, *args, **kwargs):
        super(CreateNewUser, self).__init__(*args, **kwargs)
        self.fields['role'].required = True

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()

class EditUser(forms.ModelForm):
    class Meta:
        model = UserAccount
        exclude = ['password', 'role', 'last_login', 'first_login']
        widgets = {
            'date_of_birth': forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        current_phase = ElectionPhase.objects.filter(is_active=True).first()
        if user and user.role.profile_name == 'Admin':
            del self.fields['district']
            del self.fields['party']
        elif current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day', 'End Election']:
            self.fields['district'].disabled = True
            self.fields['party'].disabled = True

class CreateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'custom-description'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.profile_name in ['Candidate', 'Admin']:
            self.fields['profile_name'].disabled = True
            self.fields['description'].disabled = True

class CreateDistrict(forms.ModelForm):
    class Meta:
        model = District
        fields = ['district_name', 'num_of_people']

class EditDistrict(forms.ModelForm):
    class Meta:
        model = District
        fields = ['district_name']
        widgets = {
            'district_name': forms.Textarea(attrs={'class': 'custom-content'})
        }

class CreateAnnouncement(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['header', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'custom-content'})
        }

class CreateParty(forms.ModelForm):
    class Meta:
        model = Party
        fields = ['party_name', 'description']

class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'changepassword-text-field'}), label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'changepassword-text-field'}), label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'changepassword-text-field'}), label="Confirm New Password")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password

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

        return cleaned_data

class FirstLoginPasswordChangeForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'changepassword-text-field'}), label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'changepassword-text-field'}), label="Confirm New Password")

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password:
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
        if cleaned_data is None:
            return {}
        
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Confirm password does not match new password.")

        return cleaned_data

#--------------------------------Candidate Forms---------------------------------------- 
class ElectionPosterForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['election_poster']
        widgets = {
            'election_poster': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['election_poster'].required = True

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].required = True

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
        self.fields['candidate_statement'].required = True
