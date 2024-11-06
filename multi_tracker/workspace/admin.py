from django.contrib import admin
from .models import UserProfile, AttendanceRecord, LeaveRequest

# Registering the models for django interface
admin.site.register(UserProfile)
admin.site.register(AttendanceRecord)
admin.site.register(LeaveRequest)
