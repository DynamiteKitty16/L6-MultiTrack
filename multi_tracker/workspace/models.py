from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

# Using built in user model, one-to-one relationship, forgein key is user
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Manager' if self.is_manager else 'Employee'}"


class AttendanceRecord(models.Model):
    WORK_TYPES = [
        ('WFH', 'Work from Home'),
        ('IO', 'In Office'),
        ('AL', 'Annual Leave'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    type = models.CharField(max_length=3, choices=WORK_TYPES)

    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} on {self.date}"

    class Meta:
        unique_together = ('user', 'date')  # Ensures one record per user per date


# This stores for each individual user
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
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')

    def clean(self):
        if self.start_date < timezone.now().date():
            raise ValidationError("The start date cannot be in the past.")
        if self.end_date < self.start_date:
            raise ValidationError("The end date cannot be before the start date.")

    def __str__(self):
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.get_status_display()}) from {self.start_date} to {self.end_date}"
