from django.contrib import admin

from .models import Materia, OfertaMateria


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "carrera", "nivel", "plan", "habilitada_asesorias")
    list_filter = ("carrera", "habilitada_asesorias")
    search_fields = ("clave", "nombre")
    actions = ("habilitar_asesorias", "deshabilitar_asesorias")

    @admin.action(description="Habilitar para asesorías")
    def habilitar_asesorias(self, request, queryset):
        actualizadas = queryset.update(habilitada_asesorias=True)
        self.message_user(request, f"{actualizadas} materia(s) habilitada(s) para asesorías.")

    @admin.action(description="Deshabilitar para asesorías")
    def deshabilitar_asesorias(self, request, queryset):
        actualizadas = queryset.update(habilitada_asesorias=False)
        self.message_user(request, f"{actualizadas} materia(s) deshabilitada(s) para asesorías.")


@admin.register(OfertaMateria)
class OfertaMateriaAdmin(admin.ModelAdmin):
    list_display = ("materia", "semestre", "se_imparte")
    list_filter = ("semestre", "se_imparte")
    search_fields = ("materia__clave", "materia__nombre")
