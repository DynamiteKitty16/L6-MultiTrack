from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from workspace.models import UserProfile

def tenant_admin_required(view_func):
    """Allows access only to users with UserProfile's is_tenant_admin=True"""
    decorated_view_func = user_passes_test(
        lambda u: hasattr(u, 'userprofile') and u.userprofile.is_tenant_admin,
        login_url='/login/'
    )(view_func)
    return decorated_view_func

def manager_required(view_func):
    """Allows access only to users with UserProfile's is_manager=True"""
    decorated_view_func = user_passes_test(
        lambda u: hasattr(u, 'userprofile') and u.userprofile.is_manager,
        login_url='/login/'
    )(view_func)
    return decorated_view_func
