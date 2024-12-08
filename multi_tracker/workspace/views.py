from django.shortcuts import render, get_object_or_404, redirect
from .models import AttendanceRecord, LeaveRequest
from django.contrib.auth.decorators import login_required
from .decorators import tenant_required
from django.contrib.auth.views import LoginView

# Login view
class CustomLoginView(LoginView):
    template_name = 'workspace/login.html'

# Home view
def home(request):
    """Public landing page"""
    return render(request, 'workspace/home.html')

# Default dashboard
@login_required
def dashboard(request):
    """User dashboard"""
    return render(request, 'workspace/dashboard.html')

# Updated leave requests
@login_required
def leave_request_list(request):
    """
    Displays a list of leave requests for the logged-in user.
    """
    leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-start_date')
    context = {'leave_requests': leave_requests}
    return render(request, 'workspace/leave_request_list.html', context)

# AttendanceRecord List View
@login_required
@tenant_required
def attendance_list(request):
    records = AttendanceRecord.objects.filter(user=request.user)
    return render(request, 'attendance/list.html', {'records': records})

# AttendanceRecord Create View
@login_required
@tenant_required
def attendance_create(request):
    if request.method == 'POST':
        # Handle form submission
        tenant = request.user.profile.tenant
        AttendanceRecord.objects.create(
            user=request.user,
            tenant=tenant,
            date=request.POST.get('date'),
            type=request.POST.get('type'),
        )
        return redirect('attendance_list')
    return render(request, 'attendance/create.html')

# AttendanceRecord Delete View
@login_required
@tenant_required
def attendance_delete(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk, user=request.user)
    record.delete()
    return redirect('attendance_list')
