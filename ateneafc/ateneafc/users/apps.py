"""Users apps."""

# Django
from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    """Users app config."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ateneafc.users'
    verbose_name = 'Users'
