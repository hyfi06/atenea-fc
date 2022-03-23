"""User model."""

# Django
from django.db import models
from django.contrib.auth.models import AbstractUser


# Utilities
from ateneafc.utils.models import AteneaFCModel
from ateneafc.utils.validators import curp_regex


class User(AteneaFCModel, AbstractUser):
    """User model.

    Extend from AteneaFCModel and Django's Abstract User, add some extra fields
    """

    curp = models.CharField(
        'CURP',
        max_length=18,
        validators=[curp_regex],
        blank=True,
    )

    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': 'A user with that email already exists.'
        }
    )

    is_verified = models.BooleanField(
        'verified',
        default=False,
        help_text='Set to true when the user have verified its email address'
    )

    def __str__(self):
        return self.username
