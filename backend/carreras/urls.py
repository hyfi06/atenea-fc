from rest_framework.routers import DefaultRouter

from .views import AreaViewSet, CarreraViewSet

router = DefaultRouter()
router.register("areas", AreaViewSet, basename="area")
router.register("carreras", CarreraViewSet, basename="carrera")

urlpatterns = router.urls
