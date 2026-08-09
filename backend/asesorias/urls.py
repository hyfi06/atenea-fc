from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AsesoriaViewSet, BuscarDisponibilidadView, DisponibilidadViewSet, OfertaView, RegistroAsesorViewSet,
)

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")
router.register("asesorias", AsesoriaViewSet, basename="asesoria")

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
    path("oferta/", OfertaView.as_view(), name="oferta"),
] + router.urls
