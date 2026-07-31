from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Materia
from .serializers import MateriaSerializer


class MateriaViewSet(ReadOnlyModelViewSet):
    serializer_class = MateriaSerializer

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