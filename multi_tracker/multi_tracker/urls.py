from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from workspace import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Custom URLs
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('leave-requests/', views.leave_request_list, name='leave_requests'),
    
    #
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
