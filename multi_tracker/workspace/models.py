from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from typing import Optional
import uuid

# Tenant model for multitenancy
class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255, unique=True)  # For subdomain-based routing
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Removed the save method to avoid unintended overwrites
    def __str__(self):
        return self.name


# Using built-in user model, one-to -one relationship, foreign key is user, further roles added to
# introduce RBAC (Role-Based Access Control)
class UserProfile(models.Model):
    # One-to-one link with the built-in User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)  # Indicates if the user is a manager
    is_tenant_admin = models.BooleanField(default=False)  # Indicates if the user is a tenant admin
    manager = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_employees'
    ) # Creating a reporting hierarchy

    def __str__(self):
        # Return a meaningful role description
        role = "Tenant Admin" if self.is_tenant_admin else "Manager" if self.is_manager else "User"
        return f"{self.user.username} - {role}"
    

# Signal to auto-create or update UserProfile whenever a User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()


# Attendance record model to track user attendance
class AttendanceRecord(models.Model):
    WORK_TYPES = [
        ('WFH', 'Work from Home'),
        ('IO', 'In Office'),
        ('AL', 'Annual Leave'),
        ('S', 'Sick'),
        ('FL', 'Flexi Leave'),
        ('NWD', 'Non Working Day'),
        ('BT', 'Business Travel'),
        ('T', 'Training'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)  # Associate attendance with a tenant
    date = models.DateField()  # Attendance date
    type = models.CharField(max_length=3, choices=WORK_TYPES, null=True, blank=True)  # Type of work

    class Meta:
        unique_together = ('user', 'date')  # Ensure one record per user per date

    def __str__(self):
        # Display user, attendance type, and date
        return f"{self.user.username} - {self.get_type_display()} on {self.date}" # type: ignore


# Leave request model with validations and workflow support
class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('SL', 'Sick Leave'),
        ('PL', 'Personal Leave'),
        ('AL', 'Annual Leave'),
        ('FL', 'Flexi Leave'),
        ('NWD', 'Non Working Day'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
        ('Cancellation Pending', 'Cancellation Pending'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=3, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    manager = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, related_name='leave_requests_to_approve'
    )  # Link to manager for approval workflow
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically store the creation timestamp

    def clean(self):
        """
        Validate leave request dates:
        - Start date cannot be in the past (except for managers).
        - End date must be after the start date.
        """
        if self.start_date < now().date():
            raise ValidationError('Start date cannot be in the past.')
        if self.end_date < self.start_date:
            raise ValidationError('End date cannot be before the start date.')

    def save(self, *args, **kwargs):
        """
        Save method ensures validation is always enforced before saving.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        # Display leave type, status, and date range
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.get_status_display()}) from {self.start_date} to {self.end_date}" # type: ignore
