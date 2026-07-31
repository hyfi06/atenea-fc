from rest_framework.routers import DefaultRouter

from .views import MateriaViewSet

router = DefaultRouter()
router.register("materias", MateriaViewSet, basename="materia")

urlpatterns = router.urls