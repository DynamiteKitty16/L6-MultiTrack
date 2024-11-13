from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Django's built-in auth views

    # Modular URLs
    path('tenant/', include('multi_tracker.tenant_urls')),         # Tenant admin-specific views
    path('manager/', include('multi_tracker.manager_urls')),       # Manager-specific views
    path('', include('multi_tracker.user_urls')),                  # Regular user views (home, login, etc.)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
