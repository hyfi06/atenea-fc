from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import RegistroAsesor
from .permissions import EsAsesorAcademico, EsDuenoDelRegistro
from .serializers import AgregarMateriaSerializer, RegistroAsesorSerializer


class RegistroAsesorViewSet(ModelViewSet):
    serializer_class = RegistroAsesorSerializer
    permission_classes = [EsAsesorAcademico, EsDuenoDelRegistro]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return RegistroAsesor.objects.filter(asesor__user=self.request.user)
        return RegistroAsesor.objects.all()

    def perform_create(self, serializer):
        serializer.save(asesor=self.request.user.perfil_asesor_academico)

    @action(detail=True, methods=["post"], url_path="materias")
    def materias(self, request, pk=None):
        registro = self.get_object()
        serializer = AgregarMateriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        materia = serializer.validated_data["materia_id"]
        try:
            registro.agregar_materia(materia)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RegistroAsesorSerializer(registro).data, status=status.HTTP_200_OK)