from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from typing import Optional
import uuid

# Moved tenant above for definition
class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255, unique=True)  # For subdomain-based routing
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Removed the save method to avoid unintended overwrites
    def __str__(self):
        return self.name


# Using built-in user model, one-to-one relationship, foreign key is user, further roles added to
# introduce RBAC (Role-Based Access Control)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)  # Indicates if the user is a manager
    is_tenant_admin = models.BooleanField(default=False)  # Indicates if the user is a tenant admin

    def __str__(self):
        # Dynamically determine the role of the user
        if self.is_tenant_admin:
            role = "Tenant Admin"
        elif self.is_manager:
            role = "Manager"
        else:
            role = "User"
        return f"{self.user.username} - {role}"


# Tracks user attendance, including work type and tenant association
class AttendanceRecord(models.Model):
    WORK_TYPES = [
        ('WFH', 'Work from Home'),
        ('IO', 'In Office'),
        ('AL', 'Annual Leave'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    date = models.DateField()  # Attendance date
    type = models.CharField(max_length=3, choices=WORK_TYPES)  # Type of work (WFH, IO, AL)

    class Meta:
        unique_together = ('user', 'date')  # Ensures one record per user per date
        
    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} on {self.date}"  # type: ignore


# This stores leave requests for each individual user
class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('SL', 'Sick Leave'),
        ('PL', 'Personal Leave'),
        ('AL', 'Annual Leave'),
    ]

    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=2, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_leaves',
    )  # Manager overseeing the leave request

    def clean(self):
        # Validate start and end dates for leave
        if self.start_date < now().date():
            raise ValidationError("The start date cannot be in the past.")
        if self.end_date < self.start_date:
            raise ValidationError("The end date cannot be before the start date.")

    def __str__(self):
        # Display leave details for the user
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.get_status_display()}) from {self.start_date} to {self.end_date}"  # type: ignore
