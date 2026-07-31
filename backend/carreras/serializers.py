from rest_framework import serializers

from .models import Area, Carrera


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "nombre"]


class CarreraSerializer(serializers.ModelSerializer):
    area = AreaSerializer(read_only=True)

    class Meta:
        model = Carrera
        fields = ["id", "clave", "nombre", "area", "acepta_nuevo_ingreso"]