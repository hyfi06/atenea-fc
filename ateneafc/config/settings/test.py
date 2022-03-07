"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env


# Base 
DEBUG = False
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="GGxgRTmyhFBmQ4sAxtd9n1zVn2PxoRf2teLUpqvROD3zY1J15oYIwi9jz09xtwgk",
)
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": ""
    }
}

# PASSWORDS
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Templates
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # NOQA
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # NOQA
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# Email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
