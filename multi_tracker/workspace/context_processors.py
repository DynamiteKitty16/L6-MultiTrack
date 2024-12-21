from django.conf import settings

def session_expiry(request):
    """
    Adds session expiry time to the context for authenticated users.
    """
    if request.user.is_authenticated:
        return {"session_expiry": request.session.get_expiry_age()}
    return {}
