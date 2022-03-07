"""Development settings."""

from .base import *  # noqa
from .base import env

# Base
DEBUG = True

# Security
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="eNdpcht7isYISdTsUofcCClPPUz4ZVaA0luCHuPcyTmdsgPGYHFl52ok30a0C0KQ",
)

ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
]

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

# Templates
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG  # noqa

# Email
EMAIL_BACKEND = env(
    'DJANGO_EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

# django-extensions
INSTALLED_APPS += ['django_extensions']  # noqa F405
