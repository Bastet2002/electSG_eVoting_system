from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapp.models import UserAccount, Profile, Party, District, CandidateProfile, VoteResults
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
import random
from myapp.forms import CreateNewUser
from faker import Faker
from . import config
from pygrpc.ringct_client import (
    grpc_generate_candidate_keys_run
)
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create initial candidate accounts'

    def handle(self, *args, **kwargs):
        fake = Faker()
        candidate_profile = Profile.objects.get_or_create(profile_name='Candidate')[0]
        parties = Party.objects.all()
        districts = District.objects.all()

        for _ in range(config.candidate_num_total):
            name = fake.name()
            if not UserAccount.objects.filter(full_name=name).exists():
                # Generate a random date of birth (between 55 and 65 years ago)
                dob = datetime.now() - timedelta(days=random.randint(55*365, 65*365))
                
                form_data = {
                    'username': name.lower().replace(" ", "_"),
                    'full_name': name,
                    'date_of_birth': dob.date(),
                    'password': 'Password1!', 
                    'role': candidate_profile.profile_id,
                    'party': random.choice(parties).party_id,
                    'district': random.choice(districts).district_id
                }

                form = CreateNewUser(data=form_data)
                if form.is_valid():
                    candidate = form.save(commit=False)
                    candidate.password = make_password(form.cleaned_data['password'])
                    candidate.save()
                    logger.info(f'Created candidate account: {candidate.full_name}')
                else:
                    logger.warning(f'Failed to create candidate account: {name}. Errors: {form.errors}')
            else:
                logger.warning(f'Candidate account already exists: {name}')

        logger.info('Candidate account creation completed')

        # Retrieve all candidate IDs
        candidate_ids = UserAccount.objects.filter(role=candidate_profile).values_list('user_id', flat=True)

        for candidate_id in candidate_ids:
            candidate = UserAccount.objects.get(user_id=candidate_id)
            CandidateProfile.objects.create(candidate=candidate)
            VoteResults.objects.create(candidate=candidate, total_vote=0)
            grpc_generate_candidate_keys_run(candidate_id=candidate_id)
            logger.info(f'Called gRPC service for candidate: {candidate.full_name}')
        
        logger.info('Candidate RingCT key generation completed')