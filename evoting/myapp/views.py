from django.contrib.auth import authenticate, login, logout, get_backends, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.messages import get_messages
from django.db.models import Q, Sum
from .forms import CreateNewUser, CSVUploadForm, EditUser, CreateDistrict, EditDistrict, CreateAnnouncement, CreateParty, CreateProfileForm, PasswordChangeForm, FirstLoginPasswordChangeForm
from .models import UserAccount, District, ElectionPhase, Announcement, Party, Profile, CandidateProfile, Voter, VoteResults, SingpassUser
from django.contrib.auth.hashers import check_password
from .decorators import flexible_access
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import csv, datetime

from pygrpc.ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_construct_vote_request,
    grpc_construct_gen_candidate_request,
    grpc_construct_calculate_total_vote_request,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
    grpc_calculate_total_vote_run,
    grpc_filter_non_voter_run,
    GrpcError,
)

User = get_user_model()

def health_check(request):
    return HttpResponse("OK", status=200)

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
            request.session['password_changed'] = True  
            
            return JsonResponse({
                'status': 'success',
                'requires_webauthn': has_webauthn,
                'message': 'Login successful. Proceed with WebAuthn registration.' if not has_webauthn else 'Login successful. Proceed with WebAuthn verification.'
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=400)
    else:
        return render(request, 'login.html')

def check_current_password(request):
    data = json.loads(request.body)
    current_password = data.get('current_password')
    is_valid = request.user.check_password(current_password)
    return JsonResponse({'is_valid': is_valid})

@flexible_access('admin', 'candidate')
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()

            # Ensure the session variable 'password_changed' is set to True after any password change
            request.session['password_changed'] = True
            print(f"Password changed for user {user.username}. Session 'password_changed' set to True.")

            messages.success(request, 'Your password has been successfully changed.')

            # Log the user in with the specified backend
            backend = get_backends()[0]
            backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user, backend=backend_path)
            request.session['password_changed'] = True

            # Redirect based on user role
            if user.role.profile_name == 'Admin':
                return redirect('admin_home')
            elif user.role.profile_name == 'Candidate':
                return redirect('candidate_home')
        else:
            return render(request, 'changePassword.html', {'form': form})
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'changePassword.html', {'form': form})


def first_login_password_change(request):
    if 'pending_user_id' not in request.session:
        print("No pending_user_id found in session, redirecting to login.")
        return redirect('login')

    user = User.objects.get(user_id=request.session['pending_user_id'])

    if request.method == 'POST':
        form = FirstLoginPasswordChangeForm(request.POST)
        if form.is_valid():
            print("Form is valid. Changing password.")
            user.set_password(form.cleaned_data['new_password'])
            user.first_login = False
            user.save()
            print("Password change successful. User first_login flag set to False and user saved.")

            # Log the user in after setting the password for WebAuthn registration
            backend = get_backends()[0]
            backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user, backend=backend_path)
            print(f"User logged in.")

            # Set session variables to indicate the password has been successfully changed
            request.session['password_changed'] = True
            request.session['first_registration'] = True
            print("Session variable 'password_changed' set to True.")

            # Return a JSON response indicating success and that WebAuthn registration should be initiated
            return JsonResponse({'status': 'success', 'prompt_webauthn': True})
        else:
            # If the form is not valid, do not reset 'password_changed'
            print(f"Form is invalid. Errors: {form.errors}")
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        print("GET request received.")
        form = FirstLoginPasswordChangeForm()

    print("Rendering firstLogin.html template with the form.")
    return render(request, 'firstLogin.html', {'form': form})



@flexible_access('admin', 'candidate')
def my_account(request):
    password_form = PasswordChangeForm(request.user)
    return render(request, 'myAccount.html', {'password_form': password_form})

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

@flexible_access('admin')
def admin_home(request):
    active_phase = ElectionPhase.objects.filter(is_active=True).first()
    announcements = Announcement.objects.all().order_by('-date')  # Order by date in descending order
    return render(request, 'adminDashboard/home.html', {'active_phase': active_phase, 'announcements': announcements})

def is_creation_deletion_disabled():
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    disable_create_delete = not current_phase or current_phase.phase_name in ['Cooling Off Day', 'Polling Day', 'End Election']
    return disable_create_delete
# ---------------------------------------UserAccount views------------------------------------------------
@flexible_access('admin')
def create_account(request, upload_type=None):
    disable_creation = is_creation_deletion_disabled()
    if request.method == 'POST':
        if disable_creation:
            messages.error(request, 'You do not have permission to create the account at this time.')
            return redirect('create_account')
        if upload_type == 'csv_upload':
            return handle_user_csv_upload(request)
        else:
            return handle_single_user_creation(request)
    else:
        return render(request, 'userAccount/createUserAcc.html', {
            'form': CreateNewUser(),
            'csv_form': CSVUploadForm(),
            'disable_creation': disable_creation
        })
    
def handle_user_csv_upload(request):
    required_fields = ['username', 'full_name', 'date_of_birth', 'password', 'role', 'party', 'district']
    form = CSVUploadForm(request.POST, request.FILES)
    if form.is_valid():
        csv_file = request.FILES['csv_file']
        reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
        # Check if required fields are present
        if not all(field in reader.fieldnames for field in required_fields):
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            messages.error(request, f"Missing fields in CSV: {', '.join(missing_fields)}")
            return redirect('create_account')
        for row in reader:
            try:
                date_of_birth = datetime.datetime.strptime(row['date_of_birth'], '%d/%m/%Y').date()
                user = UserAccount(
                        username = row['username'],
                        full_name = row['full_name'],
                        password = make_password(row['password']),
                        date_of_birth = date_of_birth,
                        role = Profile.objects.get(profile_name=row['role']),
                        district = District.objects.get(district_name=row['district'].upper()),
                        party = Party.objects.get(party_name=row['party'])
                    )
                user.save()
                create_additional_candidate_data(request, user)
            except ObjectDoesNotExist as e:
                messages.error(request, f"Error creating user {row['username']}: {e}")
                return redirect('create_account')
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
        if user.role.profile_name == 'Candidate':
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
    
    disable_deletion = is_creation_deletion_disabled()
    return render(request, 'userAccount/viewUserAcc.html', {'users': users, 'disable_deletion': disable_deletion})

@flexible_access('admin')
def edit_account(request, user_id):
    user = get_object_or_404(UserAccount, pk=user_id)
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if request.method == 'POST':
        form = EditUser(request.POST, instance=user, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account successfully updated.')
            return redirect('view_accounts')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = EditUser(instance=user, user=user)
    return render(request, 'userAccount/updateUserAcc.html', {'form': form, 'current_phase': current_phase, 'user': user})

@flexible_access('admin')
def delete_account(request, user_id):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
        messages.error(request, 'You do not have permission to delete the account at this time.')
        return redirect('view_accounts')
    
    user = get_object_or_404(UserAccount, pk=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('view_accounts')
    return HttpResponse(status=405)

# ---------------------------------------Election phase views------------------------------------------------
@flexible_access('admin')
def activate_election_phase(request, phase_id):
    ElectionPhase.objects.update(is_active=False)  # Set all phases to inactive
    phase = ElectionPhase.objects.get(pk=phase_id)
    phase.is_active = True
    if (phase.phase_name == 'End Election'):
        district_ids = District.objects.values_list('district_id', flat=True)
        compute_final_total_vote(request, district_ids)
    phase.save()
    messages.success(request, 'Election Phase successfully changed.')
    return redirect('view_election_phases')

@flexible_access('admin')
def list_election_phases(request):
    phases = ElectionPhase.objects.all()
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    return render(request, 'electionPhase/listPhases.html', {'phases': phases, 'current_phase':current_phase})

# ---------------------------------------District views-----------------------------------------------------
@flexible_access('admin')
def create_district(request, upload_type=None):
    disable_creation = is_creation_deletion_disabled()
    if request.method == 'POST':
        if disable_creation:
            messages.error(request, 'You do not have permission to create the districts at this time.')
            return redirect('create_district')
        
        if upload_type == 'csv_upload':
            return handle_district_csv_upload(request)
        else:
            return handle_single_district_creation(request)
    else:
        return render(request, 'district/createDistrict.html', {
            'form': CreateDistrict(),
            'csv_form': CSVUploadForm(),
            'disable_creation': disable_creation
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
            try:
                district = District(
                    district_name=row['district_name'],
                    num_of_people=row['num_of_people']
                )
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
        district = form.save(commit=False)
        district.save()
        create_additional_voter_data(request, district)
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
def view_districts(request):
    query = request.GET.get('search', '')
    if query:
        # Filter districts where the search query matches the name field
        districts = District.objects.filter(district_name__icontains=query)
    else:
        districts = District.objects.all()

    if request.user.is_authenticated and request.path == '/admin_home/view_districts/':
            disable_deletion = is_creation_deletion_disabled()
            return render(request, 'district/viewDistrict.html', {'districts': districts, 'disable_deletion': disable_deletion})
        
    # for general user
    return render(request, 'generalUser/viewAllDistricts.html', {'districts': districts})
    
@flexible_access('admin')
def edit_district(request, district_id):
    district = get_object_or_404(District, pk=district_id)
    if request.method == 'POST':
        form = EditDistrict(request.POST, instance=district)
        if form.is_valid():
            form.save()
            messages.success(request, 'District successfully updated.')
            return redirect('view_districts')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = EditDistrict(instance=district)

    return render(request, 'district/editDistrict.html', {'form': form, 'district': district})

@flexible_access('admin')
def delete_district(request, district_id):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
        messages.error(request, 'You do not have permission to delete the district at this time.')
        return redirect('view_districts')
    
    district = get_object_or_404(District, pk=district_id)
    if request.method == 'POST':
        district.delete()
        messages.success(request, 'District successfully deleted.')
        return redirect('view_districts')
    else:
        messages.error(request, 'Error deleting district.')
        return redirect('view_districts')

# ---------------------------------------Profile view-----------------------------------------------------
@flexible_access('admin')
def create_profile(request):
    disable_creation = is_creation_deletion_disabled()
    if request.method == 'POST':
        if disable_creation:
            messages.error(request, 'You do not have permission to create the profile at this time.')
            return redirect('create_profile')
        form = CreateProfileForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile successfully created.')
            return redirect('create_profile')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateProfileForm()
    return render(request, 'userProfile/createProfile.html', {'form': form, 'disable_creation': disable_creation})

@flexible_access('admin')
def view_profiles(request):
    profiles = Profile.objects.all()
    disable_deletion = is_creation_deletion_disabled()
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
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
        messages.error(request, 'You do not have permission to delete the profile at this time.')
        return redirect('view_profiles')
    
    profile = get_object_or_404(Profile, pk=profile_id)
    if profile.profile_name in ['Admin', 'Candidate']:
        messages.error(request, 'You do not have permission to delete the permanent profile.')
        return redirect('view_profiles')
    
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
def view_announcements(request):
    announcements = Announcement.objects.all()
    if request.user.is_authenticated and request.path == '/admin_home/view_announcements/':
        return render(request, 'announcement/viewAnnouncement.html', {'announcements': announcements})
    else:
        return render(request, 'generalUser/viewAllAnnouncements.html', {'announcements': announcements})

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
            return redirect('view_announcements')
    else:
        form = CreateAnnouncement(instance=announcement)
    return render(request, 'announcement/editAnnouncement.html', {'form': form, 'announcement': announcement})

@flexible_access('admin')
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement successfully deleted.')
        return redirect('view_announcements')
    else:
        messages.error(request, 'Error deleting announcement.')
        return redirect('view_announcements')

# ---------------------------------------Party views------------------------------------------------
@flexible_access('admin')
def create_party(request):
    disable_creation = is_creation_deletion_disabled()
    if request.method == 'POST':
        if disable_creation:
            messages.error(request, 'You do not have permission to create the party at this time.')
            return redirect('create_party')
        form = CreateParty(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party successfully created.')
            return redirect('create_party')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateParty()
    return render(request, 'party/createParty.html', {'form': form,'disable_creation': disable_creation })

@flexible_access('admin')
def view_parties(request):
    parties = Party.objects.all()
    disable_deletion = is_creation_deletion_disabled()
    return render(request, 'party/viewParty.html', {'parties': parties, 'disable_deletion': disable_deletion})

@flexible_access('admin')
def edit_party(request, party_id):
    party = get_object_or_404(Party, pk=party_id)
    if request.method == 'POST':
        form = CreateParty(request.POST, instance=party)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party successfully updated.')
            return redirect('view_parties')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateParty(instance=party)
    return render(request, 'party/editParty.html', {'form': form})

@flexible_access('admin')
def delete_party(request, party_id):
    party = get_object_or_404(Party, pk=party_id)
    if request.method == 'POST':
        disable_deletion = is_creation_deletion_disabled()
        if disable_deletion:
            messages.error(request, 'You do not have permission to delete the party at this time.')
            return redirect('view_parties')
        party.delete()
        messages.success(request, 'Party successfully deleted.')
        return redirect('view_parties')
    else:
        messages.error(request, 'Error deleting party.')
        return redirect('view_parties')

# ---------------------------------------Voter views------------------------------------------------
@flexible_access('public')
def singpass_login(request):
    # print(f"Request method: {request.method}")
    # print(f"Request POST data: {request.POST}")
    # print(f"Request headers: {request.headers}")

    if request.method == 'POST':
        singpass_id = request.POST['singpass_id']
        password = request.POST['password']
        # print(f'Login attempt with Singpass ID: {singpass_id} with password: {password}')
        # TODO it fail at the authenticate function
        user = authenticate(request, singpass_id=singpass_id, password=password)
        if user is not None:
            # print(f'Authentication successful for Singpass ID: {singpass_id}, Now logging in...')
            login(request, user)
            messages.success(request, 'Log in successful.')
            request.session['singpass_id'] = singpass_id 
            return redirect('voter_home') 
        else:
            # print(f'Login failed for Singpass ID: {singpass_id}')
            return render(request, 'singpassLogin.html', {'error': 'Invalid username or password.'})
    else:
        # print(f'Request method is not POST...')
        # print(f'Request method is {request.method}')
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
    disable_vote = not current_phase or current_phase.phase_name != 'Polling Day'
    
    # check if the voter already voted
    if candidates:
        res = grpc_compute_vote_run(candidate_id=candidates[0].candidate_id, voter_id=voter.voter_id, is_voting=False)
        voting_status = "Voted" if res.has_voted else "Haven't Voted"
    else:
        voting_status = "Haven't Voted"

    return render(request, 'Voter/voterPg.html', {
        'candidates': candidates,
        'user_district': user_district,
        'disable_vote': disable_vote, 
        'voting_status': voting_status
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
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    disable_vote = not current_phase or current_phase.phase_name != 'Polling Day'

    # Also ensure session messages are cleared
    if 'messages' in request.session:
        del request.session['messages']
    request.session.modified = True

    return render(request, 'Voter/votingPg.html', {'candidates': candidates, 'disable_vote': disable_vote})

@flexible_access('voter')
def cast_vote(request):
    if request.method == 'POST':
        current_phase = ElectionPhase.objects.filter(is_active=True).first()
        if not current_phase or current_phase.phase_name != 'Polling Day':
            messages.error(request, 'Sorry, you can not vote at this time around.')
            return redirect('voter_home')
        
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
                grpc_compute_vote_run(candidate_id=int(candidate_id), voter_id=voter.voter_id, is_voting=True)
                
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

    disable_deletion = is_creation_deletion_disabled()

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
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
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
def delete_election_poster(request):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
        messages.error(request, 'You do not have permission to delete the election poster at this time.')
        return redirect('candidate_home')

    candidate_profile = get_object_or_404(CandidateProfile, pk=request.user.user_id)
    if candidate_profile.election_poster:
        candidate_profile.election_poster.delete(save=False)
        candidate_profile.save()
        messages.success(request, 'Election poster deleted successfully.')
    else:
        messages.error(request, 'No election poster to delete.')

    return redirect('candidate_home')

@flexible_access('candidate')
def upload_profile_picture(request):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
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
def delete_profile_picture(request):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
        messages.error(request, 'You do not have permission to delete the profile picture at this time.')
        return redirect('candidate_home')
    
    candidate_profile = get_object_or_404(CandidateProfile, pk=request.user.user_id)
    if candidate_profile.profile_picture:
        candidate_profile.profile_picture.delete(save=False)
        candidate_profile.save()
        messages.success(request, 'Profile picture deleted successfully.')
    else:
        messages.error(request, 'No profile picture to delete.')

    return redirect('candidate_home')

@flexible_access('candidate')
def upload_candidate_statement(request):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
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
def delete_candidate_statement(request):
    disable_deletion = is_creation_deletion_disabled()
    if disable_deletion:
        messages.error(request, 'You do not have permission to delete the candidate statement at this time.')
        return redirect('candidate_home')
    
    candidate_profile = get_object_or_404(CandidateProfile, pk=request.user.user_id)
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
    active_phase = ElectionPhase.objects.filter(is_active=True).first()
    return render(request, 'generalUser/generalUserPg.html', {
        'announcements': announcements,
        'active_phase': active_phase,
    })

@flexible_access('public')
def view_district_detail(request, district_id):
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    phase_name = current_phase.phase_name if current_phase and current_phase.phase_name else 'Not Available'
    
    district = get_object_or_404(District, pk=district_id)
    candidate_profiles = CandidateProfile.objects.filter(candidate__district=district)
    candidates = UserAccount.objects.filter(district=district)
    vote_results = VoteResults.objects.filter(candidate__district=district)

    candidate_names = [candidate.candidate.full_name for candidate in vote_results]
    total_votes = [candidate.total_vote for candidate in vote_results]

    winner_profile = None
    if current_phase and current_phase.phase_name == 'End Election':
        winner = vote_results.order_by('-total_vote').first()
        winner_profile = CandidateProfile.objects.get(candidate=winner.candidate)

    total_votes_sum = VoteResults.objects.filter(candidate__in=candidates).aggregate(Sum('total_vote'))['total_vote__sum']
    if total_votes_sum is None:
        total_votes_sum = 0

    return render(request, 'generalUser/viewDistrictDetail.html', {
        'phase': phase_name,
        'district': district,
        'candidate_profiles': candidate_profiles,
        'candidate_names': candidate_names,
        'total_votes': total_votes,
        'voters_total': district.num_of_people,
        'result': total_votes_sum,
        'winner': winner_profile
    })

def get_ongoing_result(request, district_id):
    candidates = UserAccount.objects.filter(district__district_id=district_id)
    total_votes_sum = VoteResults.objects.filter(candidate__in=candidates).aggregate(Sum('total_vote'))['total_vote__sum']
    if total_votes_sum is None:
        total_votes_sum = 0
    return JsonResponse({'result': total_votes_sum})

def compute_final_total_vote(request, district_ids):
    try:
        grpc_calculate_total_vote_run(district_ids=district_ids)
    except GrpcError as e:
        print(f"Error in gRPC call: {e}")
        messages.error(request, f"Error in calculating vote results: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        messages.error(request, f"Unexpected error in calculating vote results: {e}")

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
origin = os.environ.get("EXPECTED_ORIGIN", 'https://localhost:8000')
rp_id =os.environ.get("EXPECTED_RP_ID", 'localhost')
rp_name = "electsg"

@login_required
@require_http_methods(["GET"])
def webauthn_register_options(request):
    try:
        print(f"User ID: {request.user.user_id}")
        print(f"Username: {request.user.username}")
        print(f"Full Name: {request.user.full_name}")
        
        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=rp_name,
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
        # Check the 'password_changed' flag
        password_changed = request.session.get('password_changed', False)
        print(f"Checking session 'password_changed': {password_changed}")

        if not password_changed:
            print("Password change not confirmed, returning error.")
            return JsonResponse({'status': 'error', 'message': 'Password change not confirmed'}, status=400)

        # Continue with the rest of the WebAuthn registration verification
        registration = WebauthnRegistration.objects.get(user=request.user)
        data = json.loads(request.body)
        
        print(f"Received registration data: {data}")  # Debug: Print received data
        
        # Check if the registration was cancelled
        if data.get('status') == 'cancelled':
            # Log the user out
            logout(request)
            return JsonResponse({'status': 'error', 'message': 'WebAuthn registration was cancelled'}, status=400)
        
        # Check if the user already has 2 devices registered
        existing_credentials = WebauthnCredentials.objects.filter(user=request.user)
        if existing_credentials.count() >= 2:
            return JsonResponse({'status': 'error', 'message': 'Maximum number of devices (2) already registered'}, status=400)
        
        # Check if this is a master device
        is_master = data.get('is_master', False)
        
        # If it's a master device, check if a master device already exists
        if is_master and existing_credentials.filter(is_master=True).exists():
            return JsonResponse({'status': 'error', 'message': 'A master device is already registered'}, status=400)
        
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
                expected_origin=origin,
                expected_rp_id=rp_id
            )
            print(f"Verification successful: {verification}")  # Debug: Print verification result
        except Exception as e:
            print(f"Verification failed: {str(e)}")  # Debug: Print verification error
            logout(request)  # Log out the user if verification fails
            return JsonResponse({'status': 'error', 'message': f'Verification failed: {str(e)}'}, status=400)
        
        # If no exception is raised, the verification is successful
        credential_id = base64.urlsafe_b64encode(verification.credential_id).rstrip(b'=').decode('ascii')
        credential_public_key = base64.urlsafe_b64encode(verification.credential_public_key).rstrip(b'=').decode('ascii')
        
        new_credential = WebauthnCredentials.objects.create(
            user=request.user,
            credential_id=credential_id,
            credential_public_key=credential_public_key,
            current_sign_count=verification.sign_count,
            is_master=is_master  # Set the is_master flag
        )
        print(f"New credential created: {new_credential}")  # Debug: Print new credential object
        
        # Verify the credential was stored
        stored_credential = WebauthnCredentials.objects.filter(user=request.user, credential_id=credential_id).first()
        if stored_credential:
            print(f"Credential successfully stored in DB: {stored_credential}")  # Debug: Print stored credential
        else:
            print("Error: Credential not found in DB after creation")  # Debug: Print error if not found
            logout(request)  # Log out the user if credential storage fails
            return JsonResponse({'status': 'error', 'message': 'Failed to store credential'}, status=500)
        
        # Print all credentials for this user
        all_credentials = WebauthnCredentials.objects.filter(user=request.user)
        print(f"All credentials for user {request.user.username}: {list(all_credentials.values())}")  # Debug: Print all user credentials
        
        # Determine the redirect URL based on user role
        if request.user.role.profile_name == 'Admin':
            redirect_url = reverse('admin_home')
        elif request.user.role.profile_name == 'Candidate':
            redirect_url = reverse('candidate_home')
        else:
            redirect_url = reverse('')  # Make sure to define a default home URL

        first_registration = request.session.get('first_registration', False)
        print(f"Checking session 'password_changed': {first_registration}")

        if first_registration:
            messages.success(request, 'Logged in Successfully.')
            request.session['first_registration'] = False

        return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
    except WebauthnRegistration.DoesNotExist:
        print("Error: WebauthnRegistration not found")  # Debug: Print error if registration not found
        logout(request)  # Log out the user if registration not found
        return JsonResponse({'status': 'error', 'message': 'Registration not found'}, status=400)
    except json.JSONDecodeError:
        print("Error: Invalid JSON data")  # Debug: Print error if JSON is invalid
        logout(request)  # Log out the user if JSON data is invalid
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug: Print unexpected errors
        logout(request)  # Log out the user if an unexpected error occurs
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
            rp_id=rp_id,
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
            messages.success(request, 'Logged in Successfully.')

            
            # Include the user's role in the response
            user_role = user.role.profile_name if hasattr(user, 'role') and hasattr(user.role, 'profile_name') else 'Unknown'
            
            return JsonResponse({
                'status': 'success',
                'user_role': user_role,
                'message': 'WebAuthn login successful!'
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
        # Delete WebAuthn credentials for the user
        WebauthnCredentials.objects.filter(user=user).delete()
        messages.success(request, f"All WebAuthn credentials for {user.username} have been deleted.")
        
        # Check if the deleted user is the logged-in user
        if request.user == user:
            # Log out the user
            logout(request)
            return redirect('login')
    
    return redirect('view_accounts')

       
def delete_my_credentials(request):
    if request.method == 'POST':
        WebauthnCredentials.objects.filter(user=request.user, is_master=False).delete()

        request.session['password_changed'] = False
        print(f"All non-master credentials for user {request.user.username} have been deleted. Session 'password_changed' set to False.")

        messages.success(request, "All your non-master credentials have been deleted.")


        logout(request)

        # Redirect to the login page
        return redirect('login')

    # If the request method is not POST, redirect to an appropriate page
    return redirect('login')


def delete_non_master_credentials(request):
    if request.method == 'POST':
        # Delete all non-master credentials
        WebauthnCredentials.objects.filter(is_master=False).delete()
        messages.success(request, "All non-master credentials have been deleted.")
    
    return redirect('login')  # Redirect to the login page or appropriate page


# ---------------------------------------Filter non-voter views------------------------------------------------
@flexible_access('admin')
def filter_non_voter(request):
    # check the election phase
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    if not current_phase or current_phase.phase_name != 'End Election':
        messages.error(request, 'Error: Not in End Election phase.')
        return redirect('view_election_phases')

    from .auth_backends import SingpassBackend
    # to be output as csv
    non_voter = []

    # for the voter login but not voter
    district_ids = District.objects.values_list('district_id', flat=True)
    try:
        res = grpc_filter_non_voter_run(district_ids=district_ids)
    except GrpcError as e:
        print(f"Error in gRPC call: {e}")
        messages.error(request, f"Error in filtering non-voters: {e}")

    print(f"Filter non-voter result: {res.voter_ids}")
    login_non_voter_grpc = set(res.voter_ids)

    singpass_users = SingpassUser.objects.all()
    for user in singpass_users:
        # for the voter never login
        hash_info = SingpassBackend.generate_hash(user)
        voter = Voter.objects.filter(district__district_name=user.district.upper(), hash_from_info=hash_info).first()
        if not voter:
            print(f"Singpass user {user.singpass_id} has never login")
            non_voter.append([user.singpass_id, user.full_name, user.district])
        else:
            # for the voter login but not voter
            if voter.voter_id in login_non_voter_grpc:
                print(f"Singpass user {user.singpass_id} has login but not vote")
                non_voter.append([user.singpass_id, user.full_name, user.district])
    
    response = HttpResponse(content_type='text/csv',
                            headers={'Content-Disposition': 'attachment; filename="non_voter.csv"'})
    
    # what if no non-voter
    writer = csv.writer(response)
    if non_voter:
        writer.writerow(['Singpass_ID', 'Full_Name', 'District'])
        for row in non_voter:
            writer.writerow(row)
    else:
        writer.writerow(['No non-voter found'])

    return response