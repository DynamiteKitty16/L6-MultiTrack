from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Case, When, Value, IntegerField, Count
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import get_connection, EmailMessage
from django.contrib.auth.tokens import default_token_generator
from datetime import datetime, timedelta
from collections import Counter

import ssl
import certifi

from .models import UserProfile, LeaveRequest, AttendanceRecord, User
from .forms import CustomUserCreationForm, AttendanceRecordForm, LeaveRequestForm


# Home View
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'workspace/landing.html', {"year": datetime.now().year})


# Register View with Email Verification
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Set user as inactive until email verification
            user.save()

            UserProfile.objects.get_or_create(user=user)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_link = request.build_absolute_uri(
                reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
            )

            subject = 'Verify Your Email Address'
            message = render_to_string('workspace/email_verification.html', {
                'user': user,
                'verification_link': verification_link,
            })

            secure_connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=True,
                ssl_context=ssl.create_default_context(cafile=certifi.where())
            )

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
                connection=secure_connection,
            )
            email.content_subtype = "html"
            email.send()

            messages.success(request, "Account created! Please check your email to verify your account.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'workspace/register.html', {'form': form})


# Email Verification View
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.is_email_verified = True
        profile.save()

        messages.success(request, "Email verified! You can now log in.")
        return redirect('login')
    else:
        return HttpResponse("Verification link is invalid or has expired.", status=400)


# Login View
class CustomLoginView(LoginView):
    template_name = 'workspace/login.html'


# Logout View
@login_required
def custom_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')


# Handling timeout
@login_required
def session_timeout_warning(request):
    """
    Refresh session when the user confirms staying logged in.
    """
    if request.method == "GET":
        request.session.modified = True
        return JsonResponse({"message": "Session refreshed successfully."})
    return JsonResponse({"error": "Invalid request method."}, status=400)


# Dashboard View
@login_required
def dashboard(request):
    today = now().date()

    reminders = [
        {"title": "Christmas Day", "date": datetime(2024, 12, 25).date()},
        {"title": "Boxing Day", "date": datetime(2024, 12, 26).date()},
        {"title": "New Year's Day", "date": datetime(2025, 1, 1).date()},
        {"title": "Good Friday", "date": datetime(2025, 4, 18).date()},
        {"title": "Easter Monday", "date": datetime(2025, 4, 21).date()},
        {"title": "Early May Bank Holiday", "date": datetime(2025, 5, 5).date()},
    ]

    past_reminders = [r for r in reminders if r["date"] < today]
    upcoming_reminders = [r for r in reminders if r["date"] >= today]

    attendance_records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')[:5]

    leave_requests = []
    if hasattr(request.user, 'profile') and request.user.profile.is_manager:
        leave_requests = LeaveRequest.objects.filter(manager=request.user, status='P').order_by('-start_date')

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
    leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'workspace/leave_request_list.html', {'leave_requests': leave_requests})


# Attendance Record Views
@login_required
def attendance_list(request):
    records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')
    return render(request, 'workspace/attendance_list.html', {'records': records})


@login_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceRecordForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.user = request.user
            attendance.save()
            return redirect('attendance_list')
    else:
        form = AttendanceRecordForm()

    return render(request, 'workspace/attendance_create.html', {'form': form})


@login_required
def attendance_delete(request, pk):
    record = get_object_or_404(AttendanceRecord, pk=pk, user=request.user)
    record.delete()
    return redirect('attendance_list')


# Leave Request Approval for Managers
@login_required
def approve_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id, manager=request.user)
    leave.status = 'A'
    leave.save()
    return redirect('dashboard')


@login_required
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id, manager=request.user)
    leave.status = 'R'
    leave.save()
    return redirect('dashboard')


# Attendance Summary (Utility)
def get_attendance_counts_for_month(user):
    current_month = now().month
    current_year = now().year
    records = AttendanceRecord.objects.filter(user=user, date__year=current_year, date__month=current_month)
    counts = Counter(record.type for record in records)
    return dict(counts)
