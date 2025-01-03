from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from workspace import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/login/', LoginView.as_view(template_name='workspace/login.html'), name='login'),
    path('accounts/logout/', views.custom_logout, name='custom_logout'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Custom URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('leave-requests/', views.leave_request_list, name='leave_requests'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),

    # Handling timeout
    path('session_timeout_warning/', views.session_timeout_warning, name='session_timeout_warning'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)