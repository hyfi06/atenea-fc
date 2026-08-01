from rest_framework.routers import DefaultRouter

from .views import DisponibilidadViewSet, RegistroAsesorViewSet

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")

urlpatterns = router.urls
