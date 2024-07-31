from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .models import UserAccount, Voter
import os

def flexible_access(*allowed_types):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # TODO remove this after stress test
            if os.environ.get('ENVIRONMENT') == 'dev' and request.headers.get('X-Locust-Test'):
                return view_func(request, *args, **kwargs)

            user_type = 'public'
            if user_type in allowed_types:
                return view_func(request, *args, **kwargs)
            
            if request.user.is_authenticated:
                if isinstance(request.user, UserAccount):
                    user_type = request.user.role.profile_name.lower() if request.user.role else 'authenticated'
                elif isinstance(request.user, Voter):
                    user_type = 'voter'
            
            if user_type in allowed_types:
                return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("You don't have permission to access this page.")
        return _wrapped_view
    return decorator