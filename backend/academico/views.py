from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import PeriodoAcademicoSerializer
from .servicios import periodo_vigente, semestre_vigente


class PeriodoVigenteView(RetrieveAPIView):
    """Detalle del periodo del semestre vigente.

    404 cuando la SAE todavía no lo dio de alta: no es un error del cliente,
    es información — el frontend usa ese 404 para no ofrecer el autoservicio
    de registro de asesor (ADR 0027 decisión 5).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PeriodoAcademicoSerializer

    def get_object(self):
        periodo = periodo_vigente()
        if periodo is None:
            raise NotFound(f"No hay periodo académico dado de alta para {semestre_vigente()}.")
        return periodo
