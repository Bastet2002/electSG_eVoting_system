from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from myapp.models import TemporaryVoter

class TemporaryVoterBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            temp_voter = TemporaryVoter.objects.get(username=username)
            if check_password(password, temp_voter.password):
                temp_voter.last_login = timezone.now()
                temp_voter.save(update_fields=['last_login'])
                return temp_voter
        except TemporaryVoter.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return TemporaryVoter.objects.get(pk=user_id)
        except TemporaryVoter.DoesNotExist:
            return None
