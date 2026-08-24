from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Materia
from .pagination import PaginacionMaterias
from .serializers import MateriaSerializer


class MateriaViewSet(ReadOnlyModelViewSet):
    serializer_class = MateriaSerializer
    pagination_class = PaginacionMaterias
    # `?search=` de DRF: icontains sobre cada campo, unidos por OR. Se aplica
    # después de `get_queryset`, así que se combina con `carrera` y
    # `habilitada_asesorias` sin trabajo extra.
    filter_backends = [SearchFilter]
    search_fields = ["nombre", "clave"]

    def get_queryset(self):
        queryset = Materia.objects.select_related("carrera").all()
        carrera_id = self.request.query_params.get("carrera")
        if carrera_id is not None:
            queryset = queryset.filter(carrera_id=carrera_id)
        habilitada_asesorias = self.request.query_params.get("habilitada_asesorias")
        if habilitada_asesorias is not None:
            queryset = queryset.filter(
                habilitada_asesorias=habilitada_asesorias.lower() in ("1", "true")
            )
        return queryset