from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import get_connection, EmailMessage
from django.contrib.auth.tokens import default_token_generator

import ssl
import certifi
from collections import Counter

from .models import UserProfile, LeaveRequest, AttendanceRecord, User
from .forms import CustomUserCreationForm, AttendanceRecordForm


# Utility function for sending verification emails
def send_verification_email(user, verification_link):
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


# Views
def home(request):
    return render(request, 'workspace/landing.html', {"year": now().year})


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
            send_verification_email(user, verification_link)
            messages.success(request, "Account created! Please check your email to verify your account.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'workspace/register.html', {'form': form})


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


class CustomLoginView(LoginView):
    template_name = 'workspace/login.html'


@login_required
def custom_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')


@login_required
def session_timeout_warning(request):
    if request.method == "GET":
        request.session.modified = True
        return JsonResponse({"message": "Session refreshed successfully."})
    return JsonResponse({"error": "Invalid request method."}, status=400)


@login_required
def dashboard(request):
    attendance_records = AttendanceRecord.objects.filter(user=request.user).order_by('-date')[:5]
    formatted_attendance = [
        {"date": record.date.strftime("%Y-%m-%d"), "status": record.get_status_display()}
        for record in attendance_records
    ]

    leave_requests = []
    if hasattr(request.user, 'profile') and request.user.profile.is_manager:
        leave_requests = LeaveRequest.objects.filter(manager=request.user, status='P').order_by('-start_date')
        formatted_leave_requests = [
            {"user": leave.user.get_full_name(), "start_date": leave.start_date.strftime("%Y-%m-%d"),
             "end_date": leave.end_date.strftime("%Y-%m-%d"), "status": leave.get_status_display()}
            for leave in leave_requests
        ]

    context = {"attendance_records": formatted_attendance, "leave_requests": formatted_leave_requests}
    return render(request, 'workspace/dashboard.html', context)
