from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from django.contrib.messages import get_messages
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
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
from pygrpc.ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_construct_vote_request,
    grpc_construct_gen_candidate_request,
    grpc_construct_calculate_total_vote_request,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
    GrpcError,
)


User = get_user_model()

class UserAccountViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin")
        self.candidate_profile = Profile.objects.create(profile_name="Candidate")
        self.district = District.objects.create(district_name="Test District")
        self.user = self.create_test_user()

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
            role=self.admin_profile,
            district=self.district
        )
        user.set_password('password')  # Set the password using set_password to handle hashing
        user.save()
        return user

    def test_user_login_view(self):
        response = self.client.post(reverse('login'), {'username': 'testuser1', 'password': 'password'})
        self.assertEqual(response.status_code, 302) # HTTP_302_FOUND
        self.assertRedirects(response, reverse('admin_home'))

    def test_create_account_view_get(self): # used to render the form for the user
        response = self.client.get(reverse('create_account'))
        self.assertEqual(response.status_code, 200) #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/createUserAcc.html')

    @patch('myapp.views.grpc_generate_candidate_keys_run')
    def test_create_account_view_post_candidate(self, mock_grpc):
        # Create a mock response
        mock_response = MagicMock()
        mock_grpc.return_value = mock_response

        form_data = {
            'username': 'testcandidate',
            'password': 'password',
            'full_name': 'Test Candidate',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        } 
        response = self.client.post(reverse('create_account'), data=form_data)
        
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
        # Simulate a gRPC error
        mock_grpc.side_effect = GrpcError("Test Mock gRPC error in create account")

        form_data = {
            'username': 'testcandidate2',
            'password': 'password',
            'full_name': 'Test Candidate 2',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Still expecting a redirect
        self.assertTrue(User.objects.filter(username='testcandidate2').exists())
        
        created_user = User.objects.get(username='testcandidate2')
        self.assertTrue(CandidateProfile.objects.filter(candidate=created_user).exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Error in creating candidate keys: Test Mock gRPC error in create account', [str(m) for m in messages])

    def test_create_account_view_post_non_candidate(self):
        form_data = {
            'username': 'testuser',
            'password': 'password',
            'full_name': 'Test User',
            'date_of_birth': '1999-01-01',
            'role': self.admin_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        created_user = User.objects.get(username='testuser')
        self.assertFalse(CandidateProfile.objects.filter(candidate=created_user).exists())
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Account successfully created.', [str(m) for m in messages])

    def test_create_account_view_post_empty(self):
        form_data = {}
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

    def test_create_account_view_post_existing(self):
        form_data = {
            'username': 'testuser1',  #duplicate username
            'password': 'password',
            'full_name': 'Test user 2',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'User account with this Username already exists.')

    def test_create_account_view_post_invalid_date(self):
        form_data = {
            'username': 'testuser3',
            'password': 'password',
            'full_name': 'Test user 3',
            'date_of_birth': 'invalid-date',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'date_of_birth', 'Enter a valid date.')

    @patch('myapp.views.grpc_generate_candidate_keys_run')
    def test_create_account_view_post_special_character(self, mock_grpc):
        mock_response = MagicMock()
        mock_grpc.return_value = mock_response

        form_data = {
            'username': '+es+@user!',  # Special characters
            'password': 'password',
            'full_name': 'Test user 5',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertTrue(User.objects.filter(username='+es+@user!').exists())
        
        created_user = User.objects.get(username='+es+@user!')
        self.assertTrue(CandidateProfile.objects.filter(candidate=created_user).exists())
        
        # Assert that the gRPC function was called
        mock_grpc.assert_called_once_with(candidate_id=created_user.user_id)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Account successfully created.', [str(m) for m in messages])

    def test_create_account_view_post_long_username(self):
        long_username = 'a' * 201  #Max length 200
        form_data = {
            'username': long_username,
            'password': 'password',
            'full_name': 'Test user 6',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'Ensure this value has at most 200 characters (it has 201).')

    def test_edit_account_view_get(self): # used to render the form for the user
        response = self.client.get(reverse('edit_user', args=[self.user.user_id]))
        self.assertEqual(response.status_code, 200) #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/updateUserAcc.html')

    def test_edit_account_view_post(self):
        form_data = {
            'username': self.user.username,
            'full_name': 'Test user updated',
            'date_of_birth': self.user.date_of_birth,
            'district': self.user.district.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302) #HTTP_302_FOUND
        self.assertEqual(self.user.full_name, 'Test user updated')

    def test_edit_account_view_post_empty(self):
        form_data = {}
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

    def test_edit_account_view_post_existing(self):
        form_data = {
            'username': 'testuser1',  # duplicate username
            'full_name': 'Test user updated',
            'date_of_birth': self.user.date_of_birth,
            'district': self.user.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'User account with this Username already exists.')

    def test_edit_account_view_post_invalid_date(self):
        form_data = {
            'username': 'testuser2',
            'full_name': 'Test user updated',
            'date_of_birth': 'invalid-date',
            'district': self.user.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'date_of_birth', 'Enter a valid date.')

    def test_edit_account_view_post_special_character(self):
        form_data = {
            'username': '+es+@user4',
            'full_name': 'Test user updated',
            'date_of_birth': '1999-01-01',
            'district': self.user.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='+es+@user4').exists())

    def test_edit_account_view_post_long_username(self):
        long_username = 'a' * 201  #Max length 200
        form_data = {
            'username': long_username,
            'full_name': 'Test user 65',
            'date_of_birth': '1999-01-01',
            'district': self.district.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'Ensure this value has at most 200 characters (it has 201).')

    def test_delete_account_view_post(self):
        response = self.client.post(reverse('delete_user', args=[self.user.user_id]))
        self.assertEqual(response.status_code, 302) #HTTP_302_FOUND
        self.assertFalse(User.objects.filter(user_id=self.user.user_id).exists())

    def test_view_accounts_view(self):
        response = self.client.get(reverse('view_user_accounts'))
        self.assertEqual(response.status_code, 200)  #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/viewUserAcc.html')



class DistrictViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = self.create_district("Test District 1")

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

    def create_district(self, district_name):
        return District.objects.create(district_name=district_name)
        
    def test_create_district_view_get(self):
        response = self.client.get(reverse('create_district'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/createDistrict.html')

    def test_create_district_view_post_empty(self):
        form_data = {
            'district_names': ''
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_names', 'This field is required.')

    @patch('myapp.views.grpc_generate_user_and_votingcurr_run')
    def test_create_district_view_post_one(self, mock_grpc):
        mock_response = ringct_pb2.Gen_VoterCurr_Response()
        mock_grpc.return_value = mock_response # a single mock response is created and set as the return value.
        
        form_data = {
            'district_names': 'Single District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        created_district = District.objects.get(district_name='Single District')
        self.assertTrue(created_district)
        mock_grpc.assert_called_once_with(district_id=created_district.district_id, voter_num=20) # uses the voter_num in create_district view
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('District(s) successfully created.', [str(m) for m in messages]) # check if the success message went thru

    @patch('myapp.views.grpc_generate_user_and_votingcurr_run')
    def test_create_district_view_post(self, mock_grpc):
        def side_effect(district_id, voter_num): # a side effect function is used to create a new mock response for each call
            mock_response = ringct_pb2.Gen_VoterCurr_Response()
            mock_response.district_id = district_id
            mock_response.voter_num = voter_num #
            return mock_response
        
        mock_grpc.side_effect = side_effect

        form_data = {
            'district_names': 'Test District 2; Test District 3; Test District 4'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Test District 2').exists())
        self.assertTrue(District.objects.filter(district_name='Test District 3').exists())
        self.assertTrue(District.objects.filter(district_name='Test District 4').exists())

        self.assertEqual(mock_grpc.call_count, 3) #check if the grpc is called 3 times
        
        calls = mock_grpc.call_args_list
        created_districts = District.objects.filter(district_name__in=['Test District 2', 'Test District 3', 'Test District 4']).order_by('district_id')
        for i, call in enumerate(calls):
            self.assertEqual(call[1], {'district_id': created_districts[i].district_id, 'voter_num': 20}) # uses the voter_num in create_district view and check if each call creates a districts

        messages = list(get_messages(response.wsgi_request))
        self.assertIn('District(s) successfully created.', [str(m) for m in messages]) # check if the success message went thru

    def test_create_district_view_post_existing(self):
        form_data = {
            'district_names': 'Test District 1; Another District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_names', 'District(s) already exist: Test District 1')

    @patch('myapp.views.grpc_generate_user_and_votingcurr_run')
    def test_create_district_view_post_special_characters(self, mock_grpc):
        mock_grpc.return_value = None
        form_data = {
            'district_names': 'Test-Distric+#%; An()ther D!stric+'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Test-Distric+#%').exists())
        self.assertTrue(District.objects.filter(district_name='An()ther D!stric+').exists())
        self.assertEqual(mock_grpc.call_count, 2)

    def test_create_district_view_post_long_name(self):
        long_name = 'a' * 256  # models max length 255
        form_data = {
            'district_names': long_name
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_names', f"District name '{long_name}' exceeds 255 characters limit.")

    @patch('myapp.views.grpc_generate_user_and_votingcurr_run')
    def test_create_district_view_post_grpc_error(self, mock_grpc):
        mock_grpc.side_effect = GrpcError("Test Mock gRPC error in create district")
        form_data = {
            'district_names': 'Error District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Error District').exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Error in gRPC call: Test Mock gRPC error in create district', [str(m) for m in messages])

    def test_view_district_view(self):
        response = self.client.get(reverse('view_district'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/viewDistrict.html')
        self.assertContains(response, self.district.district_name)

    def test_view_district_search_view(self):
        response = self.client.get(reverse('view_district'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.district.district_name)

    def test_edit_district_view_get(self):
        response = self.client.get(reverse('edit_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/editDistrict.html')

    def test_edit_district_view_post(self):
        form_data = {
            'district_name': 'Test District Updated'
        }
        response = self.client.post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.district.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.district.district_name, 'Test District Updated')

    def test_edit_district_view_post_empty(self):
        form_data = {
            'district_name': ''
        }
        response = self.client.post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_name', 'This field is required.')

    def test_edit_district_view_post_existing(self):
        form_data = {
            'district_name': 'Test District 1'
        }
        response = self.client.post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_name', 'District(s) already exist: Test District 1')

    def test_edit_district_view_post_special_character(self):
        form_data = {
            'district_name': '+es+ Di$+r1ct 1'
        }
        response = self.client.post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='+es+ Di$+r1ct 1').exists())
    
    def test_edit_district_view_post_long_name(self):
        long_name = 'a' * 256  #models max length 255
        form_data = {
            'district_name': long_name
        }
        response = self.client.post(reverse('edit_district', args=[self.district.district_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_name', 'Ensure this value has at most 255 characters (it has 256).')

    def test_delete_district_view_post_successfull(self):
        response = self.client.post(reverse('delete_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('view_district'))
        self.assertFalse(District.objects.filter(district_id=self.district.district_id).exists())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'District successfully deleted.')

    def test_delete_district_view_post_unsuccessful(self):
        response = self.client.get(reverse('delete_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('view_district'))
        self.assertTrue(District.objects.filter(district_id=self.district.district_id).exists())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Error deleting district.')



class ProfileViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if not self.election_phase:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

        self.profile = Profile.objects.create(profile_name="Test Profile", description="Test description")

    def tearDown(self):
        self.election_phase.delete()

    def test_create_profile_view_get(self):
        response = self.client.get(reverse('create_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/createProfile.html')

    def test_create_profile_view_post(self):
        form_data = {
            'profile_name': 'Test Profile',
            'description': 'Test description'
        }
        response = self.client.post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Profile.objects.filter(profile_name='Test Profile').exists())

    def test_create_profile_view_post_empty(self):
        form_data = {
            'profile_name': '',
            'description': 'Test description'
        }
        response = self.client.post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'profile_name', 'This field is required.')

    def test_create_profile_view_post_existing(self):
        form_data = {
            'profile_name': 'Candidate',
            'description': 'Duplicate profile name'
        }
        response = self.client.post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'profile_name', 'This profile name is not allowed or already exists.')

    def test_create_profile_view_post_special_characters(self):
        special_name = '!@#$%^&*()_+'
        form_data = {
            'profile_name': special_name,
            'description': 'Profile with special characters'
        }
        response = self.client.post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Profile.objects.filter(profile_name=special_name).exists())

    def test_create_profile_view_post_long_name(self):
        long_name = 'a' * 256  # max length is 255
        form_data = {
            'profile_name': long_name,
            'description': 'Test description'
        }
        response = self.client.post(reverse('create_profile'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'profile_name', 'Ensure this value has at most 255 characters (it has 256).')

    def test_view_profiles_view(self):
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        response = self.client.get(reverse('view_profiles'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/viewProfiles.html')
        self.assertContains(response, profile.profile_name)

    def test_edit_profile_view_get(self):
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        response = self.client.get(reverse('edit_profile', args=[profile.profile_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/editProfile.html')

    def test_edit_profile_view_post(self):
        form_data = {
            'profile_name': 'Test Profile updated',
            'description': 'Test description updated'
        }
        response = self.client.post(reverse('edit_profile', args=[self.profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.profile.profile_name, 'Test Profile updated')
        self.assertEqual(self.profile.description, 'Test description updated')

    def test_edit_profile_view_post_empty(self):
        form_data = {
            'profile_name': '',
            'description': 'Test description'
        }
        response = self.client.post(reverse('edit_profile', args=[self.profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'profile_name', 'This field is required.')

    def test_edit_profile_view_post_existing(self):
        form_data = {
            'profile_name': 'Candidate',
            'description': 'Duplicate profile name'
        }
        response = self.client.post(reverse('edit_profile', args=[self.profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'profile_name', 'This profile name is not allowed or already exists.')

    def test_edit_profile_view_post_special_characters(self):
        special_name = '!@#$%^&*()_+'
        form_data = {
            'profile_name': special_name,
            'description': 'Profile with special characters'
        }
        response = self.client.post(reverse('edit_profile', args=[self.profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Profile.objects.filter(profile_name=special_name).exists())

    def test_edit_profile_view_post_long_name(self):
        long_name = 'a' * 256  # max length is 255
        form_data = {
            'profile_name': long_name,
            'description': 'Test description'
        }
        response = self.client.post(reverse('edit_profile', args=[self.profile.profile_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'profile_name', 'Ensure this value has at most 255 characters (it has 256).')

    def test_delete_profile_view_post_successfull(self):
        response = self.client.post(reverse('delete_profile', args=[self.profile.profile_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('view_profiles'))
        self.assertFalse(Profile.objects.filter(profile_id=self.profile.profile_id).exists())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile successfully deleted.')

    def test_delete_profile_view_post_unsuccessful(self):
        response = self.client.post(reverse('delete_profile', args=[1234])) 
        self.assertEqual(response.status_code, 404)


class AnnouncementViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.announcement = Announcement.objects.create(
            header="Test Announcement",
            content="Test content"
        )

    def tearDown(self):
        self.announcement.delete()

    def test_create_announcement_view_get(self):
        response = self.client.get(reverse('create_announcement'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/createAnnouncement.html')

    def test_create_announcement_view_post(self):
        form_data = {
            'header': 'Test Announcement',
            'content': 'Test content'
        }
        response = self.client.post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(header='Test Announcement').exists())

    def test_create_announcement_view_post_empty(self):
        form_data = {
            'header': '',
            'content': 'Content with empty header'
        }
        response = self.client.post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        self.assertContains(response, 'This field is required.')

    def test_create_announcement_view_post_existing(self): #expected to fail, ok with same existing header
        form_data = {
            'header': 'Test Announcement',
            'content': 'Duplicate content'
        }
        response = self.client.post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 200)  # Assuming form error would not redirect
        self.assertContains(response, 'Announcement with this header already exists')

    def test_create_announcement_view_post_special_characters(self):
        special_header = '!@#$%^&*()_+'
        form_data = {
            'header': special_header,
            'content': 'Special characters in header'
        }
        response = self.client.post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(header=special_header).exists())

    def test_create_announcement_view_post_long_header(self):
        long_header = 'A' * 256  # Assuming max length is 255
        form_data = {
            'header': long_header,
            'content': 'Content with long header'
        }
        response = self.client.post(reverse('create_announcement'), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        self.assertFormError(response, 'form', 'header', 'Ensure this value has at most 255 characters (it has 256).')

    def test_view_announcement_view(self):
        response = self.client.get(reverse('view_announcement'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/viewAnnouncement.html')
        self.assertContains(response, self.announcement.header)

    def test_view_announcement_detail_view(self):
        response = self.client.get(reverse('view_announcement_detail', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/viewAnnouncementDetail.html')
        self.assertContains(response, self.announcement.header)
        self.assertContains(response, self.announcement.content)

    def test_edit_announcement_view_get(self):
        response = self.client.get(reverse('edit_announcement', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/editAnnouncement.html')

    def test_edit_announcement_view_post(self):
        form_data = {
            'header': 'Test Announcement updated',
            'content': 'Test content updated'
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.announcement.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.announcement.header, 'Test Announcement updated')
        self.assertEqual(self.announcement.content, 'Test content updated')

    def test_create_announcement_view_post_empty(self):
        form_data = {
            'header': '',
            'content': 'Content with empty header'
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        self.assertContains(response, 'This field is required.')

    def test_edit_announcement_view_post_existing(self): #expected to fail, ok with same existing header
        form_data = {
            'header': 'Test Announcement',
            'content': 'Duplicate content'
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)  # Assuming form error would not redirect
        self.assertContains(response, 'Announcement with this header already exists')

    def test_edit_announcement_view_post_special_characters(self):
        special_header = '!@#$%^&*()_+'
        form_data = {
            'header': special_header,
            'content': 'Special characters in header'
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Announcement.objects.filter(header=special_header).exists())

    def test_edit_announcement_view_post_long_header(self):
        long_header = 'A' * 256  # Assuming max length is 255
        form_data = {
            'header': long_header,
            'content': 'Content with long header'
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)  # Form error expected
        self.assertFormError(response, 'form', 'header', 'Ensure this value has at most 255 characters (it has 256).')

    def test_delete_announcement_view_get(self):
        response = self.client.get(reverse('delete_announcement', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement/deleteAnnouncement.html')

    def test_delete_announcement_view_post(self):
        response = self.client.post(reverse('delete_announcement', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.filter(pk=self.announcement.pk).exists())


class PartyViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.party = Party.objects.create(
            party_name="Test Party",
            description="Test Discription"
        )

    def tearDown(self):
        self.party.delete()

    def test_create_party_view_get(self):
        response = self.client.get(reverse('create_party'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/createParty.html')

    def test_create_party_view_post(self):
        form_data = {
            'party_name': 'New Party',
            'description': 'Test Description'
        }
        response = self.client.post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Party.objects.filter(party_name='New Party').exists())

    def test_create_party_view_post_empty(self):
        form_data = {
            'party_name': '',
            'description': 'Description with empty name'
        }
        response = self.client.post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_create_party_view_post_existing(self):
        form_data = {
            'party_name': 'Test Party',
            'description': 'Description with existing name'
        }
        response = self.client.post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A party with this name already exists.')

    def test_create_party_view_post_special_characters(self):
        special_name = '!@#$%^&*()_+'
        form_data = {
            'party_name': special_name,
            'description': 'Special characters in name'
        }
        response = self.client.post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Party.objects.filter(party_name=special_name).exists())

    def test_create_party_view_post_long_name(self):
        long_name = 'P' * 256  #max length is 255
        form_data = {
            'party_name': long_name,
            'description': 'Long name in party'
        }
        response = self.client.post(reverse('create_party'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'party_name', 'Ensure this value has at most 255 characters (it has 256).')

    def test_view_party_view(self):
        response = self.client.get(reverse('view_party'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/viewParty.html')
        self.assertContains(response, self.party.party_name)

    def test_edit_party_view_get(self):
        response = self.client.get(reverse('edit_party', args=[self.party.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/editParty.html')

    def test_edit_party_view_post(self):
        form_data = {
            'party_name': 'Updated Party',
            'description': 'Test description updated'
        }
        response = self.client.post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.party.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.party.party_name, 'Updated Party')
        self.assertEqual(self.party.description, 'Test description updated')

    def test_edit_party_view_post_empty(self):
        form_data = {
            'party_name': '',
            'description': 'Description with empty name'
        }
        response = self.client.post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_edit_party_view_post_existing(self):
        form_data = {
            'party_name': 'Test Party',
            'description': 'Description with existing name'
        }
        response = self.client.post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A party with this name already exists.')

    def test_edit_party_view_post_special_characters(self):
        special_name = '!@#$%^&*()_+'
        form_data = {
            'party_name': special_name,
            'description': 'Special characters in name'
        }
        response = self.client.post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Party.objects.filter(party_name=special_name).exists())

    def test_edit_party_view_post_long_name(self):
        long_name = 'P' * 256  #max length is 255
        form_data = {
            'party_name': long_name,
            'description': 'Long name in party'
        }
        response = self.client.post(reverse('edit_party', args=[self.party.pk]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'party_name', 'Ensure this value has at most 255 characters (it has 256).')

    def test_delete_party_view_get(self):
        response = self.client.get(reverse('delete_party', args=[self.party.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'party/deleteParty.html')

    def test_delete_party_view_post(self):
        response = self.client.post(reverse('delete_party', args=[self.party.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Party.objects.filter(pk=self.party.pk).exists())


class VoterViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.district = District.objects.create(district_name="Test District")
        self.profile = Profile.objects.create(profile_name="Voter")
        self.voter = Voter.objects.create(
            district=self.district,
            hash_from_info=None,
            pkv="pkv123"
        )
        self.user_account = UserAccount.objects.create(
            username="testuser",
            password=make_password("password"),
            full_name="Test User",
            date_of_birth="1999-11-04",
            role=self.profile,
            district=self.district
        )
        self.candidate_profile = CandidateProfile.objects.create(
            candidate=self.user_account,
            candidate_statement="Test Statement"
        )
        self.singpass_user = SingpassUser.objects.create(
            singpass_id="S1234567A",
            password=make_password("password"),
            full_name="Test Singpass User",
            date_of_birth="1999-11-04",
            phone_num="12345678",
            district=self.district
        )

    def tearDown(self):
        self.voter.delete()
        self.district.delete()
        self.profile.delete()
        self.user_account.delete()
        self.candidate_profile.delete()
        self.singpass_user.delete()

    def test_singpass_login_view_get(self):
        response = self.client.get(reverse('singpass_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'singpassLogin.html')

    def test_singpass_login_view_post(self):
        response = self.client.post(reverse('singpass_login'), {
            'singpass_id': self.singpass_user.singpass_id,
            'password': 'password'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('voter_home'))

    def test_voter_home_view(self):
        self.client.force_login(self.voter)
        response = self.client.get(reverse('voter_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/voterPg.html')
        self.assertContains(response, self.candidate_profile.candidate_id)

    def test_ballot_paper_view_get(self):
        self.client.force_login(self.voter)
        response = self.client.get(reverse('ballot_paper'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/votingPg.html')
        self.assertContains(response, self.candidate_profile.candidate_id)

    def test_cast_vote_view_get(self):
        self.client.force_login(self.voter)
        response = self.client.get(reverse('cast_vote'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/votingPg.html')
        self.assertContains(response, self.candidate_profile.candidate_id)

    def test_cast_vote_view_post(self):
        self.client.force_login(self.voter)
        response = self.client.post(reverse('cast_vote'), {
            'candidate': [self.candidate_profile.pk]
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ballot_paper'))
        follow_response = self.client.get(reverse('ballot_paper'), follow=True)
        self.assertContains(follow_response, 'Your vote has been submitted.')

    def test_cast_vote_view_post_double_voting(self):
        self.client.force_login(self.voter)
        #initail vote
        self.client.post(reverse('cast_vote'), {
            'candidate': [self.candidate_profile.pk]
        })
        #double vote
        response = self.client.post(reverse('cast_vote'), {
            'candidate': [self.candidate_profile.pk]
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ballot_paper'))
        follow_response = self.client.get(reverse('ballot_paper'), follow=True)
        self.assertContains(follow_response, 'Double voting detected. Your vote is invalid.')


class CandidateViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(profile_name="Candidate")
        self.district = District.objects.create(district_name="Test District")
        self.user_account = UserAccount.objects.create(
            username="testuser",
            password=make_password("password"),
            full_name="Test Candidate",
            date_of_birth="1999-04-11",
            role=self.profile,
            district=self.district
        )
        self.candidate_profile = CandidateProfile.objects.create(
            candidate=self.user_account,
            candidate_statement="Test Statement"
        )
        self.client.force_login(self.user_account)

    def tearDown(self):
        self.user_account.delete()
        self.profile.delete()
        self.district.delete()
        self.candidate_profile.delete()

    def test_candidate_home_view(self):
        response = self.client.get(reverse('candidate_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Candidate/candidatePg.html')
        self.assertContains(response, self.candidate_profile.candidate_statement)

    def test_upload_election_poster_view_post(self):
        with open('media/profile_pictures/download_1.webp', 'rb') as poster:
            form_data = {'election_poster': poster}
            response = self.client.post(reverse('upload_election_poster'), data=form_data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertRedirects(response, reverse('candidate_home'))
            self.candidate_profile.refresh_from_db()
            self.assertTrue(self.candidate_profile.election_poster)

    def test_upload_profile_picture_view_post(self):
        with open('media/profile_pictures/download_1.webp', 'rb') as picture:
            form_data = {'profile_picture': picture}
            response = self.client.post(reverse('upload_profile_picture'), data=form_data, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertRedirects(response, reverse('candidate_home'))
            self.candidate_profile.refresh_from_db()
            self.assertTrue(self.candidate_profile.profile_picture)

    def test_upload_candidate_statement_view_post(self):
        form_data = {'candidate_statement': 'Updated Statement'}
        response = self.client.post(reverse('upload_candidate_statement'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('candidate_home'))
        self.candidate_profile.refresh_from_db()
        self.assertEqual(self.candidate_profile.candidate_statement, 'Updated Statement')


class PasswordChangeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_profile = Profile.objects.create(profile_name="Admin")
        self.candidate_profile = Profile.objects.create(profile_name="Candidate")
        self.district = District.objects.create(district_name="Test District")
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
            role=self.admin_profile,
            district=self.district
        )
        user.set_password('old_password')
        user.save()
        return user

    def test_password_change_view_get(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'changePassword.html')

    def test_password_change_view_post_correct_change(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword1!',
            'confirm_password': 'Newpassword1!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserAccount.objects.get(username='testuser').check_password('Newpassword1!'))

    def test_password_change_view_post_wrong_current_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'not_old_password',
            'new_password': 'Newpassword1!',
            'confirm_password': 'Newpassword1!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'current_password', 'Current password is incorrect.')

    def test_password_change_view_post_not_match_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword1!',
            'confirm_password': 'Newpassword2!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'confirm_password', 'Confirm password does not match new password.')

    def test_password_change_view_post_short_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'short1!',
            'confirm_password': 'short1!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password', 'Password must have more than 8 characters.')

    def test_password_change_view_post_no_number_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword!',
            'confirm_password': 'Newpassword!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password', 'Password must contain at least one number.')

    def test_password_change_view_post_no_uppercase_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'newpassword1!',
            'confirm_password': 'newpassword1!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password', 'Password must contain at least one uppercase letter.')

    def test_password_change_view_post_no_lowercase_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'NEWPASSWORD1!',
            'confirm_password': 'NEWPASSWORD1!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password', 'Password must contain at least one lowercase letter.')

    def test_password_change_view_post_no_symbol_password(self):
        self.client.login(username='testuser', password='old_password')
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': 'Newpassword1',
            'confirm_password': 'Newpassword1'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password', 'Password must contain at least one special character.')

    def test_password_change_view_post_long_password(self):
        self.client.login(username='testuser', password='old_password')
        long_password = 'a' * 101 + '!A1'
        response = self.client.post(reverse('change_password'), {
            'current_password': 'old_password',
            'new_password': long_password,
            'confirm_password': long_password
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'new_password', 'Password must not exceed 100 characters.')

