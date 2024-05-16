from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("base/", views.base, name="base"),
    path("create/", views.create, name="create"),
    path("create_profile", views.create_profile, name="create_profile"),
    path("add_district", views.add_district,name="add_district"),
    path("create_announcement", views.create_announcement,name="create-announcement"),
    path('login/', views.user_login, name='login'),
]
