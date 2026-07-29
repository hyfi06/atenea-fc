import unicodedata

from django.contrib.postgres.fields import ArrayField
from django.db import models


def normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_acentos.strip().upper()


class Area(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


class CarreraManager(models.Manager):
    def resolve(self, texto: str) -> "Carrera":
        objetivo = normalizar(texto)
        for carrera in self.all():
            if normalizar(carrera.nombre) == objetivo:
                return carrera
            if objetivo in [normalizar(a) for a in carrera.alias]:
                return carrera
        raise Carrera.DoesNotExist(f"No se encontró la carrera '{texto}'")


class Carrera(models.Model):
    clave = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=150, unique=True)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="carreras")
    alias = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    acepta_nuevo_ingreso = models.BooleanField(default=True)
    siass_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    siassypp_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    dgeci_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    objects = CarreraManager()

    def __str__(self):
        return self.nombre
