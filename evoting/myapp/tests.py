from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from .models import UserAccount, District, ElectionPhase, Announcement, Party, Profile, CandidateProfile, Voter, SingpassUser
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

    def test_create_account_view_post(self): # used to submit the data gathered to create the acc
        form_data = {
            'username': 'testuser2',
            'password': 'password',
            'full_name': 'Test user 2',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 302) # HTTP_302_FOUND
        self.assertTrue(User.objects.filter(username='testuser2').exists())

    def test_create_account_view_post_empty(self):
        form_data = {}
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

    def test_create_account_view_post_duplicate(self):
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

    def test_create_account_view_post_missing_fields(self):
        form_data = {
            'username': 'testuser4',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id # password FN and DOB missing
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password', 'This field is required.')
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'date_of_birth', 'This field is required.')

    def test_create_account_view_post_special_character(self):
        form_data = {
            'username': '+es+@user!',  # Special characters
            'password': 'password',
            'full_name': 'Test user 5',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('create_account'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='+es+@user!').exists())

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
        self.assertFormError(response, 'form', 'username', 'Restrict name to be within set limits')

    def test_edit_account_view_get(self): # used to render the form for the user
        response = self.client.get(reverse('edit_user', args=[self.user.user_id]))
        self.assertEqual(response.status_code, 200) #HTTP_200_OK
        self.assertTemplateUsed(response, 'userAccount/updateUserAcc.html')

    def test_edit_account_view_post(self):
        form_data = {
            'username': self.user.username,
            'full_name': 'Test user updated',
            'date_of_birth': self.user.date_of_birth,
            'role': self.user.role.profile_id,
            'district': self.user.district.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302) #HTTP_302_FOUND
        self.assertEqual(self.user.full_name, 'Test user updated')

    def test_edit_account_view_post_empty(self):
        form_data = {
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302) #HTTP_302_FOUND
        self.assertFormError(response, 'form', 'username', 'This field is required.')

    def test_edit_account_view_post_duplicate(self):
        form_data = {
            'username': 'testuser1',  #duplicate username
            'password': 'password',
            'full_name': 'Test user 2',
            'date_of_birth': '1999-01-01',
            'role': self.candidate_profile.profile_id,
            'district': self.district.district_id
        }
        response = self.client.post(reverse('edit_user', args=[self.user.user_id]), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'User account with this Username already exists.')



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
        self.district = District.objects.create(district_name="Test District 1")

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

    def test_create_district_view_get(self):
        response = self.client.get(reverse('create_district'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/createDistrict.html')

    def test_create_district_view_post(self):
        form_data = {
            'district_names': 'Test District 4; Test District 2; Test District 3'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Test District 1').exists())

    def test_create_district_view_post(self):
        form_data = {
            'district_names': 'Test District 1; Test District 2; Test District 3'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        
        if response.status_code != 302:
            form = CreateDistrict(form_data)
            form.is_valid()  # Trigger validation to populate form errors
            print(form.errors)  # Print form errors for debugging
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Test District 2').exists())
        self.assertTrue(District.objects.filter(district_name='Test District 3').exists())

    def test_create_district_view_post_empty(self):
        form_data = {
            'district_names': ''
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_names', 'This field is required.')

    def test_create_district_view_post_one(self):
        form_data = {
            'district_names': 'Unique District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Unique District').exists())

    def test_create_district_view_post_existing(self):
        form_data = {
            'district_names': 'Test District 1; Another District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_names', 'District(s) already exist: Test District 1')


    def test_create_district_view_post_special_characters(self):
        form_data = {
            'district_names': 'Test-Distric+#%; An()ther D!stric+'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(District.objects.filter(district_name='Test-Distric+#%').exists())
        self.assertTrue(District.objects.filter(district_name='An()ther D!stric+').exists())

    def test_create_district_view_post_long_name(self):
        long_name = 'L' * 256  #models max length 200
        form_data = {
            'district_names': f'{long_name}; Another District'
        }
        response = self.client.post(reverse('create_district'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'district_names', 'Restrict name to be within set limits')


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

    def test_delete_district_view_get(self):
        response = self.client.get(reverse('delete_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'district/viewDistrict.html')

    def test_delete_district_view_post(self):
        response = self.client.post(reverse('delete_district', args=[self.district.district_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(District.objects.filter(district_id=self.district.district_id).exists())


class ProfileViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.election_phase = ElectionPhase.objects.filter(phase_name="Campaigning Day").first()
        if self.election_phase:
            self.election_phase.is_active = True
            self.election_phase.save()
        else:
            self.election_phase = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

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
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        form_data = {
            'profile_name': 'Test Profile updated',
            'description': 'Test description updated'
        }
        response = self.client.post(reverse('edit_profile', args=[profile.profile_id]), data=form_data)
        profile.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.profile_name, 'Test Profile updated')
        self.assertEqual(profile.description, 'Test description updated')

    def test_create_profile_view_post_empty_name(self):
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
        self.assertFormError(response, 'form', 'profile_name', 'Restrict name to be within set limits')

    def test_delete_profile_view_get(self):
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        response = self.client.get(reverse('delete_profile', args=[profile.profile_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userProfile/deleteProfile.html')

    def test_delete_profile_view_post(self):
        profile = Profile.objects.create(profile_name="Test Profile", description="Test description")
        response = self.client.post(reverse('delete_profile', args=[profile.profile_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Profile.objects.filter(profile_id=profile.profile_id).exists())


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
        self.assertContains(response, 'Restrict name to be within set limits')

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
        self.assertContains(response, 'Restrict name to be within set limits')

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
            district="Test District"
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
        self.assertContains(response, self.candidate_profile.candidate_statement)

    def test_ballot_paper_view_get(self):
        self.client.force_login(self.voter)
        response = self.client.get(reverse('ballot_paper'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Voter/votingPg.html')
        self.assertContains(response, self.candidate_profile.candidate_statement)

    def test_cast_vote_view_get(self):
        self.client.force_login(self.voter)
        response = self.client.get(reverse('cast_vote'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'voting/ballot_paper.html')
        self.assertContains(response, self.candidate_profile.candidate_statement)

    def test_cast_vote_view_post(self):
        self.client.force_login(self.voter)
        response = self.client.post(reverse('cast_vote'), {
            'candidate': [self.user_account.pk]
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ballot_paper'))
        self.assertContains(response, 'Your vote has been submitted.')

    def test_cast_vote_view_post_double_voting(self):
        self.client.force_login(self.voter)
        response = self.client.post(reverse('cast_vote'), {
            'candidate': [self.user_account.pk]
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ballot_paper'))
        self.assertContains(response, 'Double voting detected. Your vote is invalid.')


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