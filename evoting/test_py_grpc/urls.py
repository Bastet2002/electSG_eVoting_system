from django.urls import path
from . import views

urlpatterns = [
    path("grpc/", views.grpc, name="grpc"),
]
