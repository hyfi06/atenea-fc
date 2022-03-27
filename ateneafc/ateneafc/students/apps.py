"""Students apps."""

# Django
from django.apps import AppConfig


class StudentsAppConfig(AppConfig):
    """Students app config."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ateneafc.students'
    verbose_name = 'students'
