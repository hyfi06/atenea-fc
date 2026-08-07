from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from materias.models import Materia

from .models import Asesoria, Disponibilidad, RegistroAsesor


class RegistroAsesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroAsesor
        fields = ["id", "semestre", "materias"]
        read_only_fields = ["materias"]


class AgregarMateriaSerializer(serializers.Serializer):
    materia_id = serializers.IntegerField()

    def validate_materia_id(self, value):
        try:
            return Materia.objects.get(pk=value)
        except Materia.DoesNotExist:
            raise serializers.ValidationError("La materia no existe.")


class DisponibilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilidad
        fields = ["id", "registro", "dia_semana", "hora_inicio", "formato", "ubicacion", "liga_virtual", "activa"]

    def validate_registro(self, value):
        request = self.context["request"]
        if value.asesor.user_id != request.user.id:
            raise serializers.ValidationError("No puedes crear disponibilidad para el registro de otro asesor.")
        return value

    def validate(self, attrs):
        instance = self.instance or Disponibilidad()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return attrs

    def create(self, validated_data):
        # BooleanField trata una petición de formulario (multipart/urlencoded)
        # como un checkbox HTML: si "activa" no viene en el payload, DRF lo
        # interpreta como False en vez de usar el default=True del modelo.
        # Un bloque recién publicado siempre debe nacer activo; desactivarlo
        # es una acción posterior explícita vía PATCH, no algo que se decida
        # al crear.
        validated_data["activa"] = True
        return super().create(validated_data)


class ResultadoBusquedaSerializer(serializers.Serializer):
    disponibilidad_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()
    formato = serializers.CharField()
    ubicacion = serializers.CharField(allow_blank=True)
    liga_virtual = serializers.CharField(allow_blank=True)


class AsesoriaSerializer(serializers.ModelSerializer):
    cancelado_por_rol = serializers.SerializerMethodField()

    class Meta:
        model = Asesoria
        fields = [
            "id", "alumno", "disponibilidad", "materia", "carrera", "fecha", "hora_inicio",
            "formato", "ubicacion", "liga_virtual", "estado", "asistio", "notas",
            "motivo_cancelacion", "cancelado_por", "cancelado_por_rol", "creado_en",
        ]
        read_only_fields = [
            "id", "alumno", "carrera", "hora_inicio", "formato", "ubicacion", "liga_virtual",
            "estado", "asistio", "notas", "motivo_cancelacion", "cancelado_por", "creado_en",
        ]
        # DRF genera un UniqueTogetherValidator automático a partir del
        # UniqueConstraint condicional de Asesoria, lo que rechazaría el
        # doble-booking con 400 antes de tocar la base de datos. Se
        # desactiva a propósito: ADR 0017 decisión 8 exige que la condición
        # de carrera se resuelva en la base de datos y se traduzca a 409,
        # no que se prevenga con un chequeo optimista en la vista.
        validators = []

    def get_cancelado_por_rol(self, obj):
        """Quién canceló, en términos de la sesión — no de la identidad.

        `cancelado_por` es un id de User, y ninguna de las dos partes conoce
        el id de User de la otra (el asesor solo ve PerfilAlumno.id), así que
        el id crudo no alcanza para renderizar el panel de cancelación.
        """
        if not obj.cancelado_por_id:
            return None
        if obj.cancelado_por_id == obj.alumno.user_id:
            return "alumno"
        if obj.cancelado_por_id == obj.disponibilidad.registro.asesor.user_id:
            return "asesor"
        return "otro"

    def validate(self, attrs):
        disponibilidad = attrs["disponibilidad"]
        alumno = self.context["request"].user.perfil_alumno
        instance = Asesoria(
            alumno=alumno,
            disponibilidad=disponibilidad,
            materia=attrs["materia"],
            carrera=alumno.carrera,
            fecha=attrs["fecha"],
            hora_inicio=disponibilidad.hora_inicio,
            formato=disponibilidad.formato,
            ubicacion=disponibilidad.ubicacion,
            liga_virtual=disponibilidad.liga_virtual,
        )
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        attrs["carrera"] = alumno.carrera
        attrs["hora_inicio"] = disponibilidad.hora_inicio
        attrs["formato"] = disponibilidad.formato
        attrs["ubicacion"] = disponibilidad.ubicacion
        attrs["liga_virtual"] = disponibilidad.liga_virtual
        return attrs

    def create(self, validated_data):
        validated_data["alumno"] = self.context["request"].user.perfil_alumno
        return Asesoria.objects.create(**validated_data)


class CancelarSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=False, allow_blank=True, default="")


class MarcarAsistenciaSerializer(serializers.Serializer):
    asistio = serializers.BooleanField()


class NotasSerializer(serializers.Serializer):
    texto = serializers.CharField(allow_blank=True)
