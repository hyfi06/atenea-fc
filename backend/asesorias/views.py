import datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from materias.models import Materia

from .models import Asesoria, Disponibilidad, RegistroAsesor
from .permissions import (
    EsAlumno, EsAlumnoOAsesorAcademico, EsAsesorAcademico, EsDuenoDelRegistro, EsDuenoDeLaAsesoria,
)
from .serializers import (
    MateriaDelRegistroSerializer, AsesoriaSerializer, CancelarSerializer, DesactivarDisponibilidadSerializer,
    DisponibilidadSerializer, MarcarAsistenciaSerializer, NotasSerializer, RegistroAsesorSerializer,
    ResultadoBusquedaSerializer, SesionFuturaSerializer,
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
        serializer = MateriaDelRegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        materia = serializer.validated_data["materia_id"]
        try:
            registro.agregar_materia(materia)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RegistroAsesorSerializer(registro).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="materias/quitar")
    def quitar_materia(self, request, pk=None):
        registro = self.get_object()
        serializer = MateriaDelRegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        materia = serializer.validated_data["materia_id"]
        try:
            registro.quitar_materia(materia)
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

    @action(detail=True, methods=["get"], url_path="sesiones-futuras")
    def sesiones_futuras(self, request, pk=None):
        disponibilidad = self.get_object()
        sesiones = list(disponibilidad.sesiones_futuras())
        return Response({
            "total": len(sesiones),
            "sesiones": SesionFuturaSerializer(sesiones, many=True).data,
        })

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        disponibilidad = self.get_object()
        serializer = DesactivarDisponibilidadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        canceladas = disponibilidad.desactivar(
            usuario=request.user,
            cancelar_sesiones=serializer.validated_data["cancelar_sesiones"],
            motivo=serializer.validated_data["motivo"],
        )
        return Response({
            "disponibilidad": DisponibilidadSerializer(disponibilidad).data,
            "sesiones_canceladas": canceladas,
        })

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


class OfertaView(APIView):
    permission_classes = [EsAlumno]

    def get(self, request):
        carrera_id = request.query_params.get("carrera")
        buscar = request.query_params.get("buscar")

        materias = (
            Materia.objects.filter(registros_asesor__disponibilidades__activa=True)
            .annotate(num_asesores=Count("registros_asesor__asesor", distinct=True))
            .distinct()
        )
        if carrera_id:
            materias = materias.filter(carrera_id=carrera_id)
        if buscar:
            materias = materias.filter(nombre__icontains=buscar)

        data = [
            {
                "materia_id": m.id,
                "nombre": m.nombre,
                "carrera_id": m.carrera_id,
                "num_asesores": m.num_asesores,
            }
            for m in materias
        ]
        return Response(data)


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
        # alumno_nombre/asesor_nombre del serializer recorren dos cadenas de
        # FK; sin esto cada sesión del listado dispara consultas extra.
        base = Asesoria.objects.select_related(
            "alumno__user", "disponibilidad__registro__asesor__user", "materia"
        )
        if self.action in ("cancelar", "marcar_asistencia", "notas"):
            # get_object() resuelve desde este queryset ANTES de aplicar
            # has_object_permission. Si se filtrara aquí por dueño, un
            # objeto ajeno daría 404 y nunca llegaría a EsDuenoDeLaAsesoria
            # -> el 403 explícito que exige el ADR 0017 se perdería.
            return base

        # Unión de ambos lados: un usuario con doble rol (alumno y asesor) ve
        # tanto las sesiones que agendó como alumno como las que recibe como
        # asesor. Con mono-rol, solo una rama aporta condiciones (deuda 0011).
        condiciones = Q()
        if hasattr(user, "perfil_alumno"):
            condiciones |= Q(alumno=user.perfil_alumno)
        if hasattr(user, "perfil_asesor_academico"):
            condiciones |= Q(disponibilidad__registro__asesor__user=user)
        if not condiciones:
            return Asesoria.objects.none()
        queryset = base.filter(condiciones)

        # Filtro de historial por semestre. Comparación manual, igual que
        # materias/views.py — el proyecto no usa django-filter. Permisivo a
        # propósito: un semestre desconocido devuelve [], no 400, porque no
        # existe un modelo de calendario académico que defina qué claves son
        # válidas (deuda técnica 0001).
        if self.action == "list":
            semestre = self.request.query_params.get("semestre")
            if semestre:
                queryset = queryset.filter(disponibilidad__registro__semestre=semestre)
        return queryset

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

    @action(detail=False, methods=["get"])
    def semestres(self, request):
        """Claves de semestre en las que el usuario tiene sesiones, de la más
        reciente a la más antigua.

        Sostiene los subtabs del historial: sin esto el frontend tendría que
        cargar el historial completo para saber qué pestañas dibujar, que es
        justo lo que el filtro `?semestre=` busca evitar.
        """
        claves = self.get_queryset().values_list(
            "disponibilidad__registro__semestre", flat=True
        )
        return Response(sorted(set(claves), reverse=True))
