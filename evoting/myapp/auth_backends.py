from django.contrib.auth.backends import BaseBackend
from myapp.models import SingpassUser, Voter
from django.utils import timezone
from django.contrib.auth.hashers import check_password
import hashlib
import base64
import os

class SingpassBackend(BaseBackend):
    def authenticate(self, request, singpass_id=None, password=None, **kwargs):
        try:
            singpass_user = SingpassUser.objects.get(singpass_id=singpass_id)
            if check_password(password, singpass_user.password):
                hash_info, salt = self.generate_hash(singpass_user)
                # Fetch voter with matching district and hash_info
                voter = Voter.objects.filter(district__district_name=singpass_user.district.upper(), hash_from_info=hash_info).first()
                if not voter:
                    # If no voter found with matching hash_info, fetch voter with empty hash_info
                    voter = Voter.objects.filter(district__district_name=singpass_user.district.upper(), hash_from_info=None).first()
                    if voter:
                        # Voter found with empty hash_info, update hash_info and last_login
                        voter.hash_from_info = hash_info
                        voter.salt = salt
                        voter.last_login = timezone.now()
                        voter.save(update_fields=['last_login', 'hash_from_info', 'salt'])
                    else:
                        # No voter found with either empty or matching hash_info
                        return None
                else:
                    # Voter found with matching hash_info, update last_login
                    voter.last_login = timezone.now()
                    voter.save(update_fields=['last_login'])
                
                return voter
            
        except SingpassUser.DoesNotExist:
            return None
        
    def get_user(self, voter_id):
        try:
            return Voter.objects.get(pk=voter_id)
        except Voter.DoesNotExist:
            return None

    def generate_hash(self, singpass_user):
        salt = base64.b64encode(os.urandom(32)).decode('utf-8')
        hash_input = f"{singpass_user.singpass_id}{singpass_user.full_name}{singpass_user.date_of_birth}{singpass_user.phone_num}{singpass_user.district}{salt}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        print(hash_value)
        return hash_value, salt