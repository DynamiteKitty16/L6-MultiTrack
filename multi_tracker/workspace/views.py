from django.shortcuts import render, get_object_or_404, redirect
from .models import AttendanceRecord, LeaveRequest
from django.contrib.auth.decorators import login_required
from .forms import AttendanceRecordForm
from .decorators import tenant_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.utils.timezone import now
from datetime import datetime

# Login view
class CustomLoginView(LoginView):
    template_name = 'workspace/login.html'

# Home view
def home(request):
    """Public landing page"""
    return render(request, 'workspace/landing.html')

# Landing page redirect for register / login
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'workspace/register.html', {'form': form})

# Default dashboard
@login_required
def dashboard(request):
    """User dashboard with reminders and summaries"""
    today = now().date()

    # Reminders of non-workingdays
    reminders = [
        {"title": "Christmas Day", "date": datetime(2024, 12, 25).date()},
        {"title": "Boxing Day", "date": datetime(2024, 12, 26).date()},
        {"title": "New Year's Day", "date": datetime(2025, 1, 1).date()},
        {"title": "Good Friday", "date": datetime(2025, 4, 21).date()},
        {"title": "Easter Monday", "date": datetime(2025, 4, 21).date()},
        {"title": "Early May Bank Holiday", "date": datetime(2025, 5, 5).date()},
        {"title": "Spring Bank Holiday", "date": datetime(2025, 5, 26).date()},
        {"title": "Summer Bank Holiday", "date": datetime(2025, 8, 25).date()},
        {"title": "Christmas Day", "date": datetime(2025, 12, 25).date()},
        {"title": "Boxing Day", "date": datetime(2025, 12, 26).date()},
    ]

    #Seperate past and upcoming reminders
    past_reminders = [r for r in reminders if r["date"] <today]
    upcoming_reminders = [r for r in reminders if r["date"] >=today]

    # Attendence Summary
    attendance_records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')[:5]

    # if a user is a manager, fetch team leave requests
    leave_requests = []
    if request.user.userprofile.is_manager:
        leave_requests = LeaveRequest.objects.filter(manager=request.user, status='P').order_by('-start_date')
    
    context = {
        "past_reminders": past_reminders,
        "upcoming_reminders": upcoming_reminders,
        "attendance_records": attendance_records,
        "leave_requests": leave_requests,
    }

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
    records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')
    return render(request, 'workspace/attendance-list.html', {'records': records})

# AttendanceRecord Create View
@login_required
@tenant_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceRecordForm (request.POST)
        if form.is_valid():
            # Save the form data to create the record
            attendance = form.save(commit=False)
            attendance.user = request.user
            attendance.tenant = request.user.userprofile.tenant
            attendance.save()
            return redirect('attendance_list')
        
    else:
        form = AttendanceRecordForm()

    return render(request, 'workspace/attendance_create.html', {'form': form})

# AttendanceRecord Delete View
@login_required
@tenant_required
def attendance_delete(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk, user=request.user)
    record.delete()
    return redirect('attendance_list')

# Manager approve leave
@login_required
def approve_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id, manager=request.user)
    leave.status = 'A'
    leave.save()
    return redirect('dashboard')

# Manager reject leave
@login_required
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id, manager=request.user)
    leave.status = 'R'
    leave.save()
    return redirect('dashboard')
