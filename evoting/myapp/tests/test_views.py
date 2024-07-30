from django.test import TestCase, Client
from unittest.mock import patch, MagicMock, call
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
from pygrpc import ringct_pb2
from ..models import (
    SingpassUser,
    Profile,
    District,
    UserAccount,
    CandidatePublicKey,
    CandidateProfile,
    VoteResults,
    Party,
    Announcement,
    ElectionPhase,
    VoteRecords,
    VotingCurrency,
    Voter,
)
from pygrpc.ringct_client import GrpcError
from myapp.forms import CreateNewUser, CSVUploadForm

User = get_user_model()

class UserAccountViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.candidate_profile = Profile.objects.create(profile_name="Candidate", description="Candidate Profile")
        self.district = District.objects.create(district_name="Test District", num_of_people=10)
        self.party = Party.objects.create(party_name="Test Party", description="Testing 123")
        self.user = self.create_test_user()

        # Check if "Campaigning Day" phase exists and set it to active
        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if self.election_phase:
            self.election_phase.is_active = True
            self.election_phase.save()
        else:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

    def tearDown(self):
        self.user.delete()
        self.admin_profile.delete()
        self.candidate_profile.delete()
        self.district.delete()

    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1999-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_user_login_view(self):
        login_successful = self.client.login(username='testuser1', password='password')
        self.assertTrue(login_successful)

    def test_create_account_view_get(self): # used to render the form for the user
        self.client.login(username='testuser1', password='password')

        response = self.secure_get(reverse('create_account'))
        self.assertEqual(response.status_code, 200) #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/createUserAcc.html')

    @patch('myapp.views.grpc_generate_candidate_keys_run')
    def test_create_account_view_post_candidate(self, mock_grpc):
        self.client.login(username='testuser1', password='password')
        # Create a mock response
        mock_response = MagicMock()
        mock_grpc.return_value = mock_response

        form_data = {
            'username': 'testcandidate',
            'password': 'Password123!',
            'full_name': 'Test Candidate',
            'date_of_birth': '1960-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id,
            'party': self.party.party_id
        } 
        response = self.secure_post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertTrue(User.objects.filter(username='testcandidate').exists())
        
        created_user = User.objects.get(username='testcandidate')
        self.assertTrue(CandidateProfile.objects.filter(candidate=created_user).exists())
        
        # Assert that the gRPC function was called
        mock_grpc.assert_called_once_with(candidate_id=created_user.user_id)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Account successfully created.', [str(m) for m in messages])

    @patch('myapp.views.grpc_generate_candidate_keys_run')
    def test_create_account_view_post_candidate_grpc_error(self, mock_grpc):
        self.client.login(username='testuser1', password='password')
        # Simulate a gRPC error
        mock_grpc.side_effect = GrpcError("Test Mock gRPC error in create account")

        form_data = {
            'username': 'testcandidate2',
            'password': 'Password123!',
            'full_name': 'Test Candidate',
            'date_of_birth': '1960-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id,
            'party': self.party.party_id
        } 
        response = self.secure_post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Still expecting a redirect
        self.assertTrue(User.objects.filter(username='testcandidate2').exists())
        
        created_user = User.objects.get(username='testcandidate2')
        self.assertTrue(CandidateProfile.objects.filter(candidate=created_user).exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Error in creating candidate keys: Test Mock gRPC error in create account', [str(m) for m in messages])

    def test_create_account_view_post_non_candidate(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'username': 'testuser',
            'password': 'Password123!',
            'full_name': 'Test User',
            'date_of_birth': '1999-01-01',
            'role': self.admin_profile.profile_id
        }
        response = self.secure_post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        created_user = User.objects.get(username='testuser')
        self.assertFalse(CandidateProfile.objects.filter(candidate=created_user).exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Account successfully created.', [str(m) for m in messages])

    def test_create_account_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {}
        response = self.secure_post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 200)

        user_form = response.context['form']
        
        expected_errors = [
            ('username', 'This field is required.'),
            ('full_name', 'This field is required.'),
            ('date_of_birth', 'This field is required.'),
            ('password', 'This field is required.'),
            ('role', 'This field is required.')
        ]
        for field, error_msg in expected_errors:
            self.assertIn(error_msg, user_form.errors[field])

    def test_create_account_view_post_existing(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'username': 'testuser1',  #duplicate username
            'password': 'Password123!',
            'full_name': 'Test user 2',
            'date_of_birth': '1960-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id,
            'party': self.party.party_id
        }
        response = self.secure_post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        user_form = response.context['form']
        self.assertIn("User account with this username 'testuser1' already exists.", user_form.errors['username'])

    def test_create_account_view_post_invalid_date(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'username': 'testuser3',
            'password': 'password',
            'full_name': 'Test user 3',
            'date_of_birth': 'invalid-date',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id,\
            'party': self.party.party_id
        }
        response = self.secure_post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        user_form = response.context['form']
        self.assertIn('Enter a valid date.', user_form.errors['date_of_birth'])

    def test_create_account_view_post_long_username(self):
        self.client.login(username='testuser1', password='password')
        long_username = 'a' * 201  #Max length 200
        form_data = {
            'username': long_username,
            'password': 'password',
            'full_name': 'Test user 6',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id,
            'party': self.party.party_id
        }
        response = self.secure_post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        user_form = response.context['form']
        self.assertIn('Ensure this value has at most 200 characters (it has 201).', user_form.errors['username'])

    def test_edit_account_view_get(self): # used to render the form for the user
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('edit_account', args=[self.user.user_id]))
        self.assertEqual(response.status_code, 200) #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/updateUserAcc.html')

    def test_edit_account_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'username': self.user.username,
            'full_name': 'Test user updated',
            'date_of_birth': self.user.date_of_birth,
        }
        response = self.secure_post(reverse('edit_account', args=[self.user.user_id]), data=form_data)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302) #HTTP_302_FOUND
        self.assertEqual(self.user.full_name, 'Test user updated')

    def test_edit_account_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {}
        response = self.secure_post(reverse('edit_account', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

    def test_edit_account_view_post_invalid_date(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'username': 'testuser2',
            'full_name': 'Test user updated',
            'date_of_birth': 'invalid-date'
        }
        response = self.secure_post(reverse('edit_account', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        user_form = response.context['form']
        self.assertIn('Enter a valid date.', user_form.errors['date_of_birth'])

    def test_edit_account_view_post_long_username(self):
        self.client.login(username='testuser1', password='password')
        long_username = 'a' * 201  #Max length 200
        form_data = {
            'username': long_username,
            'full_name': 'Test user 65',
            'date_of_birth': '1999-01-01'
        }
        response = self.secure_post(reverse('edit_account', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        user_form = response.context['form']
        self.assertIn('Ensure this value has at most 200 characters (it has 201).', user_form.errors['username'])

    def test_delete_account_view_post(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_post(reverse('delete_account', args=[self.user.user_id]))
        self.assertEqual(response.status_code, 302) #HTTP_302_FOUND
        self.assertFalse(User.objects.filter(user_id=self.user.user_id).exists())

    def test_view_accounts_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_accounts'))
        self.assertEqual(response.status_code, 200)  #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/viewUserAcc.html')

class DistrictViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(district_name="Test District 1", num_of_people=5)
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.user = self.create_test_user()

        # Check if "Campaigning Day" phase exists and set it to active
        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if self.election_phase:
            self.election_phase.is_active = True
            self.election_phase.save()
        else:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

    def tearDown(self):
        self.district.delete()
        self.election_phase.delete()
        self.admin_profile.delete()
        self.user.delete()
    
    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1960-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_create_district_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('create_district'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/createDistrict.html')

    def test_create_district_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'district_name': '',
            'num_of_people': ''
        }
        response = self.secure_post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        district_form = response.context['form']
        self.assertIn('This field is required.', district_form.errors['district_name'])

    @patch('myapp.views.grpc_generate_user_and_votingcurr_run')
    def test_create_district_view_post_one(self, mock_grpc):
        self.client.login(username='testuser1', password='password')
        mock_response = ringct_pb2.Gen_VoterCurr_Response()
        mock_grpc.return_value = mock_response # a single mock response is created and set as the return value.
        
        form_data = {
            'district_name': 'Test District',
            'num_of_people': 5
        }
        response = self.secure_post(reverse('create_district'), data=form_data)

        self.assertEqual(response.status_code, 302)

        created_district = District.objects.get(district_name='Test District'.upper())
        self.assertTrue(created_district)

        mock_grpc.assert_called_once_with(district_id=created_district.district_id, voter_num=5) # uses the voter_num in create_district view
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('District successfully created.', [str(m) for m in messages]) # check if the success message went thru

    def test_create_district_view_post_existing(self):
        self.client.login(username='testuser1', password='password')
        District.objects.create(district_name='Test District', num_of_people=5)
        form_data = {
            'district_name': 'Test District',
            'num_of_people': 5
        }
        response = self.secure_post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        district_form = response.context['form']
        self.assertIn("District with this name 'Test District' already exist.", district_form.errors['district_name'])

    def test_create_district_view_post_long_name(self):
        self.client.login(username='testuser1', password='password')
        long_name = 'a' * 200
        form_data = {
            'district_name': long_name,
            'num_of_people': 5
        }
        response = self.secure_post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        district_form = response.context['form']
        self.assertIn("District name cannot exceed 30 characters.", district_form.errors['district_name'])

    @patch('myapp.views.grpc_generate_user_and_votingcurr_run')
    def test_create_district_view_post_grpc_error(self, mock_grpc):
        self.client.login(username='testuser1', password='password')
        mock_grpc.side_effect = GrpcError("Test Mock gRPC error in create district")
        form_data = {
            'district_name': 'Error District',
            'num_of_people': 5
        }
        response = self.secure_post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Error District'.upper()).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Error in gRPC call: Test Mock gRPC error in create district', [str(m) for m in messages])

    def test_view_district_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_districts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/viewDistrict.html')
        self.assertContains(response, self.district.district_name)

    def test_view_district_search_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_districts'), params={'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.district.district_name)

    def test_edit_district_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('edit_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/editDistrict.html')

    def test_edit_district_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'district_name': 'Test District Updated'
        }
        response = self.secure_post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.district.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.district.district_name, 'Test District Updated'.upper())

    def test_edit_district_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'district_name': ''
        }
        response = self.secure_post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        district_form = response.context['form']
        self.assertIn("This field is required.", district_form.errors['district_name'])
    
    def test_edit_district_view_post_long_name(self):
        self.client.login(username='testuser1', password='password')
        long_name = 'a' * 50
        form_data = {
            'district_name': long_name
        }
        response = self.secure_post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        district_form = response.context['form']
        self.assertIn("District name cannot exceed 30 characters.", district_form.errors['district_name'])

    def test_delete_district_view_post_successfull(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_post(reverse('delete_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(District.objects.filter(district_id=self.district.district_id).exists())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'District successfully deleted.')

class ProfileViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.user = self.create_test_user()

        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if not self.election_phase:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

    def tearDown(self):
        self.election_phase.delete()
        self.admin_profile.delete()
        self.user.delete()

    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1960-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_create_profile_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('create_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/createProfile.html')

    def test_create_profile_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'profile_name': 'Test Profile',
            'description': 'Test description'
        }
        response = self.secure_post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Profile.objects.filter(profile_name='Test Profile').exists())

    def test_create_profile_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'profile_name': '',
            'description': 'Test description'
        }
        response = self.secure_post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 200)
        profile_form = response.context['form']
        self.assertIn("This field is required.", profile_form.errors['profile_name'])

    def test_create_profile_view_post_existing(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'profile_name': 'Admin',
            'description': 'Duplicate profile name'
        }
        response = self.secure_post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 200)
        profile_form = response.context['form']
        self.assertIn("Profile name 'Admin' is too similar to existing profile 'Admin'.", profile_form.errors['profile_name'])

    def test_create_profile_view_post_long_name(self):
        self.client.login(username='testuser1', password='password')
        long_name = 'a' * 200
        form_data = {
            'profile_name': long_name,
            'description': 'Test description'
        }
        response = self.secure_post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 200)
        profile_form = response.context['form']
        self.assertIn('Profile name cannot exceed 20 characters.', profile_form.errors['profile_name'])

    def test_view_profiles_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_profiles'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/viewProfiles.html')
        self.assertContains(response, self.admin_profile.profile_name)

    def test_edit_profile_view_get(self):
        self.client.login(username='testuser1', password='password')
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        response = self.secure_get(reverse('edit_profile', args=[profile.profile_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/editProfile.html')

    def test_edit_profile_view_post(self):
        self.client.login(username='testuser1', password='password')
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        form_data = {
            'profile_name': 'Test Profile updated',
            'description': 'Test description updated'
        }
        response = self.secure_post(reverse('edit_profile', args=[profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 302)

        updated_profile = Profile.objects.get(profile_name='Test Profile updated')
        self.assertEqual(updated_profile.profile_name, 'Test Profile updated')
        self.assertEqual(updated_profile.description, 'Test description updated')

    def test_edit_profile_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        form_data = {
            'profile_name': '',
            'description': 'Test description'
        }
        response = self.secure_post(reverse('edit_profile', args=[profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        profile_form = response.context['form']
        self.assertIn('This field is required.', profile_form.errors['profile_name'])

    def test_edit_profile_view_post_long_name(self):
        self.client.login(username='testuser1', password='password')
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        long_name = 'a' * 30
        form_data = {
            'profile_name': long_name,
            'description': 'Test description'
        }
        response = self.secure_post(reverse('edit_profile', args=[profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        profile_form = response.context['form']
        self.assertIn('Profile name cannot exceed 20 characters.', profile_form.errors['profile_name'])

    def test_delete_profile_view_post_successfull(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_post(reverse('delete_profile', args=[self.admin_profile.profile_id]))
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Profile.objects.filter(profile_id=self.admin_profile.profile_id).exists())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile successfully deleted.')

class AnnouncementViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.user = self.create_test_user()
        self.announcement = Announcement.objects.create(
            header="Test Announcement",
            content="Test content"
        )

    def tearDown(self):
        self.announcement.delete()

    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1960-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_create_announcement_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('create_announcement'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/createAnnouncement.html')

    def test_create_announcement_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'header': 'Test Announcement',
            'content': 'Test content'
        }
        response = self.secure_post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(header='Test Announcement').exists())

    def test_create_announcement_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'header': '',
            'content': 'Content with empty header'
        }
        response = self.secure_post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        announcement_form = response.context['form']
        self.assertIn('This field is required.', announcement_form.errors['header'])

    def test_create_announcement_view_post_long_header(self):
        self.client.login(username='testuser1', password='password')
        long_header = 'A' * 256  # Assuming max length is 255
        form_data = {
            'header': long_header,
            'content': 'Content with long header'
        }
        response = self.secure_post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        announcement_form = response.context['form']
        self.assertIn('Ensure this value has at most 255 characters (it has 256).', announcement_form.errors['header'])
        
    def test_view_announcement_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_announcements'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/viewAnnouncement.html')
        self.assertContains(response, self.announcement.header)

    def test_view_announcement_detail_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_announcement_detail', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/viewAnnouncementDetail.html')
        self.assertContains(response, self.announcement.header)
        self.assertContains(response, self.announcement.content)

    def test_edit_announcement_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('edit_announcement', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/editAnnouncement.html')

    def test_edit_announcement_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'header': 'Test Announcement updated',
            'content': 'Test content updated'
        }
        response = self.secure_post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.announcement.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.announcement.header, 'Test Announcement updated')
        self.assertEqual(self.announcement.content, 'Test content updated')

    def test_create_announcement_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'header': '',
            'content': 'Content with empty header'
        }
        response = self.secure_post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        announcement_form = response.context['form']
        self.assertIn('This field is required.', announcement_form.errors['header'])

    def test_edit_announcement_view_post_long_header(self):
        self.client.login(username='testuser1', password='password')
        long_header = 'A' * 256  # Assuming max length is 255
        form_data = {
            'header': long_header,
            'content': 'Content with long header'
        }
        response = self.secure_post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        announcement_form = response.context['form']
        self.assertIn('Ensure this value has at most 255 characters (it has 256).', announcement_form.errors['header'])

    def test_delete_announcement_view_post(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_post(reverse('delete_announcement', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.filter(pk=self.announcement.pk).exists())

class PartyViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.user = self.create_test_user()
        self.party = Party.objects.create(
            party_name="Test Party",
            description="Test Discription"
        )

        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if not self.election_phase:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)


    def tearDown(self):
        self.party.delete()

    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1960-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_create_party_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('create_party'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/createParty.html')

    def test_create_party_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'party_name': 'New Party',
            'description': 'Test Description'
        }
        response = self.secure_post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Party.objects.filter(party_name='New Party').exists())

    def test_create_party_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'party_name': '',
            'description': 'Description with empty name'
        }
        response = self.secure_post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 200)
        party_form = response.context['form']
        self.assertIn('This field is required.', party_form.errors['party_name'])

    def test_create_party_view_post_existing(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'party_name': 'Test Party',
            'description': 'Description with existing name'
        }
        response = self.secure_post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 200)
        party_form = response.context['form']
        self.assertIn("Party with this name 'Test Party' already exists.", party_form.errors['party_name'])

    def test_create_party_view_post_long_name(self):
        self.client.login(username='testuser1', password='password')
        long_name = 'P' * 256  #max length is 255
        form_data = {
            'party_name': long_name,
            'description': 'Long name in party'
        }
        response = self.secure_post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 200)
        party_form = response.context['form']
        self.assertIn("Ensure this value has at most 255 characters (it has 256).", party_form.errors['party_name'])

    def test_view_party_view(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('view_parties'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/viewParty.html')
        self.assertContains(response, self.party.party_name)

    def test_edit_party_view_get(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_get(reverse('edit_party', args=[self.party.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/editParty.html')

    def test_edit_party_view_post(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'party_name': 'Updated Party',
            'description': 'Test description updated'
        }
        response = self.secure_post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.party.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.party.party_name, 'Updated Party')
        self.assertEqual(self.party.description, 'Test description updated')

    def test_edit_party_view_post_empty(self):
        self.client.login(username='testuser1', password='password')
        form_data = {
            'party_name': '',
            'description': 'Description with empty name'
        }
        response = self.secure_post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)
        party_form = response.context['form']
        self.assertIn('This field is required.', party_form.errors['party_name'])

    def test_edit_party_view_post_existing(self):
        self.client.login(username='testuser1', password='password')
        test_party = Party.objects.create(party_name="Test Party 2", description="Test Discription")
        form_data = {
            'party_name': 'Test Party',
            'description': 'Description with existing name'
        }
        response = self.secure_post(reverse('edit_party', args=[test_party.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)
        party_form = response.context['form']
        self.assertIn("Party with this name 'Test Party' already exists.", party_form.errors['party_name'])

    def test_edit_party_view_post_long_name(self):
        self.client.login(username='testuser1', password='password')
        long_name = 'P' * 256  #max length is 255
        form_data = {
            'party_name': long_name,
            'description': 'Long name in party'
        }
        response = self.secure_post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)
        party_form = response.context['form']
        self.assertIn("Ensure this value has at most 255 characters (it has 256).", party_form.errors['party_name'])

    def test_delete_party_view_post(self):
        self.client.login(username='testuser1', password='password')
        response = self.secure_post(reverse('delete_party', args=[self.party.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Party.objects.filter(pk=self.party.pk).exists())

class VoterViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(district_name="Test District", num_of_people=5)
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.profile = Profile.objects.create(profile_name="Candidate", description="Candidate Profile")
        self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")

        self.voter = Voter.objects.create(
            district=self.district,
            pkv="pkv123",
            last_login=timezone.now()
        )

        self.candidate_account = UserAccount.objects.create(
            username="testuser",
            password=make_password("password"),
            full_name="Test User",
            date_of_birth="1960-11-04",
            role=self.profile,
            district=self.district,
            party=self.party
        )

        self.candidate_profile = CandidateProfile.objects.create(
            candidate=self.candidate_account
        )

        self.singpass_user = SingpassUser.objects.create(
            singpass_id="S1234567A",
            password=make_password("password"),
            full_name="Test Singpass User",
            date_of_birth="1999-11-04",
            phone_num="12345678",
            district=self.district.district_name
        )
        
        self.user = self.create_test_user()

        self.vote_results = VoteResults.objects.create(candidate=self.candidate_account, total_vote=0)

        self.election_phase = ElectionPhase.objects.filter(phase_name="Polling Day").first()
        if not self.election_phase:
            self.election_phase = ElectionPhase.objects.create(phase_name="Polling Day", is_active=True)

    def tearDown(self):
        self.user.delete()
        self.voter.delete()
        self.district.delete()
        self.admin_profile.delete()
        self.profile.delete
        self.candidate_profile.delete()
        self.candidate_account.delete()
        self.singpass_user.delete()
        self.party.delete()
        self.election_phase.delete()

    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1960-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_singpass_login_view_get(self):
        response = self.secure_get(reverse('singpass_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'singpassLogin.html')

    @patch('myapp.views.grpc_compute_vote_run')
    def test_singpass_login_view_post(self, mock_grpc):
        mock_response = MagicMock()
        mock_grpc.return_value = mock_response

        response = self.secure_post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        }, follow=True)
        expected_url = f'https://testserver{reverse("voter_home")}'
        self.assertRedirects(response, expected_url)

        mock_grpc.assert_called_once_with(candidate_id=self.candidate_account.user_id, voter_id=self.voter.voter_id, is_voting=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Log in successful.', [str(m) for m in messages])

    @patch('myapp.views.grpc_compute_vote_run')
    def test_voter_home_view(self, mock_grpc):
        mock_response = MagicMock()
        mock_grpc.return_value = mock_response

        response = self.secure_post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        }, follow=True)
        expected_url = f'https://testserver{reverse("voter_home")}'
        self.assertRedirects(response, expected_url)
        mock_grpc.assert_called_once_with(candidate_id=self.candidate_account.user_id, voter_id=self.voter.voter_id, is_voting=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Log in successful.', [str(m) for m in messages])

        response = self.secure_get(reverse('voter_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/voterPg.html')
        self.assertContains(response, self.candidate_profile.candidate_id)

    @patch('myapp.views.grpc_compute_vote_run')
    def test_ballot_paper_view_get(self, mock_grpc):
        response = self.secure_post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        }, follow=True)
        response = self.secure_get(reverse('ballot_paper'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/votingPg.html')
        self.assertContains(response, self.candidate_profile.candidate_id)

    @patch('myapp.views.grpc_compute_vote_run')
    def test_cast_vote_view_get(self, mock_grpc):
        response = self.secure_post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        }, follow=True)
        response = self.secure_get(reverse('cast_vote'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/votingPg.html')
        self.assertContains(response, self.candidate_profile.candidate_id)

    @patch('myapp.views.grpc_compute_vote_run')
    def test_cast_vote_view_post(self, mock_grpc):
        mock_response = MagicMock()
        mock_grpc.return_value = mock_response

        response = self.secure_post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        }, follow=True)

        response = self.secure_post(reverse('cast_vote'), {
            'candidate': [self.candidate_profile.pk]
        })
        self.assertEqual(response.status_code, 302)
        expected_calls = [
            call(candidate_id=self.candidate_account.user_id, voter_id=self.voter.voter_id, is_voting=False),
            call(candidate_id=self.candidate_account.user_id, voter_id=self.voter.voter_id, is_voting=True)
        ]
        mock_grpc.assert_has_calls(expected_calls, any_order=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Your vote has been submitted.', [str(m) for m in messages])

    @patch('myapp.views.grpc_compute_vote_run')
    def test_cast_vote_view_post_double_voting(self, mock_grpc):
        mock_response = MagicMock()
        mock_grpc.side_effect = [
            mock_response,  # First call returns normally (log in check voting status)
            mock_response,  # First call returns normally (first time vote)
            GrpcError('CORE_DOUBLE_VOTING')  # Second call raises an error (second time vote)
        ]

        response = self.secure_post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        }, follow=True)

        #initail vote
        response = self.secure_post(reverse('cast_vote'), {
            'candidate': [self.candidate_profile.pk]
        })
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Your vote has been submitted.', [str(m) for m in messages])
        #double vote
        response = self.secure_post(reverse('cast_vote'), {
            'candidate': [self.candidate_profile.pk]
        })
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Double voting detected. Your vote is invalid.', [str(m) for m in messages])

class CandidateViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(district_name="Test District", num_of_people=5)
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.profile = Profile.objects.create(profile_name="Candidate", description="Candidate Profile")
        self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")

        self.candidate_account = UserAccount.objects.create(
            username="testuser",
            password=make_password("password"),
            full_name="Test Candidate",
            date_of_birth="1960-04-11",
            role=self.profile,
            district=self.district,
            party=self.party
        )
        self.candidate_profile = CandidateProfile.objects.create(
            candidate=self.candidate_account,
            candidate_statement='Test Statement'
        )

        self.user = self.create_test_user()

        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if not self.election_phase:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

    def tearDown(self):
        self.user.delete()
        self.candidate_account.delete()
        self.admin_profile.delete()
        self.profile.delete()
        self.district.delete()
        self.party.delete()
        self.candidate_profile.delete()
        self.election_phase.delete()

    def create_test_user(self):
        user = User(
            username='testuser1',
            full_name='Test user 1',
            date_of_birth='1960-11-04',
            role=self.admin_profile
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user
    
    def create_dummy_image(self):
        # Create a dummy image file for testing
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_candidate_home_view(self):
        self.client.login(username='testuser', password='password')
        response = self.secure_get(reverse('candidate_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Candidate/candidatePg.html')
        self.assertContains(response, self.candidate_profile.candidate_statement)

    def test_upload_election_poster_view_post(self):
        self.client.login(username='testuser', password='password')
        dummy_image1 = self.create_dummy_image()
        poster_data = {
            'election_poster': SimpleUploadedFile('poster.png', dummy_image1.getvalue(), content_type='image/png')
        }
        response = self.secure_post(reverse('upload_election_poster'), poster_data)
        self.assertEqual(response.status_code, 302)
        
        self.candidate_profile.refresh_from_db()
        self.assertTrue(self.candidate_profile.election_poster)

    def test_upload_profile_picture_view_post(self):
        self.client.login(username='testuser', password='password')
        dummy_image1 = self.create_dummy_image()
        profile_pic_data = {
            'profile_picture': SimpleUploadedFile('profile.png', dummy_image1.getvalue(), content_type='image/png')
        }
        response = self.secure_post(reverse('upload_profile_picture'), profile_pic_data)
        self.assertEqual(response.status_code, 302)
        
        self.candidate_profile.refresh_from_db()
        self.assertTrue(self.candidate_profile.profile_picture)

    def test_upload_candidate_statement_view_post(self):
        self.client.login(username='testuser', password='password')
        statement_data = {
            'candidate_statement': 'This is my campaign promise.'
        }
        response = self.secure_post(reverse('upload_candidate_statement'), statement_data)
        self.assertEqual(response.status_code, 302)

        self.candidate_profile.refresh_from_db()
        self.assertEqual(self.candidate_profile.candidate_statement, 'This is my campaign promise.')

class PasswordChangeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin", description="Admin Profile")
        self.candidate_profile = Profile.objects.create(profile_name="Candidate", description="Candidate Profile")
        self.district = District.objects.create(district_name="Test District", num_of_people=5)
        self.user = self.create_test_user()

    def tearDown(self):
        self.user.delete()
        self.admin_profile.delete()
        self.candidate_profile.delete()
        self.district.delete()

    def create_test_user(self):
        user = UserAccount(
            username='testuser',
            full_name='Test user',
            date_of_birth='1999-11-04',
            role=self.admin_profile
        )
        user.set_password('old_password')
        user.save()
        return user
    
    def secure_post(self, url, data=None, **kwargs):
        return self.client.post(url, data, secure=True, **kwargs)
    
    def secure_get(self, url, **kwargs):
        return self.client.get(url, secure=True, **kwargs)

    def test_password_change_view_get(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'changePassword.html')

    def test_password_change_view_post_correct_change(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword1!',
            'confirm_password': 'Newpassword1!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserAccount.objects.get(username='testuser').check_password('Newpassword1!'))

    def test_password_change_view_post_wrong_current_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'not_old_password',
            'new_password': 'Newpassword1!',
            'confirm_password': 'Newpassword1!'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Current password is incorrect.", change_password_form.errors['current_password'])

    def test_password_change_view_post_not_match_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword1!',
            'confirm_password': 'Newpassword2!'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Confirm password does not match new password.", change_password_form.errors['confirm_password'])

    def test_password_change_view_post_short_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'short1!',
            'confirm_password': 'short1!'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Password must have more than 8 characters.", change_password_form.errors['new_password'])

    def test_password_change_view_post_no_number_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword!',
            'confirm_password': 'Newpassword!'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Password must contain at least one number.", change_password_form.errors['new_password'])

    def test_password_change_view_post_no_uppercase_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'newpassword1!',
            'confirm_password': 'newpassword1!'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Password must contain at least one uppercase letter.", change_password_form.errors['new_password'])

    def test_password_change_view_post_no_lowercase_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'NEWPASSWORD1!',
            'confirm_password': 'NEWPASSWORD1!'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Password must contain at least one lowercase letter.", change_password_form.errors['new_password'])

    def test_password_change_view_post_no_symbol_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword1',
            'confirm_password': 'Newpassword1'
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Password must contain at least one special character.", change_password_form.errors['new_password'])

    def test_password_change_view_post_long_password(self):
        self.client.login(username='testuser', password='old_password')
        long_password = 'a' * 101 + '!A1'
        response = self.secure_post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': long_password,
            'confirm_password': long_password
        })
        self.assertEqual(response.status_code, 200)
        change_password_form = response.context['form']
        self.assertIn("Password must not exceed 100 characters.", change_password_form.errors['new_password'])

