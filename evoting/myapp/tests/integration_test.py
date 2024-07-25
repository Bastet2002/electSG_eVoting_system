from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.messages import get_messages
from django.contrib.auth.hashers import make_password
from ..models import Profile, District, Party, Announcement, UserAccount, Voter, SingpassUser, CandidateProfile, ElectionPhase

# class LoginLogoutIntegrationTest(TransactionTestCase):
#     reset_sequences = True
#     def setUp(self):
#         # Create roles
#         self.admin_role = Profile.objects.create(profile_name='Admin', description="Admin Profile")
#         self.candidate_role = Profile.objects.create(profile_name='Candidate', description="Candidate Profile")

#         # Create district
#         self.district = District.objects.create(district_name="Central District", num_of_people=10)

#         # Create party
#         self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")

#         # Create Singpass data
#         self.singpass_user = SingpassUser.objects.create(
#             singpass_id="SP001",
#             password=make_password("password123"),
#             full_name="Bruce Wayne",
#             date_of_birth="1990-01-01",
#             phone_num="12345678",
#             district="Central District"
#         )

#         # Create users 
#         self.admin_user = UserAccount.objects.create(
#             username="john_doe",
#             password=make_password("password123"),
#             full_name="John Doe",
#             date_of_birth="1990-01-01",
#             role=self.admin_role
#         )

#         self.candidate_user = UserAccount.objects.create(
#             username="mary_james",
#             password=make_password("password123"),
#             full_name="Marry James",
#             date_of_birth="1960-01-01",
#             role=self.candidate_role,
#             district=self.district,
#             party=self.party
#         )

#         self.voter_user = Voter.objects.create(
#             district=self.district,
#             pkv="pkv1234",
#             last_login=timezone.now()
#         )

#         # Create candidate profile
#         self.candidate_profile = CandidateProfile.objects.create(
#             candidate=self.candidate_user,
#             candidate_statement="Vote for me!"
#         )

#     def test_admin_login_logout(self):
#         self._test_user_login_logout(self.admin_user, 'password123', 'admin_home')

#     def test_candidate_login_logout(self):
#         self._test_user_login_logout(self.candidate_user, 'password123', 'candidate_home')

#     def _test_user_login_logout(self, user, password, expected_redirect):
#         login_url = reverse('login')
#         logout_url = reverse('logout')

#         # Test login
#         response = self.client.post(login_url, {'username': user.username, 'password': password})
#         self.assertRedirects(response, reverse(expected_redirect))

#         # Verify session exists
#         self.assertTrue(Session.objects.filter(session_key=self.client.session.session_key).exists())

#         # Test logout
#         response = self.client.get(logout_url)
#         self.assertRedirects(response, reverse('login'))

#         # Check for success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'You have been successfully logged out.')

#         # Verify session is deleted
#         self.assertFalse(Session.objects.filter(session_key=self.client.session.session_key).exists())

#     def test_voter_singpass_login_logout(self):
#         login_url = reverse('singpass_login')
#         logout_url = reverse('logout')

#         # Test Singpass login
#         response = self.client.post(login_url, {
#             'singpass_id': 'SP001',
#             'password': 'password123'
#         })
#         self.assertRedirects(response, reverse('voter_home'))

#         # Verify session exists
#         self.assertTrue(Session.objects.filter(session_key=self.client.session.session_key).exists())

#         # Test logout
#         response = self.client.get(logout_url)
#         self.assertRedirects(response, reverse('login'))

#         # Check for success message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(len(messages), 1)
#         self.assertEqual(str(messages[0]), 'You have been successfully logged out.')

#         # Verify session is deleted
#         self.assertFalse(Session.objects.filter(session_key=self.client.session.session_key).exists())

class ElectionProcessIntegrationTest(TransactionTestCase):
    reset_sequences = True
    def setUp(self):
         # Create roles
        self.admin_role = Profile.objects.create(profile_name='Admin', description="Admin Profile")
        self.candidate_role = Profile.objects.create(profile_name='Candidate', description="Candidate Profile")

        # Create district
        self.district = District.objects.create(district_name="Central District", num_of_people=10)

        # Create party
        self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")

        # Create election phase
        self.campaigning_day = ElectionPhase.objects.create(phase_name="Campaigning Day", is_active=True)

        # Create Singpass data
        self.singpass_user = SingpassUser.objects.create(
            singpass_id="SP001",
            password=make_password("password123"),
            full_name="Bruce Wayne",
            date_of_birth="1990-01-01",
            phone_num="12345678",
            district="Central District"
        )

        # Create users 
        self.admin_user = UserAccount.objects.create(
            username="john_doe",
            password=make_password("Password123!"),
            full_name="John Doe",
            date_of_birth="1990-01-01",
            role=self.admin_role
        )

        self.voter_user = Voter.objects.create(
            district=self.district,
            pkv="pkv1234",
            last_login=timezone.now()
        )

    def create_dummy_image(self):
        # Create a dummy image file for testing
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file

    def test_election_process(self):
        # Admin log in
        login_successful = self.client.login(username='john_doe', password='Password123!')
        self.assertTrue(login_successful)

        # Create candidate account
        candidate_data = {
            'username': 'candidate2',
            'password': 'Candidatepass123!',
            'full_name': 'John Candidate',
            'date_of_birth': '1965-05-15',
            'role': self.candidate_role.profile_id,
            'district': self.district.district_id,
            'party': self.party.party_id
        }
        response = self.client.post(reverse('create_account'), candidate_data)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        print(f"Response headers: {response.headers}")
        candidate = UserAccount.objects.get(username='candidate2')
        print(candidate.username)
        print(candidate.full_name)
        self.assertEqual(response.status_code, 302)

        

        # Activate Campaigning Day phase
        response = self.client.get(reverse('activate_election_phase', args=[self.campaigning_day.phase_id]))
        # self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        # Candidate uploads information
        response = self.client.post(reverse('login'), {'username': 'candidate2', 'password': 'Candidatepass123'})
        self.assertRedirects(response, reverse('candidate_home'))

        # Retrieve the created candidate user
        candidate = UserAccount.objects.get(username="candidate2")

        # Upload profile picture
        dummy_image1 = self.create_dummy_image()
        profile_pic_data = {
            'profile_picture': SimpleUploadedFile('profile.png', dummy_image1.getvalue(), content_type='image/png')
        }
        response = self.client.post(reverse('upload_profile_picture'), profile_pic_data)
        self.assertEqual(response.status_code, 302)

        # Upload election poster
        dummy_image2 = self.create_dummy_image()
        poster_data = {
            'election_poster': SimpleUploadedFile('poster.png', dummy_image2.getvalue(), content_type='image/png')
        }
        response = self.client.post(reverse('upload_election_poster'), poster_data)
        self.assertEqual(response.status_code, 302)

        # Update candidate statement
        statement_data = {
            'candidate_statement': 'This is my campaign promise.'
        }
        response = self.client.post(reverse('upload_candidate_statement'), statement_data)
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        # Voter views and votes
        response = self.client.post(reverse('singpass_login'), {
            'singpass_id': 'SP001',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('voter_home'))
        
        # Retrieve candidate profile
        candidate_profile = CandidateProfile.objects.get(pk=candidate)

        # View candidate information
        response = self.client.get(reverse('view_candidate', args=[candidate.user_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Candidate')
        self.assertContains(response, candidate_profile.profile_picture.url)
        self.assertContains(response, candidate_profile.election_poster.url)
        self.assertContains(response, 'This is my campaign promise.')

        # Cast vote
        vote_data = {
            'candidate': [candidate.user_id]
        }
        response = self.client.post(reverse('cast_vote'), vote_data)
        self.assertEqual(response.status_code, 302)  # Assuming a redirect on success

        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        # 4. Verify final state
        # vote_count = Vote.objects.filter(candidate=candidate).count()
        # self.assertEqual(vote_count, 1)

# class AnnouncementIntegrationTest(TransactionTestCase):
#     reset_sequences = True
#     def setUp(self):
#         # Create admin profile
#         self.admin_role = Profile.objects.create(profile_name='Admin', description="Admin Profile")

#         # Create an admin user
#         self.admin_user = UserAccount.objects.create(
#             username="john_doe",
#             password=make_password("password123"),
#             full_name="John Doe",
#             date_of_birth="1990-01-01",
#             role=self.admin_role
#         )
        
#     def test_admin_create_announcement_and_general_user_view(self):
#         # Admin logs in
#         response = self.client.post(reverse('login'), {'username': 'john_doe', 'password': 'password123'})
#         self.assertRedirects(response, reverse('admin_home'))
        
#         # Admin creates an announcement
#         announcement_data = {
#             'header': 'Test Announcement',
#             'content': 'This is a test announcement content.'
#         }
#         create_response = self.client.post(reverse('create_announcement'), announcement_data)
#         self.assertEqual(create_response.status_code, 302)
        
#         # Verify the announcement was created
#         self.assertEqual(Announcement.objects.count(), 1)
#         announcement = Announcement.objects.first()
#         self.assertEqual(announcement.header, 'Test Announcement')
        
#         # Admin logs out
#         response = self.client.get(reverse('logout'))
#         self.assertRedirects(response, reverse('login'))
        
#         # Regular user views the announcements
#         view_response = self.client.get(reverse('view_all_announcements'))
#         self.assertEqual(view_response.status_code, 200)
        
#         # Check if the announcement is in the response content
#         self.assertContains(view_response, 'Test Announcement')
#         self.assertContains(view_response, 'This is a test announcement content.')

# class ElectionPhaseIntegrationTest(TransactionTestCase):
#     reset_sequences = True

#     def setUp(self):
#         # Create roles
#         self.admin_role = Profile.objects.create(profile_name='Admin', description="Admin Profile")
#         self.candidate_role = Profile.objects.create(profile_name='Candidate', description="Candidate Profile")

#         # Create district
#         self.district = District.objects.create(district_name="Central District", num_of_people=10)

#         # Create party
#         self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")

#         # Create election phase
#         self.campaigning_day = ElectionPhase.objects.create(phase_name='Campaigning Day', is_active=False)
#         self.cooling_off_day = ElectionPhase.objects.create(phase_name='Cooling Off Day', is_active=False)
#         self.polling_day = ElectionPhase.objects.create(phase_name='Polling Day', is_active=False)

#         # Create Singpass data
#         self.singpass_user = SingpassUser.objects.create(
#             singpass_id="SP001",
#             password=make_password("password123"),
#             full_name="Bruce Wayne",
#             date_of_birth="1990-01-01",
#             phone_num="12345678",
#             district="Central District"
#         )

#         # Create users 
#         self.admin_user = UserAccount.objects.create(
#             username="john_doe",
#             password=make_password("password123"),
#             full_name="John Doe",
#             date_of_birth="1990-01-01",
#             role=self.admin_role
#         )

#         self.candidate_user = UserAccount.objects.create(
#             username="mary_james",
#             password=make_password("password123"),
#             full_name="Marry James",
#             date_of_birth="1960-01-01",
#             role=self.candidate_role,
#             district=self.district,
#             party=self.party
#         )

#         self.voter_user = Voter.objects.create(
#             district=self.district,
#             pkv="pkv1234",
#             last_login=timezone.now()
#         )

#         # Create candidate profile
#         self.candidate_profile = CandidateProfile.objects.create(
#             candidate=self.candidate_user
#         )

#     def test_election_phase_changes(self):
#         # Admin logs in
#         response = self.client.post(reverse('login'), {'username': 'john_doe', 'password': 'password123'})
#         self.assertRedirects(response, reverse('admin_home'))

#         # Activate Campaigning Day phase
#         response = self.client.get(reverse('activate_election_phase', args=[self.campaigning_day.phase_id]))
#         self.assertEqual(response.status_code, 302)
        
#         # Check if delete district button is enabled for admin in Campaigning Day phase
#         response = self.client.get(reverse('view_district'))
#         self.assertContains(response, '<button type="submit" class="btn btn-danger ">Delete</button>')
#         self.assertNotContains(response, '<button type="submit" class="btn btn-danger btn-disabled"disabled>Delete</button>')

#         # Admin logs out
#         response = self.client.get(reverse('logout'))
#         self.assertRedirects(response, reverse('login'))

#         # Voter logs in
#         response = self.client.post(reverse('singpass_login'), {
#             'singpass_id': 'SP001',
#             'password': 'password123'
#         })
#         self.assertRedirects(response, reverse('voter_home'))

#         # Check if vote button is disabled for voter in Campaigning Day phase
#         response = self.client.get(reverse('voter_home'))
#         self.assertContains(response, '<button disabled>Vote</button>')

#         # Voter logs out
#         response = self.client.get(reverse('logout'))
#         self.assertRedirects(response, reverse('login'))
        
#         # Admin logs in
#         response = self.client.post(reverse('login'), {'username': 'john_doe', 'password': 'password123'})
#         self.assertRedirects(response, reverse('admin_home'))

#         # Admin changes phase to Polling Day
#         response = self.client.get(reverse('activate_election_phase', args=[self.polling_day.phase_id]))
#         self.assertEqual(response.status_code, 302)  # Expect a redirect

#         # Check if delete button is now disabled for admin
#         response = self.client.get(reverse('view_district'))
#         self.assertContains(response, '<button type="submit" class="btn btn-danger btn-disabled"disabled>Delete</button>')

#         # Admin logs out
#         response = self.client.get(reverse('logout'))
#         self.assertRedirects(response, reverse('login'))

#         # Voter logs in
#         response = self.client.post(reverse('singpass_login'), {
#             'singpass_id': 'SP001',
#             'password': 'password123'
#         })
#         self.assertRedirects(response, reverse('voter_home'))

#         # Check if vote button is now enabled for voter
#         response = self.client.get(reverse('voter_home'))
#         self.assertContains(response, '<button >Vote</button>')
#         self.assertNotContains(response, '<button disabled>Vote</button>')

#         # Voter logs out
#         response = self.client.get(reverse('logout'))
#         self.assertRedirects(response, reverse('login'))
        
#         # Candidate logs in
#         response = self.client.post(reverse('login'), {'username': 'mary_james', 'password': 'password123'})
#         self.assertRedirects(response, reverse('candidate_home'))

#         # Check if upload button is now disabled for candidate
#         response = self.client.get(reverse('candidate_home'))
#         self.assertNotContains(response, '<button class="edit-icon btn')

#         # Update candidate statement
#         statement_data = {
#             'candidate_statement': 'This is my campaign promise 123.'
#         }
#         response = self.client.post(reverse('upload_candidate_statement'), statement_data)
#         self.assertEqual(response.status_code, 302)

#         # Check for the error message
#         messages = list(get_messages(response.wsgi_request))
#         self.assertTrue(any(message.message == 'You do not have permission to upload the candidate statement at this time.' for message in messages))
