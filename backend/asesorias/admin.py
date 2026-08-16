from django.contrib import admin

from .models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor 


@admin.register(PerfilAsesorAcademico)
class PerfilAsesorAcademicoAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "activo", "solicitado_por_el_usuario")
    list_filter = ("activo", "solicitado_por_el_usuario", "area")
    search_fields = ("user__email",)


@admin.register(RegistroAsesor)
class RegistroAsesorAdmin(admin.ModelAdmin):
    list_display = ("asesor", "semestre")
    list_filter = ("semestre",)
    search_fields = ("asesor__user__email",)
    filter_horizontal = ("materias",)


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ("registro", "dia_semana", "hora_inicio", "formato", "activa")
    list_filter = ("dia_semana", "formato", "activa")
    search_fields = ("registro__asesor__user__email",)

    
@admin.register(Asesoria)
class AsesoriaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "materia", "fecha", "hora_inicio", "estado", "asistio")
    list_filter = ("estado", "formato", "materia")
    search_fields = ("alumno__user__email", "alumno__numero_cuenta")