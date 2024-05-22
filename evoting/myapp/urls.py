from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("base/", views.base, name="base"),
    path("create/", views.create, name="create"),
    path("create_profile", views.create_profile, name="create_profile"),
    path("add_district/", views.add_district,name="add_district"),
    path('view_district/', views.view_district, name='view_district'),
    path('edit_district/<int:district_id>/', views.edit_district, name='edit_district'),
    path('district/delete/<int:district_id>/', views.delete_district, name='delete_district'),
    path("create_announcement", views.create_announcement,name="create-announcement"),
    path('login/', views.user_login, name='login'),
    path('view_user_accounts/', views.view_user_accounts, name='view_user_accounts'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('phases/', views.list_election_phases, name='list_election_phases'),
    path('phases/activate/<int:phase_id>/', views.activate_election_phase, name='activate_election_phase'),
]
