import datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Asesoria, Disponibilidad, RegistroAsesor
from .permissions import (
    EsAlumno, EsAlumnoOAsesorAcademico, EsAsesorAcademico, EsDuenoDelRegistro, EsDuenoDeLaAsesoria,
)
from .serializers import (
    AgregarMateriaSerializer, AsesoriaSerializer, CancelarSerializer, DisponibilidadSerializer,
    MarcarAsistenciaSerializer, NotasSerializer, RegistroAsesorSerializer, ResultadoBusquedaSerializer,
)
from .servicios import ventana_agendable


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

class DisponibilidadViewSet(ModelViewSet):
    serializer_class = DisponibilidadSerializer
    permission_classes = [EsAsesorAcademico, EsDuenoDelRegistro]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return Disponibilidad.objects.filter(registro__asesor__user=self.request.user)
        return Disponibilidad.objects.all()

class BuscarDisponibilidadView(APIView):
    permission_classes = [EsAlumno]

    def get(self, request):
        materia_id = request.query_params.get("materia")
        carrera_id = request.query_params.get("carrera")
        formato = request.query_params.get("formato")

        disponibilidades = Disponibilidad.objects.filter(activa=True).select_related("registro")
        if materia_id:
            disponibilidades = disponibilidades.filter(registro__materias__id=materia_id)
        if carrera_id:
            disponibilidades = disponibilidades.filter(registro__materias__carrera_id=carrera_id)
        if formato:
            disponibilidades = disponibilidades.filter(formato=formato)
        disponibilidades = list(disponibilidades.distinct())

        inicio, fin = ventana_agendable()
        ocupados = set(
            Asesoria.objects.filter(fecha__range=(inicio, fin))
            .exclude(estado="cancelada")
            .values_list("disponibilidad_id", "fecha")
        )

        resultados = []
        fecha_cursor = inicio
        while fecha_cursor <= fin:
            dia_semana = fecha_cursor.weekday()
            for disp in disponibilidades:
                if disp.dia_semana != dia_semana:
                    continue
                if (disp.id, fecha_cursor) in ocupados:
                    continue
                resultados.append({
                    "disponibilidad_id": disp.id,
                    "fecha": fecha_cursor,
                    "hora_inicio": disp.hora_inicio,
                    "hora_fin": disp.hora_fin,
                    "formato": disp.formato,
                    "ubicacion": disp.ubicacion,
                    "liga_virtual": disp.liga_virtual,
                })
            fecha_cursor += datetime.timedelta(days=1)

        return Response(ResultadoBusquedaSerializer(resultados, many=True).data)


class AsesoriaViewSet(ModelViewSet):
    serializer_class = AsesoriaSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [EsAlumno()]
        if self.action == "cancelar":
            return [EsAlumnoOAsesorAcademico(), EsDuenoDeLaAsesoria()]
        if self.action in ("marcar_asistencia", "notas"):
            return [EsAsesorAcademico(), EsDuenoDeLaAsesoria()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if self.action in ("cancelar", "marcar_asistencia", "notas"):
            # get_object() resuelve desde este queryset ANTES de aplicar
            # has_object_permission. Si se filtrara aquí por dueño, un
            # objeto ajeno daría 404 y nunca llegaría a EsDuenoDeLaAsesoria
            # -> el 403 explícito que exige el ADR 0017 se perdería.
            return Asesoria.objects.all()
        if hasattr(user, "perfil_alumno"):
            return Asesoria.objects.filter(alumno=user.perfil_alumno)
        if hasattr(user, "perfil_asesor_academico"):
            return Asesoria.objects.filter(disponibilidad__registro__asesor__user=user)
        return Asesoria.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "Este horario ya fue tomado por otro alumno."},
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        asesoria = self.get_object()
        serializer = CancelarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asesoria.cancelar(usuario=request.user, motivo=serializer.validated_data["motivo"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AsesoriaSerializer(asesoria).data)

    @action(detail=True, methods=["post"], url_path="marcar_asistencia")
    def marcar_asistencia(self, request, pk=None):
        asesoria = self.get_object()
        serializer = MarcarAsistenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asesoria.marcar_asistencia(serializer.validated_data["asistio"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AsesoriaSerializer(asesoria).data)

    @action(detail=True, methods=["post"])
    def notas(self, request, pk=None):
        asesoria = self.get_object()
        serializer = NotasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asesoria.guardar_notas(serializer.validated_data["texto"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AsesoriaSerializer(asesoria).data)
