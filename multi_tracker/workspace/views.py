from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Case, When, Value, IntegerField, Count
from datetime import datetime, timedelta
from collections import Counter

from .models import UserProfile, LeaveRequest, AttendanceRecord, User
from .forms import CustomUserCreationForm, AttendanceRecordForm, LeaveRequestForm


# Home View
def home(request):
    """
    Public landing page with the current year.
    """
    year = datetime.now().year
    return render(request, 'workspace/landing.html', {"year": year})


# Register View
def register(request):
    """
    User registration using the custom form.
    Redirects to the dashboard upon successful registration.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set default backend explicitly
            user.backend = settings.AUTHENTICATION_BACKENDS[0]  
            login(request, user)
            return redirect('dashboard')  # Redirect to the user dashboard
    else:
        form = CustomUserCreationForm()

    # Pass the form to the template
    return render(request, 'workspace/register.html', {'form': form})


# Login View
class CustomLoginView(LoginView):
    """
    Custom login view with a tailored template.
    """
    template_name = 'workspace/login.html'


# Logout View
@login_required
def custom_logout(request):
    """
    Logs out the user and redirects to the home page.
    """
    logout(request)
    return redirect('home')


# Dashboard View
@login_required
def dashboard(request):
    """
    User dashboard displaying reminders, attendance summaries, and leave requests for managers.
    """
    today = now().date()

    # Static reminders (e.g., bank holidays)
    reminders = [
        {"title": "Christmas Day", "date": datetime(2024, 12, 25).date()},
        {"title": "Boxing Day", "date": datetime(2024, 12, 26).date()},
        {"title": "New Year's Day", "date": datetime(2025, 1, 1).date()},
        {"title": "Good Friday", "date": datetime(2025, 4, 18).date()},
        {"title": "Easter Monday", "date": datetime(2025, 4, 21).date()},
        {"title": "Early May Bank Holiday", "date": datetime(2025, 5, 5).date()},
    ]

    # Separate past and upcoming reminders
    past_reminders = [r for r in reminders if r["date"] < today]
    upcoming_reminders = [r for r in reminders if r["date"] >= today]

    # Attendance Summary
    attendance_records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')[:5]

    # Manager-specific leave requests
    leave_requests = []
    if hasattr(request.user, 'profile') and request.user.profile.is_manager:
        leave_requests = LeaveRequest.objects.filter(
            manager=request.user, 
            status='P'
        ).order_by('-start_date')

    context = {
        "past_reminders": past_reminders,
        "upcoming_reminders": upcoming_reminders,
        "attendance_records": attendance_records,
        "leave_requests": leave_requests,
    }

    return render(request, 'workspace/dashboard.html', context)


# Leave Request List View
@login_required
def leave_request_list(request):
    """
    Displays leave requests for the logged-in user.
    """
    leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'workspace/leave_request_list.html', {'leave_requests': leave_requests})


# Attendance Record Views
@login_required
def attendance_list(request):
    """
    Displays a list of attendance records for the logged-in user.
    """
    records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')
    return render(request, 'workspace/attendance_list.html', {'records': records})


@login_required
def attendance_create(request):
    """
    Handles the creation of attendance records.
    """
    if request.method == 'POST':
        form = AttendanceRecordForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.user = request.user
            attendance.tenant = request.user.profile.tenant
            attendance.save()
            return redirect('attendance_list')
    else:
        form = AttendanceRecordForm()

    return render(request, 'workspace/attendance_create.html', {'form': form})


@login_required
def attendance_delete(request, pk):
    """
    Deletes an attendance record.
    """
    record = get_object_or_404(AttendanceRecord, pk=pk, user=request.user)
    record.delete()
    return redirect('attendance_list')


# Leave Request Approval for Managers
@login_required
def approve_leave(request, leave_id):
    """
    Approves a leave request by a manager.
    """
    leave = get_object_or_404(LeaveRequest, id=leave_id, manager=request.user)
    leave.status = 'A'
    leave.save()
    return redirect('dashboard')


@login_required
def reject_leave(request, leave_id):
    """
    Rejects a leave request by a manager.
    """
    leave = get_object_or_404(LeaveRequest, id=leave_id, manager=request.user)
    leave.status = 'R'
    leave.save()
    return redirect('dashboard')


# Attendance Summary (Utility)
def get_attendance_counts_for_month(user):
    """
    Counts attendance records for the current month.
    """
    current_month = now().month
    current_year = now().year
    records = AttendanceRecord.objects.filter(
        user=user, 
        date__year=current_year, 
        date__month=current_month
    )
    counts = Counter(record.type for record in records)
    return dict(counts)
