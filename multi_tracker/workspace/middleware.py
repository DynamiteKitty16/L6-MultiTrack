from datetime import datetime
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

class UpdateLastActivityMiddleware:
    """
    Middleware to track the user's last activity for session timeout handling.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.session['last_activity'] = datetime.now().timestamp()
        return self.get_response(request)


class SessionTimeoutMiddleware:
    """
    Middleware to enforce session timeout based on user inactivity.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity', datetime.now().timestamp())
            time_elapsed = datetime.now().timestamp() - last_activity
            if time_elapsed > 180:  # Timeout set to 3 minutes
                logout(request)
                return redirect('login')  # Redirect to login page
        return self.get_response(request)


@receiver(user_logged_in)
def set_last_activity(sender, request, user, **kwargs):
    """
    Signal to set the initial last_activity timestamp on user login.
    """
    request.session['last_activity'] = datetime.now().timestamp()
