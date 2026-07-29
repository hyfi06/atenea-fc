from django.contrib import admin

from .models import Area, Carrera


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "area", "acepta_nuevo_ingreso")
    list_filter = ("area", "acepta_nuevo_ingreso")
    search_fields = ("clave", "nombre")
