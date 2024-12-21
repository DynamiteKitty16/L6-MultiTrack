from datetime import datetime

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
