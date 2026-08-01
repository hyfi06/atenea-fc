from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from materias.models import Materia

from .models import RegistroAsesor


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