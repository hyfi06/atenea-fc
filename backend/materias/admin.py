from django.contrib import admin

from .models import Materia, OfertaMateria


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "carrera", "nivel", "plan", "habilitada_asesorias")
    list_filter = ("carrera", "habilitada_asesorias")
    search_fields = ("clave", "nombre")


@admin.register(OfertaMateria)
class OfertaMateriaAdmin(admin.ModelAdmin):
    list_display = ("materia", "semestre", "se_imparte")
    list_filter = ("semestre", "se_imparte")
    search_fields = ("materia__clave", "materia__nombre")
