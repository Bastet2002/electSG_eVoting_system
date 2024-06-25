from django.test import TestCase
from django.utils import timezone
from ..models import (
    SingpassUser,
    Profile,
    District,
    UserAccount,
    CandidatePublicKey,
    CandidateProfile,
    VoteResults,
    Party,
    Announcement,
    ElectionPhase,
    VoteRecords,
    VotingCurrency,
    Voter,
)
import json

class ModelsTestCase(TestCase):

    def setUp(self):
        self.district = District.objects.create(district_name="Central District")
        self.profile = Profile.objects.create(profile_name="Administrator", description="Admin Profile")
        self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")
        self.singpass_user = SingpassUser.objects.create(
            singpass_id="SP001",
            password="password123",
            full_name="John Doe",
            date_of_birth="1990-01-01",
            phone_num="12345678",
            district="Central District"
        )
        self.user_account = UserAccount.objects.create(
            username="john_doe",
            password="password123",
            full_name="John Doe",
            date_of_birth="1990-01-01",
            role=self.profile,
            district=self.district,
            party=self.party
        )
        self.candidate_profile = CandidateProfile.objects.create(
            candidate=self.user_account,
            candidate_statement="Vote for me!"
        )
        self.vote_result = VoteResults.objects.create(
            candidate=self.user_account,
            total_vote=100
        )
        self.announcement = Announcement.objects.create(
            header="Election Day",
            content="The election will be held on the 1st of November."
        )
        self.election_phase = ElectionPhase.objects.create(
            phase_name="Voting",
            is_active=True
        )
        self.vote_record = VoteRecords.objects.create(
            key_image="abcd1234",
            district=self.district,
            transaction_record=json.dumps({"txid": "1234"})
        )
        self.voting_currency = VotingCurrency.objects.create(
            district=self.district,
            stealth_address="stealth1234",
            commitment_record=json.dumps({"commitment": "abcd"})
        )
        self.voter = Voter.objects.create(
            district=self.district,
            hash_from_info="hash1234",
            pkv="pkv1234",
            last_login=timezone.now()
        )

    def test_singpass_user_creation(self):
        self.assertEqual(self.singpass_user.singpass_id, "SP001")

    def test_profile_creation(self):
        self.assertEqual(self.profile.profile_name, "Administrator")

    def test_district_creation(self):
        self.assertEqual(self.district.district_name, "Central District")

    def test_user_account_creation(self):
        self.assertEqual(self.user_account.username, "john_doe")
        self.assertEqual(self.user_account.role, self.profile)
        self.assertEqual(self.user_account.district, self.district)
        self.assertEqual(self.user_account.party, self.party)

    def test_candidate_profile_creation(self):
        self.assertEqual(self.candidate_profile.candidate, self.user_account)

    def test_vote_result_creation(self):
        self.assertEqual(self.vote_result.total_vote, 100)

    def test_announcement_creation(self):
        self.assertEqual(self.announcement.header, "Election Day")

    def test_election_phase_creation(self):
        self.assertEqual(self.election_phase.phase_name, "Voting")
        self.assertTrue(self.election_phase.is_active)

    def test_vote_record_creation(self):
        self.assertEqual(self.vote_record.key_image, "abcd1234")
        self.assertEqual(self.vote_record.district, self.district)

    def test_voting_currency_creation(self):
        self.assertEqual(self.voting_currency.stealth_address, "stealth1234")
        self.assertEqual(self.voting_currency.district, self.district)

    def test_voter_creation(self):
        self.assertEqual(self.voter.hash_from_info, "hash1234")
        self.assertEqual(self.voter.district, self.district)
        self.assertEqual(self.voter.pkv, "pkv1234")
        self.assertTrue(self.voter.is_authenticated)
