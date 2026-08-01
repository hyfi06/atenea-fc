from rest_framework.routers import DefaultRouter

from .views import (
    AsesoriaViewSet, BuscarDisponibilidadView, DisponibilidadViewSet, RegistroAsesorViewSet,
)

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")
router.register("asesorias", AsesoriaViewSet, basename="asesoria")

urlpatterns = router.urls
