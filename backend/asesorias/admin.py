from django.contrib import admin

from .models import PerfilAsesorAcademico, RegistroAsesor


@admin.register(PerfilAsesorAcademico)
class PerfilAsesorAcademicoAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "activo")
    list_filter = ("area", "activo")
    search_fields = ("user__email",)


@admin.register(RegistroAsesor)
class RegistroAsesorAdmin(admin.ModelAdmin):
    list_display = ("asesor", "semestre")
    list_filter = ("semestre",)
    search_fields = ("asesor__user__email",)
    filter_horizontal = ("materias",)