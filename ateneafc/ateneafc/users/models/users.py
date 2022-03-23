"""User model."""

# Django
from django.db import models
from django.contrib.auth.models import AbstractUser

# Utilities
from ateneafc.utils.models import AteneaFCModel


class User(AteneaFCModel, AbstractUser):
    """User model.

    Extend from AteneaFCModel and Django's Abstract User, add some extra fields
    """

    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.',
        }
    )

    is_verified = models.BooleanField(
        'verified',
        default=False,
        help_text='Set to true when the user have verified its email address'
    )

    is_student = models.BooleanField(
        'student',
        default=False,
        help_text='Set to true when the user is a student',
    )

    is_sae_staff = models.BooleanField(
        'sae staff',
        default=False,
        help_text='Set to true when the user is a sae staff'
    )

    def __str__(self):
        return self.username

    def get_full_name_by_last_name(self):
        """
        Return the last_name plus the first_name, with a space in between.
        """
        full_name = "%s %s" % (self.last_name, self.first_name)
        return full_name.strip()
