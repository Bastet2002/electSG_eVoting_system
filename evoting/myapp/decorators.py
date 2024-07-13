from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .models import UserAccount, Voter

# def user_type_required(*allowed_types):
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped_view(request, *args, **kwargs):
#             if not request.user.is_authenticated:
#                 return redirect('login')  # Redirect to login page if not authenticated

#             # Check if the user is a voter
#             if 'voter' in allowed_types:
#                 try:
#                     voter = Voter.objects.get(pkv=request.user.username)
#                     return view_func(request, *args, **kwargs)
#                 except Voter.DoesNotExist:
#                     pass

#             # Check if the user is an admin or candidate
#             if request.user.is_authenticated and isinstance(request.user, UserAccount):
#                 if request.user.role:
#                     user_type = request.user.role.name.lower()
#                     if user_type in allowed_types:
#                         return view_func(request, *args, **kwargs)

#             # If user type doesn't match, forbid access
#             return HttpResponseForbidden("You don't have permission to access this page.")
#         return _wrapped_view
#     return decorator

# def public_view(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         # Allow access to all users, including unauthenticated ones
#         return view_func(request, *args, **kwargs)
#     return _wrapped_view


def flexible_access(*allowed_types):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_type = 'public'
            
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