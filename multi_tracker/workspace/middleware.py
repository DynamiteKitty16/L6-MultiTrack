from datetime import datetime, timedelta
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.timezone import now, make_aware
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in


class UpdateLastActivityMiddleware:
    """
    Middleware to track the user's last activity for session timeout handling.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip updating for static files or unauthenticated users
        if request.user.is_authenticated and not request.path.startswith(('/static/', '/logout/')):
            request.session['last_activity'] = now().timestamp()  # Use timezone-aware now
        return self.get_response(request)


class SessionTimeoutMiddleware:
    """
    Middleware to enforce session timeout based on user inactivity.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                # Ensure last_activity is timezone-aware
                last_activity_time = make_aware(datetime.fromtimestamp(last_activity))
                
                # Check if the timeout period has passed
                if now() - last_activity_time > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    logout(request)
                    return redirect('login')
            else:
                # Set initial last activity if not present
                request.session['last_activity'] = now().timestamp()

        return self.get_response(request)


@receiver(user_logged_in)
def set_last_activity(sender, request, user, **kwargs):
    """
    Signal to set the initial last_activity timestamp on user login.
    """
    request.session['last_activity'] = now().timestamp()
