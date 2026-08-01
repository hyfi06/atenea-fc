from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, PerfilAcademico, PerfilAlumno


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "apellido1",
        "apellido2",
        "is_staff",
        "is_active",
        "google_conectado",
    )
    search_fields = ("email", "first_name", "apellido1", "apellido2")

    @admin.display(description=_("Google conectado"), boolean=True)
    def google_conectado(self, obj):
        return obj.socialaccount_set.exists()
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {
         "fields": ("first_name", "apellido1", "apellido2")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(PerfilAlumno)
class PerfilAlumnoAdmin(admin.ModelAdmin):
    list_display = ("numero_cuenta", "user")
    search_fields = ("numero_cuenta", "user__email")


@admin.register(PerfilAcademico)
class PerfilAcademicoAdmin(admin.ModelAdmin):
    list_display = ("numero_trabajador", "user")
    search_fields = ("numero_trabajador", "user__email")