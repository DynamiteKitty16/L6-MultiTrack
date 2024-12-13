from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from .models import AttendanceRecord, LeaveRequest, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.timezone import now


# Regex validator for names (example for stricter naming)
from django.core.validators import RegexValidator
name_regex = RegexValidator(r'^[A-Z][a-zA-Z\s]*$', 'Names must start with a capital letter and can only contain letters and spaces.')

class CustomUserCreationForm(UserCreationForm):
    """
    Form for user registration with custom fields and validations.
    """
    first_name = forms.CharField(max_length=30, validators=[name_regex], required=True, help_text="Enter your first name.")
    last_name = forms.CharField(max_length=30, validators=[name_regex], required=True, help_text="Enter your last name.")
    email = forms.EmailField(required=True, help_text="Enter a valid email address.")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].help_text = (
            'Your password must be at least 8 characters long, contain at least one number, '
            'one uppercase letter, and one special character.'
        )
        self.fields['password2'].help_text = 'Enter the same password as above, for verification.'

    def clean_email(self):
        """
        Ensures that the email is unique.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use. Please use a different email address.")
        return email

    def save(self, commit=True):
        """
        Auto-generates username based on first and last name to ensure uniqueness.
        """
        user = super().save(commit=False)
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')

        base_username = f"{first_name}.{last_name}".lower()
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()
        return user


class LeaveRequestForm(forms.ModelForm):
    """
    Form for creating and validating leave requests.
    """
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        """
        Custom validation for leave request dates.
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and start_date < now().date():
            self.add_error('start_date', _("Start date cannot be in the past unless you're a manager."))
        if end_date and end_date < start_date:
            self.add_error('end_date', _("End date cannot be before the start date."))

        return cleaned_data


class AttendanceRecordForm(forms.ModelForm):
    """
    Form for creating attendance records.
    """
    class Meta:
        model = AttendanceRecord
        fields = ['date', 'type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

def clean_date(self):
    """
    Validates that the attendance record date is not in the future.
    """
    date = self.cleaned_data.get('date')
    if date > now().date():
        raise ValidationError(_("You cannot log attendance for a future date."))
    return date

