"""Validtators module."""

# Django
from django.core.validators import RegexValidator

curp_regex = RegexValidator(
    regex=r'[A-Z]{4}[0-9]{6}[HMX][A-Z]{5}[A-Z0-9][0-9]',
    message="CURP must be entered in standard format of 18 characters"
)
