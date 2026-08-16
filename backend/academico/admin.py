from django.contrib import admin

from .models import PeriodoAcademico


@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = (
        "semestre", "fecha_inicio", "fecha_fin",
        "registro_asesores_inicio", "registro_asesores_fin",
    )
    ordering = ("-semestre",)
