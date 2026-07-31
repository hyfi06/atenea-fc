from rest_framework import serializers

from .models import Materia


class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ["id", "clave", "nombre", "carrera", "nivel", "plan", "habilitada_asesorias"]