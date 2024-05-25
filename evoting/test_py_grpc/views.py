from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

def grpc(response):
    return HttpResponse("Hello, world. You're at the test_py_grpc index.")

    # create the res req here