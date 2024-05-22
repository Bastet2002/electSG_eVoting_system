from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import createNewUser
from .forms import addDistrict
from .forms import editDistrict
from .forms import createAnnouncement
from .forms import createProfile
from .models import UserAccount
from .models import District
from .models import ElectionPhase


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

#---------------------------------------UserAccount views------------------------------------------------
def create(request):
    if request.method == 'POST':
        form = createNewUser(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.save()
            return render(request, "userAccount/createUserAcc.html", {"form": createNewUser(), "success": True})
            #return redirect('create')
        else:
            print(form.errors)  #using this to debug
            return render(request, "userAccount/createUserAcc.html", {"form": form, "success": False})
    else:
        form = createNewUser()
    #return render(request, "userAccount/createUserAcc.html", {"form": form})
    return render(request, "userAccount/createUserAcc.html", {"form": form, "success": False})

def view_user_accounts(request):
    users = UserAccount.objects.all()
    return render(request, 'userAccount/viewUserAcc.html', {'users': users})

def edit_user(request, user_id):
    user = get_object_or_404(UserAccount, pk=user_id)
    if request.method == 'POST':
        form = createNewUser(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('view_user_accounts')
    else:
        form = createNewUser(instance=user)
    return render(request, 'userAccount/updateUserAcc.html',{'form': form})

def delete_user(request, user_id):
    user = get_object_or_404(UserAccount, pk=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('view_user_accounts')
    return HttpResponse(status=405)

#----------------------------------------------------------------------------------------------------------
#---------------------------------------Election phase views------------------------------------------------
def activate_election_phase(request, phase_id):
    ElectionPhase.objects.update(is_active=False)  # Set all phases to inactive
    phase = ElectionPhase.objects.get(id=phase_id)
    phase.is_active = True
    phase.save()
    return redirect('list_election_phases')

def list_election_phases(request):
    phases = ElectionPhase.objects.all()
    return render(request, 'electionPhase/listPhases.html', {'phases': phases})

#----------------------------------------------------------------------------------------------------------
#---------------------------------------District views------------------------------------------------
def add_district(request):
    success = False
    if request.method == 'POST':
        form = addDistrict(request.POST)
        if form.is_valid():
            district_names = form.cleaned_data['district_names']
            district_list = [name.strip() for name in district_names.split(';') if name.strip()]
            
            for name in district_list:
                District.objects.get_or_create(name=name)

            success = True
            return render(request, 'district/addDistrict.html', {'form': addDistrict(), "success": True})
    else:
        form = addDistrict()
    
    return render(request, 'district/addDistrict.html', {'form': form, "success" : False})

def view_district(request):
    district = District.objects.all()
    return render(request, 'district/viewDistrict.html', {'district': district})

def edit_district(request, district_id):
    district = get_object_or_404(District, id=district_id)
    if request.method == 'POST':
        form = editDistrict(request.POST, instance=district)
        if form.is_valid():
            form.save()
            return redirect('view_district')
    else:
        form = editDistrict(instance=district)

    return render(request, 'district/editDistrict.html', {'form': form, 'district': district})

def delete_district(request, district_id):
    district = get_object_or_404(District, pk=district_id)
    if request.method == 'POST':
        district.delete()
        return redirect('view_district')
    return render(request, 'district/deleteDistrict.html', {'district': district})
#----------------------------------------------------------------------------------------------------------


def create_profile(response):
    form = createProfile()

    return render(response, "userProfile/createProfile.html",{"form":form})

def create_announcement(response):
    form = createAnnouncement()

    return render(response, "announcement/createAnnouncement.html",{"form":form})

# def view_user_accounts(request):
#     # Mock data for user accounts
#     users = [
#         {'name': 'Alice', 'date_of_birth': '1990-01-01', 'user_id': 1, 'district': 'Yio Chu Kang', 'role': 'Admin'},
#         {'name': 'Bob', 'date_of_birth': '1992-02-02', 'user_id': 2, 'district': 'Ang Mo Kio', 'role': 'User'},
#         {'name': 'Charlie', 'date_of_birth': '1988-03-03', 'user_id': 3, 'district': 'Bishan', 'role': 'Candidate'},
#     ]
#     return render(request, 'viewUserAcc.html', {'users': users})



