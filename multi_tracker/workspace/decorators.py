from django.http import HttpResponseForbidden
from functools import wraps

def tenant_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.tenant:
            return HttpResponseForbidden("You must belong to a tenant to access this view.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
