from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from .models import AttendanceRecord, LeaveRequest, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# Validator for names
name_regex = RegexValidator(
    r'^[A-Z][a-zA-Z\s]*$',
    'Names must start with a capital letter and can only contain letters and spaces.'
)


# Custom form for user registration
class CustomUserCreationForm(UserCreationForm):
    """
    Custom form for user registration with email as the primary identifier and validations.
    """
    first_name = forms.CharField(
        max_length=30,
        validators=[name_regex],
        required=True,
        help_text="Enter your first name."
    )
    last_name = forms.CharField(
        max_length=30,
        validators=[name_regex],
        required=True,
        help_text="Enter your last name."
    )
    email = forms.EmailField(
        required=True,
        help_text="Enter a valid email address. This will be used to log in."
    )

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
        Validates that the email is unique across all users and normalizes it to lowercase.
        """
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Please enter a valid email address.")
        email = email.lower()  # Normalize to lowercase
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use a different email address.")
        return email

    def clean(self):
        """
        Validates passwords and ensures form fields are consistent.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Password matching validation
        if password1 and password2 and password1 != password2:
            self.add_error('password1', "The passwords do not match. Please ensure both fields are identical.")

        return cleaned_data

    def save(self, commit=True):
        """
        Overridden save method to set email as the username.
        Ensures uniqueness and assigns additional fields.
        """
        user = super().save(commit=False)
        email = self.cleaned_data.get('email')

        if email:  # Ensure email is not None
            email = email.lower()  # Normalize to lowercase
            user.email = email
            user.username = email  # Use normalized email as the username
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')

        if commit:
            user.save()
        return user


# Form for leave requests
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

        # Validate start date is not in the past
        if start_date and start_date < now().date():
            self.add_error('start_date', _("Start date cannot be in the past unless you're a manager."))

        # Validate end date is not before start date
        if end_date and end_date < start_date:
            self.add_error('end_date', _("End date cannot be before the start date."))

        return cleaned_data


# Form for attendance records
class AttendanceRecordForm(forms.ModelForm):
    """
    Form for creating attendance records with custom validations.
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
        if not date:  # Ensure the field is not None
            raise ValidationError(_("The date field is required."))
        if date > now().date():  # Validate future dates
            raise ValidationError(_("You cannot log attendance for a future date."))
        return date

    def clean(self):
        """
        Additional validation for the form as a whole.
        """
        cleaned_data = super().clean()
        self.clean_date()  # Ensure clean_date is executed
        return cleaned_data
