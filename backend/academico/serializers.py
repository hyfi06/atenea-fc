from rest_framework import serializers

from .models import PeriodoAcademico


class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    registro_asesores_abierto = serializers.SerializerMethodField()

    class Meta:
        model = PeriodoAcademico
        fields = [
            "semestre", "fecha_inicio", "fecha_fin",
            "registro_asesores_inicio", "registro_asesores_fin",
            "registro_asesores_abierto",
        ]

    def get_registro_asesores_abierto(self, obj) -> bool:
        return obj.esta_abierto_el_registro()
