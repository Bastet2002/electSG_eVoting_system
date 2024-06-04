from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .forms import createNewUser, editUser, createDistrict, editDistrict, createAnnouncement, createParty, CreateProfileForm
from .models import UserAccount, District, ElectionPhase, Announcement, Party, Profile, CandidateProfile


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role.profile_name == 'Admin':
                return redirect('admin_home')
            elif user.role.profile_name == 'Candidate':
                return redirect('candidate_home')
            elif user.role.profile_name == 'Voter':
                return redirect('voter_home')
            return redirect('base')  # Redirect to home page after successful login
        else:
            print("here")
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    else:
        return render(request, 'login.html')
    
    
def index(response):
    return HttpResponse("<h1>Hello World!</h1>")


def base(response):
    return render(response, "adminDashboard/base.html", {})

def admin_home(request):
    active_phase = ElectionPhase.objects.filter(is_active=True).first()
    announcements = Announcement.objects.all().order_by('-date')  # Order by date in descending order
    return render(request, 'adminDashboard/home.html', {'active_phase': active_phase, 'announcements': announcements})


# ---------------------------------------UserAccount views------------------------------------------------
def create(request):
    if request.method == 'POST':
        form = createNewUser(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            # Hash the password before saving
            password = form.cleaned_data['password']
            new_user.password = make_password(password)
            new_user.save()

            # Check if the created user account is for a candidate
            if new_user.role.profile_name == 'Candidate':
                # Create a CandidateProfile instance for the candidate user
                CandidateProfile.objects.create(user_account=new_user)

            return render(request, "userAccount/createUserAcc.html", {"form": createNewUser(), "success": True})
        else:
            print(form.errors)  # using this to debug
            return render(request, "userAccount/createUserAcc.html", {"form": form, "success": False})
    else:
        form = createNewUser()
    return render(request, "userAccount/createUserAcc.html", {"form": form, "success": False})


def view_user_accounts(request):
    query = request.GET.get('search', '')  # Retrieves the search keyword from the GET request
    if query:
        # Filter users where the search query matches any of the desired fields
        users = UserAccount.objects.filter(
            Q(name__icontains=query) |
            Q(username__icontains=query) |
            Q(district__name__icontains=query) |
            Q(party__party__icontains=query) |  # Assuming 'party' field references a related Party model
            Q(role__icontains=query)
        )
    else:
        users = UserAccount.objects.all()

    return render(request, 'userAccount/viewUserAcc.html', {'users': users})


def edit_user(request, user_id):
    user = get_object_or_404(UserAccount, pk=user_id)
    if request.method == 'POST':
        form = editUser(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('view_user_accounts')
    else:
        form = editUser(instance=user)
    return render(request, 'userAccount/updateUserAcc.html', {'form': form})


def delete_user(request, user_id):
    user = get_object_or_404(UserAccount, pk=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('view_user_accounts')
    return HttpResponse(status=405)


# ---------------------------------------Election phase views------------------------------------------------
def activate_election_phase(request, phase_id):
    ElectionPhase.objects.update(is_active=False)  # Set all phases to inactive
    phase = ElectionPhase.objects.get(id=phase_id)
    phase.is_active = True
    phase.save()
    return redirect('list_election_phases')


def list_election_phases(request):
    phases = ElectionPhase.objects.all()
    return render(request, 'electionPhase/listPhases.html', {'phases': phases})


# ---------------------------------------District views-----------------------------------------------------
def create_district(request):
   
    if request.method == 'POST':
        form = createDistrict(request.POST)
        if form.is_valid():
            district_names = form.cleaned_data['district_names']
            district_list = [name.strip() for name in district_names.split(';') if name.strip()]

            for name in district_list:
                District.objects.get_or_create(name=name)

            
            return render(request, 'district/createDistrict.html', {'form': createDistrict(), "success": True})
    else:
        form = createDistrict()

    return render(request, 'district/createDistrict.html', {'form': form, "success": False})


def view_district(request):
    query = request.GET.get('search', '')
    if query:
        # Filter districts where the search query matches the name field
        district = District.objects.filter(name__icontains=query)
    else:
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


# ---------------------------------------Profile view-----------------------------------------------------
def create_profile(request):
    if request.method == 'POST':
        form = CreateProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_profile')
    else:
        form = CreateProfileForm()
    return render(request, 'userProfile/createProfile.html', {'form': form})

def view_profiles(request):
    profiles = Profile.objects.all()
    return render(request, 'userProfile/viewProfiles.html', {'profiles': profiles})

def edit_profile(request, id):
    profile = get_object_or_404(Profile, id=id)
    if request.method == 'POST':
        form = CreateProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('view_profiles')
    else:
        form = CreateProfileForm(instance=profile)
    return render(request, 'userProfile/editProfile.html', {'form': form, 'profile': profile})

def delete_profile(request, id):
    profile = get_object_or_404(Profile, id=id)
    if request.method == 'POST':
        profile.delete()
        return redirect('view_profiles')
    return render(request, 'userProfile/deleteProfile.html', {'profile': profile})


# ---------------------------------------Announcement views------------------------------------------------
def create_announcement(request):
    if request.method == 'POST':
        form = createAnnouncement(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_announcement')
    else:
        form = createAnnouncement()
    return render(request, 'announcement/createAnnouncement.html', {'form': form})


def view_announcement(request):
    announcements = Announcement.objects.all()
    return render(request, 'announcement/viewAnnouncement.html', {'announcements': announcements})


def view_announcement_detail(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    return render(request, 'announcement/viewAnnouncementDetail.html', {'announcement': announcement})


def edit_announcement(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST':
        form = createAnnouncement(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            return redirect('view_announcement')
    else:
        form = createAnnouncement(instance=announcement)
    return render(request, 'announcement/editAnnouncement.html', {'form': form})


def delete_announcement(request, id):
    announcement = get_object_or_404(Announcement, id=id)
    if request.method == 'POST':
        announcement.delete()
        return redirect('view_announcement')
    return render(request, 'announcement/deleteAnnouncement.html', {'announcement': announcement})


# ---------------------------------------Party views------------------------------------------------
def create_party(request):
    if request.method == 'POST':
        form = createParty(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'party/createParty.html', {'form': createParty(), "success": True})
    else:
        form = createParty()
    return render(request, 'party/createParty.html', {'form': form, "success": False})


def view_party(request):
    parties = Party.objects.all()
    return render(request, 'party/viewParty.html', {'parties': parties})


def edit_party(request, id):
    party = get_object_or_404(Party, id=id)
    if request.method == 'POST':
        form = createParty(request.POST, instance=party)
        if form.is_valid():
            form.save()
            return redirect('view_party')
    else:
        form = createParty(instance=party)
    return render(request, 'party/editParty.html', {'form': form})


def delete_party(request, id):
    party = get_object_or_404(Party, id=id)
    if request.method == 'POST':
        party.delete()
        return redirect('view_party')
    return render(request, 'party/deleteParty.html', {'party': party})

# ---------------------------------------Voter views------------------------------------------------

def voter_home(response):
    return render(response, "Voter/voterPg.html", {})

def ballot_paper(response):
    return render(response, "Voter/votingPg.html", {})

# ---------------------------------------Candidate views------------------------------------------------

from .forms import ElectionPosterForm, ProfilePictureForm, CandidateStatementForm
def candidate_home(request):
    candidate_profile = get_object_or_404(CandidateProfile, user_account=request.user)
    
    profile_picture_form = ProfilePictureForm()
    election_poster_form = ElectionPosterForm()
    candidate_statement_form = CandidateStatementForm()
    candidate_statement_form.fields['candidate_statement'].initial = candidate_profile.candidate_statement
    
    return render(request, 'Candidate/candidatePg.html', {
        'profile_picture_form': profile_picture_form,
        'election_poster_form': election_poster_form,
        'candidate_statement_form': candidate_statement_form,
        'candidate_profile': candidate_profile
    })

def upload_election_poster(request):
    if request.method == 'POST':
        form = ElectionPosterForm(request.POST, request.FILES)
        if form.is_valid():
            candidate_profile = get_object_or_404(CandidateProfile, user_account=request.user)
            candidate_profile.election_poster = form.cleaned_data['election_poster']
            candidate_profile.save()
            return redirect('candidate_home')  # Redirect to candidate home page after successful upload
    # else:
    #     form = ElectionPosterForm()
    # return render(request, 'upload_election_poster.html', {'form': form})

def upload_profile_picture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            candidate_profile = get_object_or_404(CandidateProfile, user_account=request.user)
            candidate_profile.profile_picture = form.cleaned_data['profile_picture']
            candidate_profile.save()
            return redirect('candidate_home')  # Redirect to candidate home page after successful upload
    # else:
    #     form = ProfilePictureForm()
    # return render(request, 'upload_profile_picture.html', {'form': form})

def upload_candidate_statement(request):
    if request.method == 'POST':
        form = CandidateStatementForm(request.POST)
        if form.is_valid():
            candidate_profile = get_object_or_404(CandidateProfile, user_account=request.user)
            candidate_profile.candidate_statement = form.cleaned_data['candidate_statement']
            candidate_profile.save()
            return redirect('candidate_home')  # Redirect to candidate home page after successful upload
    # else:
    #     form = CandidateStatementForm()
    # return render(request, 'upload_candidate_statement.html', {'form': form})