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

class ResultadoBusquedaSerializer(serializers.Serializer):
    disponibilidad_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()
    formato = serializers.CharField()
    ubicacion = serializers.CharField(allow_blank=True)
    liga_virtual = serializers.CharField(allow_blank=True)


class AsesoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asesoria
        fields = [
            "id", "alumno", "disponibilidad", "materia", "fecha", "hora_inicio",
            "formato", "ubicacion", "liga_virtual", "estado", "asistio", "notas", "creado_en",
        ]
        read_only_fields = [
            "id", "alumno", "hora_inicio", "formato", "ubicacion", "liga_virtual",
            "estado", "asistio", "notas", "creado_en",
        ]
        # DRF genera un UniqueTogetherValidator automático a partir del
        # UniqueConstraint condicional de Asesoria, lo que rechazaría el
        # doble-booking con 400 antes de tocar la base de datos. Se
        # desactiva a propósito: ADR 0017 decisión 8 exige que la condición
        # de carrera se resuelva en la base de datos y se traduzca a 409,
        # no que se prevenga con un chequeo optimista en la vista.
        validators = []

    def validate(self, attrs):
        disponibilidad = attrs["disponibilidad"]
        instance = Asesoria(
            alumno=self.context["request"].user.perfil_alumno,
            disponibilidad=disponibilidad,
            materia=attrs["materia"],
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
