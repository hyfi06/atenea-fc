from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, HistoriaAcademica, PerfilAcademico, PerfilAlumno, PerfilSAE


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


class HistoriaAcademicaInline(admin.TabularInline):
    model = HistoriaAcademica
    extra = 0


@admin.register(PerfilAlumno)
class PerfilAlumnoAdmin(admin.ModelAdmin):
    list_display = ("numero_cuenta", "user")
    search_fields = ("numero_cuenta", "user__email")
    inlines = [HistoriaAcademicaInline]


@admin.register(HistoriaAcademica)
class HistoriaAcademicaAdmin(admin.ModelAdmin):
    list_display = ("perfil_alumno", "carrera", "generacion")
    list_filter = ("carrera", "generacion")
    search_fields = ("perfil_alumno__numero_cuenta", "perfil_alumno__user__email")


@admin.register(PerfilAcademico)
class PerfilAcademicoAdmin(admin.ModelAdmin):
    list_display = ("numero_trabajador", "user")
    search_fields = ("numero_trabajador", "user__email")


@admin.register(PerfilSAE)
class PerfilSAEAdmin(admin.ModelAdmin):
    list_display = ("user", "activo")
    list_filter = ("activo",)
    search_fields = ("user__email",)