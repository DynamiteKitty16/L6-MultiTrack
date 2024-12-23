from datetime import timedelta
from django.utils.timezone import now
from django.conf import settings

class SessionTimeoutMiddleware:
    """
    Middleware to enforce session timeouts for authenticated users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Get the last activity timestamp
            last_activity = request.session.get('last_activity', now())

            # Timeout period in seconds (15 minutes = 900 seconds)
            timeout = getattr(settings, 'SESSION_TIMEOUT', 900)  # Default to 15 minutes
            if (now() - last_activity).total_seconds() > timeout:
                from django.contrib.auth import logout
                logout(request)  # Log the user out
            else:
                # Update last activity
                request.session['last_activity'] = now()
        return self.get_response(request)
