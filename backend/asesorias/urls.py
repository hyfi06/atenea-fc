from rest_framework.routers import DefaultRouter

from .views import RegistroAsesorViewSet

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")

urlpatterns = router.urls