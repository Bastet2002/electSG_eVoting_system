from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("base/", views.base, name="base"),
    path('admin_home/', views.admin_home, name='admin_home'),
    path("create_profile/", views.create_profile, name="create_profile"),
    path('view_profiles/', views.view_profiles, name='view_profiles'),
    path('edit_profile/<int:id>/', views.edit_profile, name='edit_profile'),
    path('delete_profile/<int:id>/', views.delete_profile, name='delete_profile'),
    path("district/create/", views.create_district, name="create_district"),
    path("district/", views.view_district, name="view_district"),
    path("district/edit/<int:district_id>/", views.edit_district, name="edit_district"),
    path("district/delete/<int:district_id>/", views.delete_district, name="delete_district"),
    path('announcement/', views.view_announcement, name='view_announcement'),
    path('announcement/view/<int:id>/', views.view_announcement_detail, name='view_announcement_detail'),
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/edit/<int:id>/', views.edit_announcement, name='edit_announcement'),
    path('announcement/delete/<int:id>/', views.delete_announcement, name='delete_announcement'),
    path('party/', views.view_party, name='view_party'),
    path('party/create/', views.create_party, name='create_party'),
    path('party/edit/<int:id>/', views.edit_party, name='edit_party'),
    path('party/delete/<int:id>/', views.delete_party, name='delete_party'),
    path('login/', views.user_login, name='login'),
    path('account/', views.view_user_accounts, name='view_user_accounts'),
    path('account/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('account/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('account/create/', views.create, name='create'),
    path('phases/', views.list_election_phases, name='list_election_phases'),
    path('phases/activate/<int:phase_id>/', views.activate_election_phase, name='activate_election_phase'),
    path('voter_home/', views.voter_home, name='voter_home'),
    path('ballot_paper/', views.ballot_paper, name='ballot_paper'),
    path('candidate_home/', views.candidate_home, name='candidate_home'),
    # path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # path('candidate_dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    # path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('candidate_home/election_poster', views.upload_election_poster, name='upload_election_poster'),
    path('candidate_home/profile_picture', views.upload_profile_picture, name='upload_profile_picture'),
    path('candidate_home/candidate_statement', views.upload_candidate_statement, name='upload_candidate_statement'),
]
