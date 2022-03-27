"""Students model."""

# Django
from django.db import models

# Models

from ateneafc.users.models import User

# Utilities
from ateneafc.utils.models import AteneaFCModel


class Student(AteneaFCModel):
    """Student model."""

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )

    student_id = models.CharField(
        'student id',
        unique=True,
        max_length=9,
    )
