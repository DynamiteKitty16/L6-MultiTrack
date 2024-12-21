from datetime import datetime
from django.contrib.auth import logout

class UpdateLastActivityMiddleware:
    """
    Middleware to track the user's last activity for session timeout handling.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update session with the user's last activity timestamp
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
            # Get the last activity timestamp from the session
            last_activity = request.session.get('last_activity', datetime.now().timestamp())
            # Calculate the time elapsed since the last activity
            time_elapsed = datetime.now().timestamp() - last_activity
            # If the time elapsed exceeds the session timeout, log out the user
            if time_elapsed > 180:  # Timeout set to 3 minutes
                logout(request)
        return self.get_response(request)
