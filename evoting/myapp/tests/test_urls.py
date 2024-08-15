from django.test import SimpleTestCase
from django.urls import reverse, resolve
from myapp import views

class TestUrls(SimpleTestCase):
    def test_login_url(self):
        url = reverse('login')
        self.assertEquals(resolve(url).func, views.user_login)

    def test_logout_url(self):
        url = reverse('logout')
        self.assertEquals(resolve(url).func, views.user_logout)

    def test_change_password_url(self):
        url = reverse('change_password')
        self.assertEquals(resolve(url).func, views.change_password)

    def test_first_login_password_change_url(self):
        url = reverse('first_login_password_change')
        self.assertEquals(resolve(url).func, views.first_login_password_change)
        
    def test_admin_home_url(self):
        url = reverse('admin_home')
        self.assertEquals(resolve(url).func, views.admin_home)

    def test_create_profile_url(self):
        url = reverse('create_profile')
        self.assertEquals(resolve(url).func, views.create_profile)

    def test_view_profiles_url(self):
        url = reverse('view_profiles')
        self.assertEquals(resolve(url).func, views.view_profiles)

    def test_edit_profile_url(self):
        url = reverse('edit_profile', args=[1])
        self.assertEquals(resolve(url).func, views.edit_profile)

    def test_delete_profile_url(self):
        url = reverse('delete_profile', args=[1])
        self.assertEquals(resolve(url).func, views.delete_profile)

    def test_create_district_url(self):
        url = reverse('create_district')
        self.assertEquals(resolve(url).func, views.create_district)

    def test_view_district_url(self):
        url = reverse('view_districts')
        self.assertEquals(resolve(url).func, views.view_districts)

    def test_edit_district_url(self):
        url = reverse('edit_district', args=[1])
        self.assertEquals(resolve(url).func, views.edit_district)

    def test_delete_district_url(self):
        url = reverse('delete_district', args=[1])
        self.assertEquals(resolve(url).func, views.delete_district)

    def test_view_announcement_url(self):
        url = reverse('view_announcements')
        self.assertEquals(resolve(url).func, views.view_announcements)

    def test_view_announcement_detail_url(self):
        url = reverse('view_announcement_detail', args=[1])
        self.assertEquals(resolve(url).func, views.view_announcement_detail)

    def test_create_announcement_url(self):
        url = reverse('create_announcement')
        self.assertEquals(resolve(url).func, views.create_announcement)

    def test_edit_announcement_url(self):
        url = reverse('edit_announcement', args=[1])
        self.assertEquals(resolve(url).func, views.edit_announcement)

    def test_delete_announcement_url(self):
        url = reverse('delete_announcement', args=[1])
        self.assertEquals(resolve(url).func, views.delete_announcement)

    def test_view_party_url(self):
        url = reverse('view_parties')
        self.assertEquals(resolve(url).func, views.view_parties)

    def test_create_party_url(self):
        url = reverse('create_party')
        self.assertEquals(resolve(url).func, views.create_party)

    def test_edit_party_url(self):
        url = reverse('edit_party', args=[1])
        self.assertEquals(resolve(url).func, views.edit_party)

    def test_delete_party_url(self):
        url = reverse('delete_party', args=[1])
        self.assertEquals(resolve(url).func, views.delete_party)

    def test_login_url(self):
        url = reverse('login')
        self.assertEquals(resolve(url).func, views.user_login)

    def test_view_user_accounts_url(self):
        url = reverse('view_accounts')
        self.assertEquals(resolve(url).func, views.view_accounts)

    def test_edit_user_url(self):
        url = reverse('edit_account', args=[1])
        self.assertEquals(resolve(url).func, views.edit_account)

    def test_delete_user_url(self):
        url = reverse('delete_account', args=[1])
        self.assertEquals(resolve(url).func, views.delete_account)

    def test_create_account_url(self):
        url = reverse('create_account')
        self.assertEquals(resolve(url).func, views.create_account)

    def test_list_election_phases_url(self):
        url = reverse('view_election_phases')
        self.assertEquals(resolve(url).func, views.list_election_phases)

    def test_activate_election_phase_url(self):
        url = reverse('activate_election_phase', args=[1])
        self.assertEquals(resolve(url).func, views.activate_election_phase)

    def test_singpass_login_url(self):
        url = reverse('singpass_login')
        self.assertEquals(resolve(url).func, views.singpass_login)

    def test_voter_home_url(self):
        url = reverse('voter_home')
        self.assertEquals(resolve(url).func, views.voter_home)

    def test_ballot_paper_url(self):
        url = reverse('ballot_paper')
        self.assertEquals(resolve(url).func, views.ballot_paper)

    def test_view_candidate_url(self):
        url = reverse('view_candidate', args=[1])
        self.assertEquals(resolve(url).func, views.candidate_home)

    def test_cast_vote_url(self):
        url = reverse('cast_vote')
        self.assertEquals(resolve(url).func, views.cast_vote)

    def test_candidate_home_url(self):
        url = reverse('candidate_home')
        self.assertEquals(resolve(url).func, views.candidate_home)

    def test_upload_election_poster_url(self):
        url = reverse('upload_election_poster')
        self.assertEquals(resolve(url).func, views.upload_election_poster)

    def test_upload_profile_picture_url(self):
        url = reverse('upload_profile_picture')
        self.assertEquals(resolve(url).func, views.upload_profile_picture)

    def test_upload_candidate_statement_url(self):
        url = reverse('upload_candidate_statement')
        self.assertEquals(resolve(url).func, views.upload_candidate_statement)

    def test_general_user_home_url(self):
        url = reverse('general_user_home')
        self.assertEquals(resolve(url).func, views.general_user_home)

    def test_view_all_announcements_url(self):
        url = reverse('view_all_announcements')
        self.assertEquals(resolve(url).func, views.view_announcements)

    def test_webauthn_register_options_url(self):
        url = reverse('webauthn_register_options')
        self.assertEquals(resolve(url).func, views.webauthn_register_options)

    def test_webauthn_register_verify_url(self):
        url = reverse('webauthn_register_verify')
        self.assertEquals(resolve(url).func, views.webauthn_register_verify)

    def test_webauthn_login_options_url(self):
        url = reverse('webauthn_login_options')
        self.assertEquals(resolve(url).func, views.webauthn_login_options)

    def test_webauthn_login_verify_url(self):
        url = reverse('webauthn_login_verify')
        self.assertEquals(resolve(url).func, views.webauthn_login_verify)

    def test_webauthn_verify_view_url(self):
        url = reverse('webauthn_verify')
        self.assertEquals(resolve(url).func, views.webauthn_verify_view)

    def test_delete_all_credentials_url(self):
        url = reverse('delete_all_credentials', args=[1])
        self.assertEquals(resolve(url).func, views.delete_all_credentials)

    def test_delete_my_credentials_url(self):
        url = reverse('delete_my_credentials')
        self.assertEquals(resolve(url).func, views.delete_my_credentials)

    def test_delete_non_master_credentials_url(self):
        url = reverse('delete_non_master_credentials')
        self.assertEquals(resolve(url).func, views.delete_non_master_credentials)

    def test_my_account_url(self):
        url = reverse('my_account')
        self.assertEquals(resolve(url).func, views.my_account)

    def test_check_current_password_url(self):
        url = reverse('check_current_password')
        self.assertEquals(resolve(url).func, views.check_current_password)
