from datetime import datetime
from django.utils.timezone import now
from django.conf import settings
from django.contrib.auth import logout


class SessionTimeoutMiddleware:
    """
    Middleware to enforce session timeouts for authenticated users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Get the last activity timestamp from the session
            last_activity = request.session.get('last_activity')
            
            # Timeout period in seconds (default to 15 minutes = 900 seconds)
            timeout = getattr(settings, 'SESSION_TIMEOUT', 900)

            if last_activity:
                try:
                    # Convert ISO string back to datetime object
                    last_activity = datetime.fromisoformat(last_activity)
                except ValueError:
                    # If deserialization fails, log out the user
                    logout(request)
                    request.session.flush()
                    return self.get_response(request)

                # Check if the session has timed out
                if (now() - last_activity).total_seconds() > timeout:
                    logout(request)  # Log out the user
                    request.session.flush()  # Clear the session
                    return self.get_response(request)

            # Update the last activity timestamp in the session
            request.session['last_activity'] = now().isoformat()

        return self.get_response(request)


class UpdateLastActivityMiddleware:
    """
    Middleware to update the 'last_activity' timestamp in the session for authenticated users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only update if the user is authenticated
        if request.user.is_authenticated:
            # Store the current timestamp as an ISO string
            request.session['last_activity'] = now().isoformat()
        return self.get_response(request)
