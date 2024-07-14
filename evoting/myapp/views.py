from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.messages import get_messages
from django.db.models import Q
from .forms import CreateNewUser, EditUser, CreateDistrict, EditDistrict, CreateAnnouncement, CreateParty, CreateProfileForm, PasswordChangeForm
from .models import UserAccount, District, ElectionPhase, Announcement, Party, Profile, CandidateProfile, Voter
from django.contrib.auth.hashers import check_password
from .decorators import flexible_access
from django.core.exceptions import ValidationError

from pygrpc.ringct_client import (
    grpc_generate_user_and_votingcurr_run,
    grpc_construct_vote_request,
    grpc_construct_gen_candidate_request,
    grpc_construct_calculate_total_vote_request,
    grpc_generate_candidate_keys_run,
    grpc_compute_vote_run,
    GrpcError,
)

@flexible_access('public')
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
        else:
            messages.error(request, "Invalid username or password.")
 
    return render(request, 'login.html')

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')

            if not check_password(current_password, request.user.password):
                form.add_error('current_password', 'Current password is incorrect.')
            else:
                user = request.user
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been successfully changed.')
                return redirect('login')
    else:
        form = PasswordChangeForm()

    return render(request, 'changePassword.html', {'form': form})

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
@flexible_access('admin')
def create_account(request):
    if request.method == 'POST':
        form = CreateNewUser(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            # Hash the password before saving
            password = form.cleaned_data['password']
            new_user.password = make_password(password)
            new_user.save()

            # Check if the created user account is for a candidate
            if new_user.role.profile_name == 'Candidate':
                # Create a CandidateProfile instance for the candidate user
                CandidateProfile.objects.create(candidate=new_user)
                # Generate user and voting currency via gRPC
                try:
                    grpc_generate_candidate_keys_run(candidate_id=new_user.user_id)
                    messages.success(request, 'Account successfully created.')
                except GrpcError as grpc_error:
                    # Handle specific gRPC errors
                    print(f"Error in gRPC call: {grpc_error}")
                    messages.error(request, f"Error in creating candidate keys: {grpc_error}")
                except Exception as e:
                    # Handle other unexpected exceptions
                    print(f"Unexpected error: {e}")
                    messages.error(request, f"Unexpected error in creating candidate keys: {e}")
            else:
                messages.success(request, 'Account successfully created.')
            return redirect('create_account')  # Redirect to clear the form and show the success message
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateNewUser()

    return render(request, 'userAccount/createUserAcc.html', {'form': form})

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
@flexible_access('admin')
def create_district(request):
    if request.method == 'POST':
        form = CreateDistrict(request.POST)
        if form.is_valid():
            district_names = form.cleaned_data['district_names']
            district_list = [name.strip().upper() for name in district_names.split(';') if name.strip()]

            for name in district_list:
                district, created = District.objects.get_or_create(district_name=name)
                if created:
                    try:
                        grpc_generate_user_and_votingcurr_run(district_id=district.district_id, voter_num=20)
                    except GrpcError as grpc_error:
                        # Handle gRPC errors
                        print(f"Error in gRPC call: {grpc_error}")
                        messages.error(request, f"Error in gRPC call: {grpc_error}")
                    except Exception as e:
                        # Handle other exceptions
                        print(f"Unexpected error: {e}")
                        messages.error(request, f"Error: {e}")

            messages.success(request, 'District(s) successfully created.')
            return redirect('create_district')  # Redirect to clear the form and show the success message
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = CreateDistrict()

    return render(request, 'district/createDistrict.html', {'form': form})

@flexible_access('public', 'admin')
def view_district(request):
    query = request.GET.get('search', '')
    if query:
        # Filter districts where the search query matches the name field
        districts = District.objects.filter(district_name__icontains=query)
    else:
        districts = District.objects.all()
    
    # for general user
    if not request.user.is_authenticated:
        return render(request, 'generalUser/viewAllDistricts.html', {'districts': districts})
    
    current_phase = ElectionPhase.objects.filter(is_active=True).first()
    disable_deletion = current_phase and current_phase.phase_name in ['Cooling Off Day', 'Polling Day']

    return render(request, 'district/viewDistrict.html', {'districts': districts, 'disable_deletion': disable_deletion})

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
    list(messages.get_messages(request))
    return render(request, 'Voter/voterPg.html', {
        'candidates': candidates,
        'user_district': user_district,
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

    return render(request, 'Candidate/candidatePg.html', {
        'profile_picture_form': profile_picture_form,
        'election_poster_form': election_poster_form,
        'candidate_statement_form': candidate_statement_form,
        'candidate_profile': candidate_profile,
        'is_owner': is_owner
    })

@flexible_access('candidate')
def upload_election_poster(request):
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
    district = get_object_or_404(District, pk=district_id)
    candidates = CandidateProfile.objects.filter(candidate__district=district)
    return render(request, 'generalUser/viewDistrictDetail.html', {
        'district': district,
        'candidates': candidates,
    })


#------------------------------------------------- WebAuthn------------------------------------------------------
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from webauthn import ( generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response, options_to_json)
from .models import WebauthnRegistration, WebauthnCredentials
import json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from webauthn import (generate_registration_options, verify_registration_response,options_to_json)
from django.views.decorators.http import require_http_methods

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
        
        WebauthnRegistration.objects.update_or_create(
            user=request.user,
            defaults={'challenge': options.challenge}
        )
        
        print("WebauthnRegistration updated/created successfully")
        
        json_options = options_to_json(options)
        print("JSON Options:", json_options)
        print("JSON Options type:", type(json_options))
        
        # Ensure json_options is a dictionary, not a string
        if isinstance(json_options, str):
            json_options = json.loads(json_options)
        
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
        verification = verify_registration_response(
            credential=data,
            expected_challenge=registration.challenge,
            expected_origin='https://localhost:8000',
            expected_rp_id='localhost'
        )
        if verification.success:
            WebauthnCredentials.objects.create(
                user=request.user,
                credential_id=verification.credential_id,
                credential_public_key=verification.credential_public_key,
                current_sign_count=verification.sign_count
            )
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Verification failed'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_http_methods(["GET"])
def webauthn_login_options(request):
    options = generate_authentication_options(
        rp_id='localhost',
        allow_credentials=[
            {
                'id': base64url_to_bytes(cred.credential_id),
                'type': 'public-key'
            } for cred in request.user.webauthn_credentials.all()
        ]
    )
    request.user.webauthnregistration.challenge = options.challenge
    request.user.webauthnregistration.save()
    return JsonResponse(options_to_json(options), safe=False)

@login_required
@require_http_methods(["POST"])
def webauthn_login_verify(request):
    try:
        registration = WebauthnRegistration.objects.get(user=request.user)
        data = json.loads(request.body)
        verification = verify_authentication_response(
            credential=data,
            expected_challenge=registration.challenge,
            expected_origin='https://localhost:8000',
            expected_rp_id='localhost',
            credential_public_key=request.user.webauthn_credentials.get(credential_id=data['id']).credential_public_key,
            credential_current_sign_count=request.user.webauthn_credentials.get(credential_id=data['id']).current_sign_count
        )
        if verification.success:
            credential = request.user.webauthn_credentials.get(credential_id=data['id'])
            credential.current_sign_count = verification.sign_count
            credential.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Verification failed'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def webauthn_register_view(request):
    return render(request, 'webauthn_register.html')

def webauthn_login_view(request):
    return render(request, 'webauthn_login.html')
