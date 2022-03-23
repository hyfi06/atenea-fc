"""User models admin."""

# Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Models

from ateneafc.users.models import User


class CustomUserAdmin(UserAdmin):
    """User model admin."""
    list_display = (
        'username',
        'email',
        'is_verified',
        'is_staff',
        'is_student',
        'is_sae_staff',
    )
    fieldsets = UserAdmin.fieldsets + (
        ('FC', {
            'fields': (('is_student', 'is_sae_staff'),)
        }),
        ('Metadata', {
            'fields': (
                ('is_verified', ),
                ('created', 'modified',)
            )
        }),
    )

    readonly_fields = UserAdmin.readonly_fields + ('created', 'modified')


admin.site.register(User, CustomUserAdmin)
