from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import createNewUser
from .forms import addDistrict
from .forms import createAnnouncement
from .forms import createProfile
from .models import UserAccount

def view_user_accounts(request):
    users = UserAccount.objects.all()
    return render(request, 'viewUserAcc.html', {'users': users})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home page after successful login
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    else:
        return render(request, 'login.html')

def index(response):
    return HttpResponse("<h1>Hello World!</h1>")

def base(response):
    return render(response, "adminDashboard/base.html",{})

def create(response):
    form = createNewUser()

    return render(response, "userAccount/createUserAcc.html",{"form":form})

def create_profile(response):
    form = createProfile()

    return render(response, "userProfile/createProfile.html",{"form":form})

def add_district(response):
    form = addDistrict()

    return render(response, "district/addDistrict.html",{"form":form})

def create_announcement(response):
    form = createAnnouncement()

    return render(response, "announcement/createAnnouncement.html",{"form":form})

def view_user_accounts(request):
    # Mock data for user accounts
    users = [
        {'name': 'Alice', 'date_of_birth': '1990-01-01', 'user_id': 1, 'district': 'Yio Chu Kang', 'role': 'Admin'},
        {'name': 'Bob', 'date_of_birth': '1992-02-02', 'user_id': 2, 'district': 'Ang Mo Kio', 'role': 'User'},
        {'name': 'Charlie', 'date_of_birth': '1988-03-03', 'user_id': 3, 'district': 'Bishan', 'role': 'Candidate'},
    ]
    return render(request, 'viewUserAcc.html', {'users': users})

