import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """
    Ensures the presence of at least one uppercase letter (A-Z).
    """
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter.")


class SpecialCharacterValidator:
    """
    Ensures the presence of at least one special character (!@#$%^&* etc.).
    """
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (e.g., @, #, $)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character (e.g., @, #, $).")


class NumberValidator:
    """
    Ensures the presence of at least one digit (0-9).
    """
    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one number."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Your password must contain at least one number.")


class NoReusePasswordValidator:
    """
    Prevents users from reusing old passwords.
    """
    def validate(self, password, user=None):
        if user and user.check_password(password):
            raise ValidationError(
                _("You cannot reuse your previous password."),
                code='password_reuse',
            )

    def get_help_text(self):
        return _("You cannot reuse your previous password.")


class MinLengthValidator:
    """
    Ensures the password meets a custom minimum length.
    """
    def __init__(self, min_length=12):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _("Your password must be at least %(min_length)d characters long.") % {'min_length': self.min_length}
