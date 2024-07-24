from django.urls import path
from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path("health/", views.health_check, name="health_check"),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change_password/', views.change_password, name='change_password'),
    path('first_login/', views.first_login_password_change, name='first_login_password_change'),

    # Admin 
    path('admin_home/', views.admin_home, name='admin_home'),
    ## Account
    path('admin_home/create_account/', views.create_account, name='create_account'),
    path('admin_home/create_account/<str:upload_type>/', views.create_account, name='create_account'),
    path('admin_home/view_accounts/', views.view_accounts, name='view_accounts'),
    path('admin_home/edit_account/<int:user_id>/', views.edit_account, name='edit_account'),
    path('admin_home/delete_account/<int:user_id>/', views.delete_account, name='delete_account'),
    ## Profile
    path("admin_home/create_profile/", views.create_profile, name="create_profile"),
    path('admin_home/view_profiles/', views.view_profiles, name='view_profiles'),
    path('admin_home/edit_profile/<int:profile_id>/', views.edit_profile, name='edit_profile'),
    path('admin_home/delete_profile/<int:profile_id>/', views.delete_profile, name='delete_profile'),
    ## District
    path('admin_home/create_district/<str:upload_type>/', views.create_district, name='create_district'),
    path("admin_home/create_district/", views.create_district, name="create_district"),
    path("admin_home/view_districts/", views.view_districts, name="view_districts"),
    path("admin_home/edit_district/<int:district_id>/", views.edit_district, name="edit_district"),
    path("admin_home/delete_district/<int:district_id>/", views.delete_district, name="delete_district"),
    ## Announcement
    path('admin_home/create_announcement/', views.create_announcement, name='create_announcement'),
    path('admin_home/view_announcements/', views.view_announcements, name='view_announcements'),
    path('admin_home/view_announcement/<int:announcement_id>/', views.view_announcement_detail, name='view_announcement_detail'),
    path('admin_home/edit_announcement/<int:announcement_id>/', views.edit_announcement, name='edit_announcement'),
    path('admin_home/delete_announcement/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    ## Party
    path('admin_home/create_party/', views.create_party, name='create_party'),
    path('admin_home/view_parties/', views.view_parties, name='view_parties'),
    path('admin_home/edit_party/<int:party_id>/', views.edit_party, name='edit_party'),
    path('admin_home/delete_party/<int:party_id>/', views.delete_party, name='delete_party'),
    ## Phase
    path('admin_home/view_phases/', views.list_election_phases, name='view_election_phases'),
    path('admin_home/activate_phase/<int:phase_id>/', views.activate_election_phase, name='activate_election_phase'),

    # Candidate
    path('candidate_home/', views.candidate_home, name='candidate_home'),
    path('candidate_home/upload_election_poster', views.upload_election_poster, name='upload_election_poster'),
    path('candidate_home/delete_election_poster/<int:candidate_id>/', views.delete_election_poster, name='delete_election_poster'),
    path('candidate_home/upload_profile_picture', views.upload_profile_picture, name='upload_profile_picture'),
    path('candidate_home/delete_profile_picture/<int:candidate_id>/', views.delete_profile_picture, name='delete_profile_picture'),
    path('candidate_home/upload_candidate_statement', views.upload_candidate_statement, name='upload_candidate_statement'),
    path('candidate_home/delete_candidate_statement/<int:candidate_id>/', views.delete_candidate_statement, name='delete_candidate_statement'),

    # Voter
    path('singpass_login/', views.singpass_login, name='singpass_login'),
    path('voter_home/', views.voter_home, name='voter_home'),
    path('voter_home/ballot_paper/', views.ballot_paper, name='ballot_paper'),
    path('voter_home/view_candidate/<int:candidate_id>/', views.candidate_home, name='view_candidate'),
    path('voter_home/ballot_paper/cast_vote/', views.cast_vote, name='cast_vote'),
    
    # General User
    path('', views.general_user_home, name='general_user_home'),
    path('announcements/', views.view_announcements, name='view_all_announcements'),
    path('districts/', views.view_districts, name='view_all_districts'),
    path('districts/<int:district_id>/', views.view_district_detail, name='view_district_detail'),
    path('ongoing-result/<int:district_id>/', views.get_ongoing_result, name='ongoing_result'),

    # Web Authentication
    path('webauthn/register/', views.webauthn_register_view, name='webauthn_register_view'),
    path('webauthn/register/options/', views.webauthn_register_options, name='webauthn_register_options'),
    path('webauthn/register/verify/', views.webauthn_register_verify, name='webauthn_register_verify'),
    path('webauthn/login/', views.webauthn_login_view, name='webauthn_login_view'),
    path('webauthn/login/options/', views.webauthn_login_options, name='webauthn_login_options'),
    path('webauthn/login/verify/', views.webauthn_login_verify, name='webauthn_login_verify'),
    path('webauthn/verify/', views.webauthn_verify_view, name='webauthn_verify'),
    path('delete-all-credentials/<int:user_id>/', views.delete_all_credentials, name='delete_all_credentials'),
    path('delete-all-credentials-temp/', views.delete_all_credentials_temp, name='delete_all_credentials_temp'),
    path('my_account/', views.my_account, name='my_account'),
    path('check-current-password/', views.check_current_password, name='check_current_password'),
]
