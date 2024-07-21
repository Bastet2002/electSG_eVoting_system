from django.contrib.auth import authenticate, login, logout, get_backends, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.messages import get_messages
from django.db.models import Q
from django.db.models import Sum
from .forms import CreateNewUser, CSVUploadForm, EditUser, CreateDistrict, EditDistrict, CreateAnnouncement, CreateParty, CreateProfileForm, PasswordChangeForm, FirstLoginPasswordChangeForm
from .models import UserAccount, District, ElectionPhase, Announcement, Party, Profile, CandidateProfile, Voter, VoteResults
from django.db.models import Sum
from django.contrib.auth.hashers import check_password
from .decorators import flexible_access
from django.core.exceptions import ValidationError
import csv, datetime

from pygrpc.ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_construct_vote_request,
    grpc_construct_gen_candidate_request,
    grpc_construct_calculate_total_vote_request,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
    grpc_calculate_total_vote_run,
    GrpcError,
)

User = get_user_model()

@flexible_access('public')
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if the user has registered WebAuthn credentials
            has_webauthn = WebauthnCredentials.objects.filter(user=user).exists()
            
            # Store the user ID in the session for WebAuthn verification
            request.session['pending_user_id'] = user.user_id
            
            return JsonResponse({
                'status': 'success',
                'requires_webauthn': has_webauthn
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=400)
    else:
        return render(request, 'login.html')

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, 'Your password has been successfully changed.')
            backend = get_backends()[0]
            backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
            
            # Log the user in with the specified backend
            login(request, user, backend=backend_path)
            if user.role.profile_name == 'Admin':
                return redirect('admin_home')
            elif user.role.profile_name == 'Candidate':
                return redirect('candidate_home')
            messages.success(request, 'Your password has been set.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'changePassword.html', {'form': form})


def first_login_password_change(request):
    if 'pending_user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(user_id=request.session['pending_user_id'])

    if request.method == 'POST':
        form = FirstLoginPasswordChangeForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.first_login = False
            user.save()

            backend = get_backends()[0]
            backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
            
            # Log the user in with the specified backend
            login(request, user, backend=backend_path)

            # Return a JSON response indicating success and that WebAuthn registration should be initiated
            return JsonResponse({'status': 'success', 'prompt_webauthn': True})
    else:
        form = FirstLoginPasswordChangeForm()

    return render(request, 'firstLogin.html', {'form': form})




@flexible_access('admin', 'candidate', 'voter')
def user_logout(request):
    if request.method == 'GET':
        user_sessions = Session.objects.filter(session_key=request.session.session_key)
        user_sessions.delete()
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return HttpResponseRedirect(reverse('login'))

def index(response):
    return HttpResponse("<h1>Hello World!</h1>")

def base(response):
    return render(response, "adminDashboard/base.html", {})

@flexible_access('admin')
def admin_home(request):
    active_phase = ElectionPhase.objects.filter(is_active=True).first()
    announcements = Announcement.objects.all().order_by('-date')  # Order by date in descending order
    return render(request, 'adminDashboard/home.html', {'active_phase': active_phase, 'announcements': announcements})

# ---------------------------------------UserAccount views------------------------------------------------
# @flexible_access('admin')
# def create_account(request, upload_type=None):
#     if request.method == 'POST':
#         if upload_type == 'csv_upload':
#             form = CSVUploadForm(request.POST, request.FILES)
#             if form.is_valid():
#                 csv_file = request.FILES['csv_file']
#                 decoded_file = csv_file.read().decode('utf-8').splitlines()
#                 reader = csv.DictReader(decoded_file)

#                 for row in reader:
#                     user = UserAccount(
#                         username = row['username'],
#                         full_name = row['full_name'],
#                         password = make_password(row['password']),
#                         date_of_birth = row['date_of_birth'],
#                         role_name = Profile.objects.get(profile_name=row['role']),
#                         district_name = District.objects.get(district_name=row['district']),
#                         party_name = Party.objects.get(party_name=row['party'])
#                     )

#                     user.save()

#                     if user.role.profile_name == 'Candidate':
#                         CandidateProfile.objects.create(candidate=user)
#                         VoteResults.objects.create(candidate=user, total_vote=0)
#                         # Generate user and voting currency via gRPC
#                         try:
#                             grpc_generate_candidate_keys_run(candidate_id=user.user_id)
#                             messages.success(request, 'Account successfully created.')
#                         except GrpcError as grpc_error:
#                             # Handle specific gRPC errors
#                             print(f"Error in gRPC call: {grpc_error}")
#                             messages.error(request, f"Error in creating candidate keys: {grpc_error}")
#                         except Exception as e:
#                             # Handle other unexpected exceptions
#                             print(f"Unexpected error: {e}")
#                             messages.error(request, f"Unexpected error in creating candidate keys: {e}")
#                     else:
#                         messages.success(request, 'Account successfully created.')
#                 messages.success(request, 'Users created successfully')
#                 return redirect('create_account')  # Replace with your actual success URL
#         else:
#             form = CreateNewUser(request.POST)
#             if form.is_valid():
#                 new_user = form.save(commit=False)
#                 # Hash the password before saving
#                 password = form.cleaned_data['password']
#                 new_user.password = make_password(password)
#                 new_user.save()

#                 # Check if the created user account is for a candidate
#                 if new_user.role.profile_name == 'Candidate':
#                     CandidateProfile.objects.create(candidate=new_user)
#                     VoteResults.objects.create(candidate=new_user, total_vote=0)
#                     # Generate user and voting currency via gRPC
#                     try:
#                         grpc_generate_candidate_keys_run(candidate_id=new_user.user_id)
#                         messages.success(request, 'Account successfully created.')
#                     except GrpcError as grpc_error:
#                         # Handle specific gRPC errors
#                         print(f"Error in gRPC call: {grpc_error}")
#                         messages.error(request, f"Error in creating candidate keys: {grpc_error}")
#                     except Exception as e:
#                         # Handle other unexpected exceptions
#                         print(f"Unexpected error: {e}")
#                         messages.error(request, f"Unexpected error in creating candidate keys: {e}")
#                 else:
#                     messages.success(request, 'Account successfully created.')
#                 return redirect('create_account')  # Redirect to clear the form and show the success message
#             else:
#                 messages.error(request, 'Invalid form submission.')
#     else:
#         form = CreateNewUser()
#         csv_form = CSVUploadForm()

#     return render(request, 'userAccount/createUserAcc.html', {'form': form, 'csv_form': csv_form})

@flexible_access('admin')
def create_account(request, upload_type=None):
    if request.method == 'POST':
        if upload_type == 'csv_upload':
            return handle_user_csv_upload(request)
        else:
            return handle_single_user_creation(request)
    else:
        return render(request, 'userAccount/createUserAcc.html', {
            'form': CreateNewUser(),
            'csv_form': CSVUploadForm()
        })
    
def handle_user_csv_upload(request):
    required_fields = ['username', 'full_name', 'date_of_birth', 'password', 'role', 'party', 'district']
    form = CSVUploadForm(request.POST, request.FILES)
    if form.is_valid():
        print("here")
        csv_file = request.FILES['csv_file']
        reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
        # Check if required fields are present
        if not all(field in reader.fieldnames for field in required_fields):
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            messages.error(request, f"Missing fields in CSV: {', '.join(missing_fields)}")
            return redirect('create_account')
        for row in reader:
            date_of_birth = datetime.datetime.strptime(row['date_of_birth'], '%d/%m/%Y').date()
            user = UserAccount(
                    username = row['username'],
                    full_name = row['full_name'],
                    password = make_password(row['password']),
                    date_of_birth = date_of_birth,
                    role = Profile.objects.get(profile_name=row['role']),
                    district = District.objects.get(district_name=row['district']),
                    party = Party.objects.get(party_name=row['party'])
                )
            try:
                user.save()
                create_additional_candidate_data(request, user)
            except ValidationError as e:
                for field, messages_list in e.message_dict.items():
                    for message in messages_list:
                        messages.error(request, f"{field}: {message}")
                return redirect('create_account')
            messages.success(request, 'Users created successfully')
    else:
        messages.error(request, 'Invalid CSV file')
    return redirect('create_account')

def handle_single_user_creation(request):
    form = CreateNewUser(request.POST)
    if form.is_valid():
        user = form.save(commit=False)
        user.password = make_password(form.cleaned_data['password'])
        user.save()
        create_additional_candidate_data(request, user)
        messages.success(request, 'Account successfully created.')
        return redirect('create_account')
    else:
        messages.error(request, 'Invalid form submission.')
        return render(request, 'userAccount/createUserAcc.html', {
            'form': form,
            'csv_form': CSVUploadForm()
        })
    
def create_additional_candidate_data(request, user):
    if user.role.profile_name == 'Candidate':
        CandidateProfile.objects.create(candidate=user)
        VoteResults.objects.create(candidate=user, total_vote=0)
        try:
            grpc_generate_candidate_keys_run(candidate_id=user.user_id)
        except GrpcError as grpc_error:
            messages.error(request, f"Error in creating candidate keys: {grpc_error}")
        except Exception as e:
            messages.error(request, f"Unexpected error in creating candidate keys: {e}")

@flexible_access('admin')
def view_accounts(request):
    query = request.GET.get('search', '')  # Retrieves the search keyword from the GET request
    if query:
        # Filter users where the search query matches any of the desired fields
        users = UserAccount.objects.filter(
            Q(full_name__icontains=query) |
            Q(username__icontains=query) |
            Q(district__district_name__icontains=query) |
            Q(party__party_name__icontains=query) |  # Assuming 'party' field references a related Party model
            Q(role__profile_name__icontains=query) #### add this to search
        )
    else:
        users = UserAccount.objects.all()

    return render(request, 'userAccount/viewUserAcc.html', {'users': users})

@flexible_access('admin')
def edit_account(request, user_id):
    user = get_object_or_404(UserAccount, pk=user_id)
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if request.method == 'POST':
        form = EditUser(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account successfully updated.')
            return redirect('view_user_accounts')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = EditUser(instance=user)
    return render(request, 'userAccount/updateUserAcc.html', {'form': form, 'current_phase': current_phase, 'user': user})

@flexible_access('admin')
def delete_account(request, user_id):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
        messages.error(request, 'You do not have permission to delete the account at this time.')
        return redirect('view_user_accounts')
    
    user = get_object_or_404(UserAccount, pk=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('view_user_accounts')
    return HttpResponse(status=405)

# ---------------------------------------Election phase views------------------------------------------------
@flexible_access('admin')
def activate_election_phase(request, phase_id):
    ElectionPhase.objects.update(is_active=False)  # Set all phases to inactive
    phase = ElectionPhase.objects.get(pk=phase_id)
    phase.is_active = True
    phase.save()
    return redirect('list_election_phases')

@flexible_access('admin')
def list_election_phases(request):
    phases = ElectionPhase.objects.all()
    return render(request, 'electionPhase/listPhases.html', {'phases': phases})

# ---------------------------------------District views-----------------------------------------------------
# @flexible_access('admin')
# def create_district(request):
#     if request.method == 'POST':
#         form = CreateDistrict(request.POST)
#         if form.is_valid():
#             district_names = form.cleaned_data['district_names']
#             district_list = [name.strip().upper() for name in district_names.split(';') if name.strip()]

#             for name in district_list:
#                 district, created = District.objects.get_or_create(district_name=name)
#                 if created:
#                     try:
#                         grpc_generate_user_and_votingcurr_run(district_id=district.district_id, voter_num=20)
#                     except GrpcError as grpc_error:
#                         # Handle gRPC errors
#                         print(f"Error in gRPC call: {grpc_error}")
#                         messages.error(request, f"Error in gRPC call: {grpc_error}")
#                     except Exception as e:
#                         # Handle other exceptions
#                         print(f"Unexpected error: {e}")
#                         messages.error(request, f"Error: {e}")

#             messages.success(request, 'District(s) successfully created.')
#             return redirect('create_district')  # Redirect to clear the form and show the success message
#         else:
#             messages.error(request, 'Invalid form submission.')
#     else:
#         form = CreateDistrict()

#     return render(request, 'district/createDistrict.html', {'form': form})

@flexible_access('admin')
def create_district(request, upload_type=None):
    if request.method == 'POST':
        # csv_form = CSVUploadForm(request.POST, request.FILES)
        # form = CreateDistrict(request.POST)
        if upload_type == 'csv_upload':
            return handle_district_csv_upload(request)
        else:
            return handle_single_district_creation(request)
    else:
        return render(request, 'district/createDistrict.html', {
            'form': CreateDistrict(),
            'csv_form': CSVUploadForm()
        })
    
def handle_district_csv_upload(request):
    required_fields = ['district_name', 'num_of_people']
    form = CSVUploadForm(request.POST, request.FILES)
    if form.is_valid():
        csv_file = request.FILES['csv_file']
        reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
        # Check if required fields are present
        if not all(field in reader.fieldnames for field in required_fields):
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            messages.error(request, f"Missing fields in CSV: {', '.join(missing_fields)}")
            return redirect('create_district')
        for row in reader:
            district = District(
                district_name=row['district_name'],
                num_of_people=row['num_of_people']
            )
            try:
                district.save()
                create_additional_voter_data(request, district)
                
            except ValidationError as e:
                for field, messages_list in e.message_dict.items():
                    for message in messages_list:
                        messages.error(request, f"{field}: {message}")
                return redirect('create_district')
            messages.success(request, 'Distticts created successfully')
    else:
        messages.error(request, 'Invalid CSV file')
    return redirect('create_district')

def handle_single_district_creation(request):
    form = CreateDistrict(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'District successfully created.')
        return redirect('create_district')
    else:
        messages.error(request, 'Invalid form submission.')
        return render(request, 'district/createDistrict.html', {
            'form': form,
            'csv_form': CSVUploadForm()
        })

def create_additional_voter_data(request, district):
    try:
        grpc_generate_user_and_votingcurr_run(district_id=district.district_id, voter_num=district.num_of_people)
    except GrpcError as grpc_error:
        messages.error(request, f"Error in gRPC call: {grpc_error}")
    except Exception as e:
        messages.error(request, f"Error: {e}")

@flexible_access('public', 'admin')
def view_district(request):
    query = request.GET.get('search', '')
    if query:
        # Filter districts where the search query matches the name field
        districts = District.objects.filter(district_name__icontains=query)
    else:
        districts = District.objects.all()

    if isinstance(request.user, UserAccount):
        if request.user.role.profile_name.lower() == 'admin':
            current_phase = ElectionPhase.objects.filter(is_active=True).first()
            disable_deletion = current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']

            return render(request, 'district/viewDistrict.html', {'districts': districts, 'disable_deletion': disable_deletion})
    # for general user
    # if not request.user.is_authenticated:
    return render(request, 'generalUser/viewAllDistricts.html', {'districts': districts})
    
@flexible_access('admin')
def edit_district(request, district_id):
    district = get_object_or_404(District, pk=district_id)
    if request.method == 'POST':
        form = EditDistrict(request.POST, instance=district)
        if form.is_valid():
            form.save()
            messages.success(request, 'District successfully updated.')
            return redirect('view_district')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = EditDistrict(instance=district)

    return render(request, 'district/editDistrict.html', {'form': form, 'district': district})

@flexible_access('admin')
def delete_district(request, district_id):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
        messages.error(request, 'You do not have permission to delete the district at this time.')
        return redirect('candidate_home')
    
    district = get_object_or_404(District, pk=district_id)
    if request.method == 'POST':
        district.delete()
        messages.success(request, 'District successfully deleted.')
        return redirect('view_district')
    else:
        messages.error(request, 'Error deleting district.')
        return redirect('view_district')

# ---------------------------------------Profile view-----------------------------------------------------
@flexible_access('admin')
def create_profile(request):
    if request.method == 'POST':
        form = CreateProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile successfully created.')
            return redirect('create_profile')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateProfileForm()
    return render(request, 'userProfile/createProfile.html', {'form': form})

@flexible_access('admin')
def view_profiles(request):
    profiles = Profile.objects.all()
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    disable_deletion = current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']
    not_allow = ['Admin', 'Candidate']

    return render(request, 'userProfile/viewProfiles.html', {'profiles': profiles, 'disable_deletion': disable_deletion, "disable_edit_list": not_allow})

@flexible_access('admin')
def edit_profile(request, profile_id):
    profile = get_object_or_404(Profile, pk=profile_id)
    if request.method == 'POST':
        form = CreateProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile successfully updated.')
            return redirect('view_profiles')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateProfileForm(instance=profile)
    return render(request, 'userProfile/editProfile.html', {'form': form, 'profile': profile})

@flexible_access('admin')
def delete_profile(request, profile_id):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
        messages.error(request, 'You do not have permission to delete the profile at this time.')
        return redirect('view_profiles')
    
    profile = get_object_or_404(Profile, pk=profile_id)
    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Profile successfully deleted.')
        return redirect('view_profiles')
    else:
        messages.error(request, 'Error deleting profile.')
        return redirect('view_profiles')

# ---------------------------------------Announcement views------------------------------------------------
@flexible_access('admin')
def create_announcement(request):
    if request.method == 'POST':
        form = CreateAnnouncement(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement successfully created.')
            return redirect('create_announcement')
    else:
        form = CreateAnnouncement()
    return render(request, 'announcement/createAnnouncement.html', {'form': form})

@flexible_access('public', 'admin')
def view_announcement(request):
    announcements = Announcement.objects.all()
    if not request.user.is_authenticated:
        return render(request, 'generalUser/viewAllAnnouncements.html', {'announcements': announcements})
    else:
        return render(request, 'announcement/viewAnnouncement.html', {'announcements': announcements})

@flexible_access('admin')
def view_announcement_detail(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    return render(request, 'announcement/viewAnnouncementDetail.html', {'announcement': announcement})

@flexible_access('admin')
def edit_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    if request.method == 'POST':
        form = CreateAnnouncement(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement successfully updated.')
            return redirect('view_announcement')
    else:
        form = CreateAnnouncement(instance=announcement)
    return render(request, 'announcement/editAnnouncement.html', {'form': form, 'announcement': announcement})

@flexible_access('admin')
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement successfully deleted.')
        return redirect('view_announcement')
    else:
        messages.error(request, 'Error deleting announcement.')
        return redirect('view_announcement')

# ---------------------------------------Party views------------------------------------------------
@flexible_access('admin')
def create_party(request):
    if request.method == 'POST':
        form = CreateParty(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party successfully created.')
            return redirect('create_party')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateParty()
    return render(request, 'party/createParty.html', {'form': form})

@flexible_access('admin')
def view_party(request):
    parties = Party.objects.all()
    return render(request, 'party/viewParty.html', {'parties': parties})

@flexible_access('admin')
def edit_party(request, party_id):
    party = get_object_or_404(Party, pk=party_id)
    if request.method == 'POST':
        form = CreateParty(request.POST, instance=party)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party successfully updated.')
            return redirect('view_party')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateParty(instance=party)
    return render(request, 'party/editParty.html', {'form': form})

@flexible_access('admin')
def delete_party(request, party_id):
    party = get_object_or_404(Party, pk=party_id)
    if request.method == 'POST':
        party.delete()
        messages.success(request, 'Party successfully deleted.')
        return redirect('view_party')
    else:
        messages.error(request, 'Error deleting party.')
        return redirect('view_party')

# ---------------------------------------Voter views------------------------------------------------
@flexible_access('public')
def singpass_login(request):
    if request.method == 'POST':
        # auth_backend = SingpassBackend()
        singpass_id = request.POST['singpass_id']
        password = request.POST['password']
        user = authenticate(request, singpass_id=singpass_id, password=password)
        if user is not None:
            # user.backend = 'myapp.auth_backends.SingpassBackend'
            login(request, user)
            return redirect('voter_home') 
        else:
            return render(request, 'singpassLogin.html', {'error': 'Invalid username or password.'})
    else:
        return render(request, 'singpassLogin.html')

@flexible_access('voter')
def voter_home(request):
    if isinstance(request.user, Voter):
        voter = request.user
    else:
        messages.error(request, 'Error: Only voters can access this page.')
        return redirect('login')

    district_id = voter.district.district_id if voter.district else None

    if not district_id:
        messages.error(request, 'Error: Voter does not belong to a district.')
        return redirect('login')

    candidates = CandidateProfile.objects.filter(candidate__district_id=district_id).select_related('candidate', 'candidate__party')
    user_district = voter.district.district_name if voter.district else "No District"
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    disable_vote = current_phase and current_phase.phase_name not in ['Polling Day']
    list(messages.get_messages(request))
    return render(request, 'Voter/voterPg.html', {
        'candidates': candidates,
        'user_district': user_district,
        'disable_vote': disable_vote
        #'voting_status':...
    })

@flexible_access('voter')
def ballot_paper(request):
    list(messages.get_messages(request))
    if not isinstance(request.user, Voter):
        messages.error(request, 'Error: Only voters can view the ballot paper.')
        return redirect('login')

    voter = request.user
    district_id = voter.district.district_id if voter.district else None

    if not district_id:
        messages.error(request, 'Error: Voter does not belong to a district.')
        return redirect('login')

    candidates = CandidateProfile.objects.filter(candidate__district_id=district_id).select_related('candidate', 'candidate__party')
    
    # Also ensure session messages are cleared
    if 'messages' in request.session:
        del request.session['messages']
    request.session.modified = True

    return render(request, 'Voter/votingPg.html', {'candidates': candidates})

@flexible_access('voter')
def cast_vote(request):
    if request.method == 'POST':
        selected_candidates = request.POST.getlist('candidate')
        
        if isinstance(request.user, Voter):
            voter = request.user
        else:
            messages.error(request, 'Error: Only voters can cast votes.')
            return redirect('voter_home')
        
        district_id = voter.district.district_id if voter.district else None

        if not district_id:
            messages.error(request, 'Error: Voter does not belong to a district.')
            return redirect('voter_home')

        double_voting_detected = False  # Flag to check if double voting error occurred

        for candidate_id in selected_candidates:
            try:
                grpc_compute_vote_run(candidate_id=int(candidate_id), voter_id=voter.voter_id)
                
                vote_result = get_object_or_404(VoteResults, candidate_id=candidate_id)
                if vote_result:
                    vote_result.total_vote += 1
                    vote_result.save()

            except GrpcError as e:
                # Check if the error message indicates double voting
                if "CORE_DOUBLE_VOTING" in str(e):
                    double_voting_detected = True
                    messages.error(request, 'Double voting detected. Your vote is invalid.')
                    break  # Exit loop on double voting detection
                else:
                    print(f"Error in gRPC call: {e}")
                    messages.error(request, f"Error in voting for candidate {candidate_id}: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                messages.error(request, f"Error in voting for candidate {candidate_id}: {e}")

        if not double_voting_detected:
            messages.success(request, 'Your vote has been submitted.')
        
        return redirect('ballot_paper')
    else:
        candidates = CandidateProfile.objects.select_related('candidate', 'candidate__party').all()
        return render(request, 'Voter/votingPg.html', {'candidates': candidates})

# ---------------------------------------Candidate views------------------------------------------------

from .forms import ElectionPosterForm, ProfilePictureForm, CandidateStatementForm

@flexible_access('public', 'voter', 'candidate')
def candidate_home(request, candidate_id=None):
    candidate_profile = None
    if candidate_id:
        candidate_profile = get_object_or_404(CandidateProfile, pk=candidate_id)
    else:
        candidate_profile = get_object_or_404(CandidateProfile, pk=request.user)
    
    is_owner = request.user == candidate_profile.candidate
    
    profile_picture_form = ProfilePictureForm()
    election_poster_form = ElectionPosterForm()
    candidate_statement_form = CandidateStatementForm()
    candidate_statement_form.fields['candidate_statement'].initial = candidate_profile.candidate_statement

    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    disable_deletion = current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']

    return render(request, 'Candidate/candidatePg.html', {
        'profile_picture_form': profile_picture_form,
        'election_poster_form': election_poster_form,
        'candidate_statement_form': candidate_statement_form,
        'candidate_profile': candidate_profile,
        'is_owner': is_owner,
        'disable_deletion': disable_deletion
    })

@flexible_access('candidate')
def upload_election_poster(request):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
        messages.error(request, 'You do not have permission to upload the election poster this time.')
        return redirect('candidate_home')
    
    if request.method == 'POST':
        form = ElectionPosterForm(request.POST, request.FILES)
        if form.is_valid():
            candidate_profile = get_object_or_404(CandidateProfile, candidate=request.user)
            candidate_profile.election_poster = form.cleaned_data['election_poster']
            candidate_profile.save()
            messages.success(request, 'Election poster successfully uploaded.')
        else:
            messages.error(request, "File size should not exceed 5MB.")

        return redirect('candidate_home')
    
@flexible_access('candidate')
def delete_election_poster(request, candidate_id):
    candidate_profile = get_object_or_404(CandidateProfile, pk=candidate_id)

    if candidate_profile.election_poster:
        candidate_profile.election_poster.delete(save=False)
        candidate_profile.save()
        messages.success(request, 'Election poster deleted successfully.')
    else:
        messages.error(request, 'No election poster to delete.')

    return redirect('candidate_home')

@flexible_access('candidate')
def upload_profile_picture(request):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
        messages.error(request, 'You do not have permission to upload the profile picture at this time.')
        return redirect('candidate_home')
    
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            candidate_profile = get_object_or_404(CandidateProfile, candidate=request.user)
            candidate_profile.profile_picture = form.cleaned_data['profile_picture']
            candidate_profile.save()
            messages.success(request, 'Profile picture successfully uploaded.')
        else:
            messages.error(request, "File size should not exceed 5MB.")
    
        return redirect('candidate_home')

@flexible_access('candidate')
def delete_profile_picture(request, candidate_id):
    candidate_profile = get_object_or_404(CandidateProfile, pk=candidate_id)

    if candidate_profile.profile_picture:
        candidate_profile.profile_picture.delete(save=False)
        candidate_profile.save()
        messages.success(request, 'Profile picture deleted successfully.')
    else:
        messages.error(request, 'No profile picture to delete.')

    return redirect('candidate_home')

@flexible_access('candidate')
def upload_candidate_statement(request):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase.phase_name in ['Cooling Off Day', 'Polling Day']:
        messages.error(request, 'You do not have permission to upload the candidate statement at this time.')
        return redirect('candidate_home')
    
    if request.method == 'POST':
        form = CandidateStatementForm(request.POST)
        if form.is_valid():
            candidate_profile = get_object_or_404(CandidateProfile, candidate=request.user)
            candidate_profile.candidate_statement = form.cleaned_data['candidate_statement']
            candidate_profile.save()
            messages.success(request, 'Candidate statement successfully updated.')
        else:
            messages.error(request, "Invalid submission.")

        return redirect('candidate_home')

@flexible_access('candidate')
def delete_candidate_statement(request, candidate_id):
    candidate_profile = get_object_or_404(CandidateProfile, pk=candidate_id)

    if candidate_profile.candidate_statement:
        candidate_profile.candidate_statement = None
        candidate_profile.save()
        messages.success(request, 'Candidate statement deleted successfully.')
    else:
        messages.error(request, 'No candidate statement to delete.')

    return redirect('candidate_home')

# ---------------------------------------Genereal user views------------------------------------------------
@flexible_access('public')
def general_user_home(request):
    announcements = Announcement.objects.all()[:2]  # only get latest 2 announcements
    districts = District.objects.all()
    active_phase = ElectionPhase.objects.filter(is_active=True).first()
    return render(request, 'generalUser/generalUserPg.html', {
        'announcements': announcements,
        'districts': districts,
        'active_phase': active_phase,
    })

@flexible_access('public')
def view_district_detail(request, district_id):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if current_phase and current_phase.phase_name == 'End Election':
        compute_final_total_vote(request, district_id)

    phase_name = current_phase.phase_name if current_phase and current_phase.phase_name else 'Not Available'
    
    district = get_object_or_404(District, pk=district_id)
    candidate_profiles = CandidateProfile.objects.filter(candidate__district=district)
    candidates = UserAccount.objects.filter(district=district)
    vote_results = VoteResults.objects.filter(candidate__district=district)

    candidate_names = [candidate.full_name for candidate in candidates]
    total_votes = [candidate.total_vote for candidate in vote_results]

    total_votes_sum = VoteResults.objects.filter(candidate__in=candidates).aggregate(Sum('total_vote'))['total_vote__sum']
    if total_votes_sum is None:
        total_votes_sum = 0
    print(total_votes_sum)

    return render(request, 'generalUser/viewDistrictDetail.html', {
        'phase': phase_name,
        'district': district,
        'candidate_profiles': candidate_profiles,
        'candidate_names': candidate_names,
        'total_votes': total_votes,
        'result': total_votes_sum 
    })

def get_ongoing_result(request, district_id):
    candidates = UserAccount.objects.filter(district__district_id=district_id)
    total_votes_sum = VoteResults.objects.filter(candidate__in=candidates).aggregate(Sum('total_vote'))['total_vote__sum']
    if total_votes_sum is None:
        total_votes_sum = 0
    return JsonResponse({'result': total_votes_sum})

def compute_final_total_vote(request, district_id):
    try:
        grpc_calculate_total_vote_run(district_ids=[district_id])
    except GrpcError as e:
        print(f"Error in gRPC call: {e}")
        messages.error(request, f"Error in calculating vote result for {district_id}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        messages.error(request, f"Unexpected error in calculating vote result for {district_id}: {e}")

#------------------------------------------------- WebAuthn------------------------------------------------------
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from webauthn import (generate_registration_options, verify_registration_response, 
                      generate_authentication_options, verify_authentication_response, 
                      options_to_json)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, structs
from webauthn.helpers.structs import (RegistrationCredential, AuthenticatorAssertionResponse, 
                                      AuthenticatorAttestationResponse, AuthenticationCredential, 
                                      PublicKeyCredentialDescriptor)
from .models import WebauthnRegistration, WebauthnCredentials
from django.utils.module_loading import import_string
import base64
import os
import json

@login_required
@require_http_methods(["GET"])
def webauthn_register_options(request):
    try:
        print(f"User ID: {request.user.user_id}")
        print(f"Username: {request.user.username}")
        print(f"Full Name: {request.user.full_name}")
        
        options = generate_registration_options(
            rp_id='localhost',
            rp_name='myapp',
            user_id=str(request.user.user_id).encode('utf-8'),
            user_name=request.user.username,
            user_display_name=request.user.full_name
        )
        
        print("Options generated successfully")

        challenge_b64 = base64.urlsafe_b64encode(options.challenge).rstrip(b'=').decode('ascii')
        
        WebauthnRegistration.objects.update_or_create(
            user=request.user,
            defaults={'challenge': challenge_b64}
        )
        print(f"Stored challenge: {options.challenge}")
        print("WebauthnRegistration updated/created successfully")
        
        json_options = options_to_json(options)
        json_options = json.loads(json_options)
        json_options['challenge'] = challenge_b64  # Replace with properly encoded challenge
      
        return JsonResponse(json_options, safe=False)
    except Exception as e:
        print(f"Error in webauthn_register_options: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def webauthn_register_verify(request):
    try:
        registration = WebauthnRegistration.objects.get(user=request.user)
        data = json.loads(request.body)
        
        print(f"Received registration data: {data}")  # Debug: Print received data
        
        # Create the RegistrationCredential object
        credential = RegistrationCredential(
            id=data['id'],
            raw_id=base64.urlsafe_b64decode(data['rawId'] + '=='),
            response=AuthenticatorAttestationResponse(
                client_data_json=base64.urlsafe_b64decode(data['response']['clientDataJSON'] + '=='),
                attestation_object=base64.urlsafe_b64decode(data['response']['attestationObject'] + '==')
            ),
            type=data['type']
        )
        
        try:
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=base64.urlsafe_b64decode(registration.challenge + '=='),
                expected_origin='https://localhost:8000',
                expected_rp_id='localhost'
            )
            print(f"Verification successful: {verification}")  # Debug: Print verification result
        except Exception as e:
            print(f"Verification failed: {str(e)}")  # Debug: Print verification error
            return JsonResponse({'status': 'error', 'message': f'Verification failed: {str(e)}'}, status=400)
        
        # If no exception is raised, the verification is successful
        credential_id = base64.urlsafe_b64encode(verification.credential_id).rstrip(b'=').decode('ascii')
        credential_public_key = base64.urlsafe_b64encode(verification.credential_public_key).rstrip(b'=').decode('ascii')
        
        new_credential = WebauthnCredentials.objects.create(
            user=request.user,
            credential_id=credential_id,
            credential_public_key=credential_public_key,
            current_sign_count=verification.sign_count
        )
        print(f"New credential created: {new_credential}")  # Debug: Print new credential object
        
        # Verify the credential was stored
        stored_credential = WebauthnCredentials.objects.filter(user=request.user, credential_id=credential_id).first()
        if stored_credential:
            print(f"Credential successfully stored in DB: {stored_credential}")  # Debug: Print stored credential
        else:
            print("Error: Credential not found in DB after creation")  # Debug: Print error if not found
        
        # Print all credentials for this user
        all_credentials = WebauthnCredentials.objects.filter(user=request.user)
        print(f"All credentials for user {request.user.username}: {list(all_credentials.values())}")  # Debug: Print all user credentials
        
        # Determine the redirect URL based on user role
        if request.user.role.profile_name == 'Admin':
            redirect_url = reverse('admin_home')
        elif request.user.role.profile_name == 'Candidate':
            redirect_url = reverse('candidate_home')
        else:
            redirect_url = reverse('default_home')  # Make sure to define a default home URL

        return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
    except WebauthnRegistration.DoesNotExist:
        print("Error: WebauthnRegistration not found")  # Debug: Print error if registration not found
        return JsonResponse({'status': 'error', 'message': 'Registration not found'}, status=400)
    except json.JSONDecodeError:
        print("Error: Invalid JSON data")  # Debug: Print error if JSON is invalid
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug: Print unexpected errors
        return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def webauthn_login_options(request):
    try:
        # Get the pending user from the session
        pending_user_id = request.session.get('pending_user_id')
        if not pending_user_id:
            return JsonResponse({'error': 'No pending login'}, status=400)
        
        user = User.objects.get(user_id=pending_user_id)  # Changed from 'id' to 'user_id'
        
        allow_credentials = []
        for cred in user.webauthn_credentials.all():
            try:
                decoded_id = base64.urlsafe_b64decode(cred.credential_id + '==')
                allow_credentials.append({
                    'type': 'public-key',
                    'id': decoded_id
                })
            except Exception as e:
                print(f"Error processing credential {cred.credential_id}: {str(e)}")
        
        options = generate_authentication_options(
            rp_id='localhost',
            challenge=os.urandom(32),
            allow_credentials=allow_credentials
        )
        
        # Store the challenge in the session
        request.session['webauthn_challenge'] = base64.urlsafe_b64encode(options.challenge).decode('ascii')
        
        # Manually create the JSON response
        json_options = {
            'challenge': base64.urlsafe_b64encode(options.challenge).decode('ascii'),
            'timeout': options.timeout,
            'rpId': options.rp_id,
            'allowCredentials': [
                {
                    'type': 'public-key',
                    'id': base64.urlsafe_b64encode(cred['id']).decode('ascii')
                }
                for cred in options.allow_credentials
            ],
            'userVerification': options.user_verification
        }
        
        return JsonResponse(json_options)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        print(f"Error in webauthn_login_options: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def webauthn_login_verify(request):
    try:
        data = json.loads(request.body)
        print(f"Received data: {data}")  # Debug: Print received data
        
        # Create the AuthenticationCredential object
        credential = AuthenticationCredential(
            id=data['id'],
            raw_id=base64url_to_bytes(data['rawId']),
            response=AuthenticatorAssertionResponse(
                client_data_json=base64url_to_bytes(data['response']['clientDataJSON']),
                authenticator_data=base64url_to_bytes(data['response']['authenticatorData']),
                signature=base64url_to_bytes(data['response']['signature']),
                user_handle=base64url_to_bytes(data['response']['userHandle']) if data['response'].get('userHandle') else None
            ),
            type=data['type']
        )
        
        # Retrieve the stored challenge
        stored_challenge = base64.urlsafe_b64decode(request.session.get('webauthn_challenge', '') + '==')
        
        # Find the user based on the credential ID
        credential_id = data['id']
        try:
            user_credential = WebauthnCredentials.objects.get(credential_id=credential_id)
        except WebauthnCredentials.DoesNotExist:
            print(f"Credential not found: {credential_id}")
            print(f"Available credentials: {list(WebauthnCredentials.objects.values_list('credential_id', flat=True))}")
            return JsonResponse({'status': 'error', 'message': 'Credential not found'}, status=400)
        
        user = user_credential.user
        
        # Ensure the user matches the pending user
        pending_user_id = request.session.get('pending_user_id')
        if not pending_user_id or user.user_id != pending_user_id:
            return JsonResponse({'status': 'error', 'message': 'User mismatch'}, status=400)
        
        origin = os.environ.get("EXPECTED_ORIGIN", 'https://localhost:8000')
        rp_id = os.environ.get("EXPECTED_RP_ID", 'localhost')

        try:
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=stored_challenge,
                expected_origin=origin,
                expected_rp_id=rp_id,
                credential_public_key=base64.urlsafe_b64decode(user_credential.credential_public_key + '=='),
                credential_current_sign_count=user_credential.current_sign_count,
                require_user_verification=True
            )
            
            # Update the sign count
            user_credential.current_sign_count = verification.new_sign_count
            user_credential.save()
            
            # Get the first authentication backend
            backend = get_backends()[0]
            
            # Get the dotted path string for the backend
            backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
            
            # Log the user in with the specified backend
            login(request, user, backend=backend_path)
            
            # Include the user's role in the response
            user_role = user.role.profile_name if hasattr(user, 'role') and hasattr(user.role, 'profile_name') else 'Unknown'
            
            return JsonResponse({
                'status': 'success',
                'user_role': user_role
            })
        except Exception as e:
            print(f"Verification failed: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Verification failed: {str(e)}'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'}, status=500)

def webauthn_register_view(request):
    return render(request, 'webauthn_register.html')

def webauthn_login_view(request):
    return render(request, 'webauthn_login.html')

def webauthn_verify_view(request):
    if 'pending_user_id' not in request.session:
        return redirect('login')
    return render(request, 'webauthn_verify.html')

def user_has_webauthn_credential(user):
    return WebauthnCredentials.objects.filter(user=user).exists()

@flexible_access('admin')
def delete_all_credentials(request, user_id):
    user = get_object_or_404(UserAccount, user_id=user_id)
    
    if request.method == 'POST':
        WebauthnCredentials.objects.filter(user=user).delete()
        messages.success(request, f"All WebAuthn credentials for {user.username} have been deleted.")
    
    return redirect('view_user_accounts')