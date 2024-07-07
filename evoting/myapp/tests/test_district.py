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
        mock_grpc.side_effect = GrpcError("Test Mock gRPC error")
        form_data = {
            'district_names': 'Error District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Error District').exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Error in gRPC call: Test Mock gRPC error', [str(m) for m in messages])

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
