from django.contrib import admin

from .models import PerfilAsesorAcademico


@admin.register(PerfilAsesorAcademico)
class PerfilAsesorAcademicoAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "activo")
    list_filter = ("area", "activo")
    search_fields = ("user__email",)
