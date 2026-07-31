from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Area, Carrera
from .serializers import AreaSerializer, CarreraSerializer


class AreaViewSet(ReadOnlyModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class CarreraViewSet(ReadOnlyModelViewSet):
    queryset = Carrera.objects.select_related("area").all()
    serializer_class = CarreraSerializer