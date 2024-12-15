from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now


# UserProfile model without tenancy
class UserProfile(models.Model):
    """
    Represents additional user information, including roles, reporting hierarchy, and email verification status.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_manager = models.BooleanField(default=False)  # Indicates if the user is a manager
    is_tenant_admin = models.BooleanField(default=False)  # Indicates if the user is a tenant admin
    is_email_verified = models.BooleanField(default=False)  # Tracks email verification status
    manager = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_employees'
    )  # Reporting hierarchy

    def __str__(self):
        """
        Returns a meaningful string representation based on the user's role.
        """
        role = "Tenant Admin" if self.is_tenant_admin else "Manager" if self.is_manager else "User"
        return f"{self.user.username} - {role}"


# Signal to auto-create or update UserProfile whenever a User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensures a UserProfile is created or updated whenever a User object is saved.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()


# Attendance record model
class AttendanceRecord(models.Model):
    """
    Tracks user attendance and work types for specific dates.
    """
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
    date = models.DateField()  # The date of attendance
    type = models.CharField(max_length=3, choices=WORK_TYPES, null=True, blank=True)  # Type of work

    class Meta:
        unique_together = ('user', 'date')  # Ensures a user can only have one attendance record per date

    def __str__(self):
        """
        Returns a string representation of the attendance record.
        """
        return f"{self.user.username} - {self.get_type_display()} on {self.date}"  # type: ignore


# Leave request model
class LeaveRequest(models.Model):
    """
    Manages leave requests, their types, and approval workflow.
    """
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
    )  # Link to a manager for approval workflow
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically stores creation timestamp

    def clean(self):
        """
        Validates leave request dates:
        - Start date cannot be in the past.
        - End date must be after the start date.
        """
        if self.start_date < now().date():
            raise ValidationError('Start date cannot be in the past.')
        if self.end_date < self.start_date:
            raise ValidationError('End date cannot be before the start date.')

    def save(self, *args, **kwargs):
        """
        Ensures validation is enforced before saving.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a string representation of the leave request.
        """
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.get_status_display()}) from {self.start_date} to {self.end_date}"  # type: ignore
