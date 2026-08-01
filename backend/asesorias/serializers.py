from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from materias.models import Materia

from .models import Disponibilidad, RegistroAsesor


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

