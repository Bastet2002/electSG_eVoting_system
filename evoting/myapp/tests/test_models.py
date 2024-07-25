from django.test import TestCase
from django.utils import timezone
from django.db.utils import DataError, IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
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
        self.district = District.objects.create(district_name="Central District", num_of_people=10)
        self.profile = Profile.objects.create(profile_name="Administrator", description="Admin Profile")
        self.party = Party.objects.create(party_name="Democratic Party", description="Democratic Party Description")
        self.singpass_user = SingpassUser.objects.create(
            singpass_id="SP001",
            password="Password123!",
            full_name="John Doe",
            date_of_birth="1990-01-01",
            phone_num="12345678",
            district="Central District"
        )
        self.user_account_one = UserAccount.objects.create(
            username="john_doe",
            password="Password123!",
            full_name="John Doe",
            date_of_birth="1990-01-01",
            role=self.profile,
            district=self.district,
            party=self.party
        )
        self.user_account_two = UserAccount.objects.create(
            username="testuser",
            password="Password123!",
            full_name="John Doe",
            date_of_birth="1990-01-01",
            role=self.profile,
            district=self.district,
            party=self.party
        )
        self.candidate_profile = CandidateProfile.objects.create(
            candidate=self.user_account_one,
            candidate_statement="Vote for me!"
        )
        self.candidate_public_key = CandidatePublicKey.objects.create(
            candidate=self.user_account_one,
            pkv="pkv123456",
            pks="pks123456"
        )
        self.vote_result = VoteResults.objects.create(
            candidate=self.user_account_one,
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
        self.assertEqual(self.district.district_name, "Central District".upper())

    def test_user_account_creation(self):
        self.assertEqual(self.user_account_one.username, "john_doe")
        self.assertEqual(self.user_account_one.role, self.profile)
        self.assertEqual(self.user_account_one.district, self.district)
        self.assertEqual(self.user_account_one.party, self.party)

    def test_candidate_profile_creation(self):
        self.assertEqual(self.candidate_profile.candidate, self.user_account_one)

    def test_candidate_public_key_creation(self):
        self.assertEqual(self.candidate_public_key.candidate, self.user_account_one)
        self.assertEqual(self.candidate_public_key.pkv, "pkv123456")
        self.assertEqual(self.candidate_public_key.pks, "pks123456")

    def test_vote_result_creation(self):
        self.assertEqual(self.vote_result.total_vote, 100)

    def test_party_creation(self):
        self.assertEqual(self.party.party_name, "Democratic Party")

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

    # Invalid inputs
    def test_invalid_singpass_user_creation(self):
        with self.assertRaises(IntegrityError):
            SingpassUser.objects.create(
                singpass_id="SP002",
                password=None,  # Invalid password (None)
                full_name="John Doe",
                date_of_birth="1990-01-01",
                phone_num="12345678",
                district="Central District"
            )

    def test_invalid_profile_creation(self):
        with self.assertRaises(ValidationError):
            Profile.objects.create(profile_name=None, description="Candidate Profile")  # Invalid profile_name (None)

    def test_invalid_district_creation(self):
        with self.assertRaises(ValidationError):
            District.objects.create(district_name=None)  # Invalid district_name (None)

    def test_invalid_user_account_creation(self):
        with self.assertRaises(ValidationError):
            UserAccount.objects.create(
                username=None,  # Invalid username (length 26)
                password="Password123!",
                full_name="John Doe",
                date_of_birth="1990-01-01",
                role=self.profile,
                district=self.district,
                party=self.party
            )

    def test_invalid_candidate_profile_creation(self):
        with self.assertRaises(ValidationError):
            CandidateProfile.objects.create(
                candidate=None,  # Invalid candidate (None)
                profile_picture=None,
                election_poster=None,
                candidate_statement="Vote for me!"
            )

    def test_invalid_candidate_public_key_creation(self):
        with self.assertRaises(IntegrityError):
            CandidatePublicKey.objects.create(
                candidate=None,  # Invalid candidate (None)
                pkv="valid_pkv",
                pks="valid_pks"
            )

    def test_invalid_vote_result_creation(self):
        with self.assertRaises(ValidationError):
            VoteResults.objects.create(
                candidate=None,  # Invalid candidate (None)
                total_vote=10
            )

    def test_invalid_party_creation(self):
        with self.assertRaises(ValidationError):
            Party.objects.create(
                party_name=None  # Invalid party_name (None)
            )

    def test_invalid_announcement_creation(self):
        with self.assertRaises(IntegrityError):
            Announcement.objects.create(
                header=None,  # Invalid header (None)
                content=""
            )

    def test_invalid_election_phase_creation(self):
        with self.assertRaises(ValidationError):
            ElectionPhase.objects.create(
                phase_name=None,  # Invalid phase_name (None)
                is_active=True
            )

    def test_invalid_vote_record_district_creation(self):
        with self.assertRaises(IntegrityError):
            VoteRecords.objects.create(
                key_image="abcd1234",  
                district=None,   # Invalid district (None)
                transaction_record=self.vote_record.transaction_record 
            )
    
    def test_invalid_vote_record_json_creation(self):
        with self.assertRaises(ValidationError):
            VoteRecords.objects.create(
                key_image="x" * 64,
                district=self.district,
                transaction_record="invalid_json"
            )

    def test_invalid_voting_currency_creation(self):
        with self.assertRaises(IntegrityError):
            VotingCurrency.objects.create(
                district=self.district,
                stealth_address=None,  # Invalid stealth_address (None)
                commitment_record="invalid_json"  # Invalid commitment_record (not JSON)
            )

    def test_invalid_voter_creation(self):
        with self.assertRaises(IntegrityError):
            Voter.objects.create(
                district=self.district,
                hash_from_info=None,  # Invalid hash_from_info (None)
                pkv=None,  # Invalid pkv (None)
                last_login="2019-01-19T00:00:00Z"
            )

    # Edge cases
    def test_singpassuser_long_singpass_id(self):
        with self.assertRaises(DataError):
            SingpassUser.objects.create(
                singpass_id="x" * 256,
                password="password123",
                full_name="John Doe",
                date_of_birth="1990-01-01",
                phone_num="1234567890",
                district="Test District"
            )
    
    def test_profile_long_profile_name(self):
        with self.assertRaises(ValidationError):
            Profile.objects.create(profile_name="x" * 256)  # Invalid profile_name (too long)

    def test_district_long_district_name(self):
        with self.assertRaises(ValidationError):
            District.objects.create(district_name="x" * 256)  # Invalid district_name (too long)

    def test_useraccount_long_username(self):
        with self.assertRaises(ValidationError):
            UserAccount.objects.create(
                username="x" * 201,
                password="password123",
                full_name="John Doe",
                date_of_birth="1990-01-01",
                role=self.profile,
                district=self.district,
                party=self.party
            )

    def test_useraccount_duplicate_username(self):
        UserAccount.objects.create(
            username="testinguser",
            password="Password123!",
            full_name="John Doe",
            date_of_birth="1990-01-01",
            role=self.profile,
            district=self.district,
            party=self.party
        )
        with self.assertRaises(ValidationError):
            UserAccount.objects.create(
                username="testinguser",
                password="Password456!",
                full_name="Jane Doe",
                date_of_birth="1991-01-01",
                role=self.profile,
                district=self.district,
                party=self.party
            )

    def test_candidateprofile_large_image_file(self):
        # Create a large image file (5 MB)
        large_image = SimpleUploadedFile(
            name='large_image.jpg',
            content=b'\x00' * 10 * 1024 * 1024,  # 10 MB of zero bytes
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError):
            CandidateProfile.objects.create(
                candidate=self.user_account_two,
                profile_picture=large_image,
                election_poster=large_image,
                candidate_statement="This is a test statement."
            )

    def test_candidatepublickey_invalid_pkv_length(self):
        with self.assertRaises(DataError):
            CandidatePublicKey.objects.create(
                candidate=self.user_account_two,
                pkv="x" * 65,  # Should be max 64 characters
                pks="y" * 64
            )

    def test_voteresults_negative_total_vote(self):
        with self.assertRaises(ValidationError):
            VoteResults.objects.create(candidate=self.user_account_two, total_vote=-1)

    def test_voteresults_big_total_vote(self):
        with self.assertRaises(ValidationError):
            VoteResults.objects.create(candidate=self.user_account_two, total_vote=5000000)

    def test_party_long_party_name(self):
        with self.assertRaises(ValidationError):
            Party.objects.create(party_name="x" * 256)  # Invalid party_name (too long)

    def test_announcement_future_date(self):
        threshold_date = timezone.now()
        future_date = threshold_date + timezone.timedelta(days=1)
        announcement = Announcement.objects.create(
            header="Future Announcement",
            content="This is from the future",
            date=future_date
        )
        self.assertGreater(announcement.date, threshold_date)

    def test_electionphase_multiple_active_phases(self):
        with self.assertRaises(ValidationError):
            ElectionPhase.objects.create(phase_name="Phase 1", is_active=True)
            ElectionPhase.objects.create(phase_name="Phase 2", is_active=True)

    def test_electionphase_long_phase_name(self):
        with self.assertRaises(ValidationError):
            ElectionPhase.objects.create(
                phase_name="x" * 256,
                is_active=False
            )

    def test_voterecords_long_key_image(self):
        with self.assertRaises(DataError):
            VoteRecords.objects.create(
                key_image="x" * 65,
                district=self.district,
                transaction_record=json.dumps({"txid": "12345"})
            )

    def test_votingcurrency_duplicate_stealth_address(self):
        VotingCurrency.objects.create(
            district=self.district,
            stealth_address="x" * 64,
            commitment_record={"some": "data"}
        )
        with self.assertRaises(IntegrityError):
            VotingCurrency.objects.create(
                district=self.district,
                stealth_address="x" * 64,
                commitment_record={"other": "data"}
            )

    def test_voter_long_hash_length(self):
        with self.assertRaises(DataError):
            Voter.objects.create(
                district=self.district,
                hash_from_info="x" * 129,  # Should be max 128 characters
                pkv="y" * 64
            )