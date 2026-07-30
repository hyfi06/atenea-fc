from django.core.exceptions import ValidationError
from django.db import models

import datetime

DIAS_SEMANA = [
    (0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"),
    (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
]
FORMATOS = [("presencial", "Presencial"), ("virtual", "Virtual")]
ESTADOS_ASESORIA = [("agendada", "Agendada"), ("cancelada", "Cancelada"), ("realizada", "Realizada")]


class PerfilAsesorAcademico(models.Model):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="perfil_asesor_academico"
    )
    area = models.ForeignKey(
        "carreras.Area", on_delete=models.PROTECT, related_name="asesores_academicos"
    )
    activo = models.BooleanField(default=True)

    def clean(self):
        if not hasattr(self.user, "perfil_academico"):
            raise ValidationError("Un asesor académico debe tener PerfilAcademico.")

    def __str__(self):
        return f"{self.user.email}, {self.area}"

class RegistroAsesor(models.Model):
    asesor = models.ForeignKey(PerfilAsesorAcademico, on_delete=models.PROTECT, related_name="registros")
    semestre = models.CharField(max_length=5)
    materias = models.ManyToManyField("materias.Materia", related_name="registros_asesor", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asesor", "semestre"], name="unique_registro_asesor_semestre"),
        ]

    def agregar_materia(self, materia):
        if not materia.habilitada_asesorias:
            raise ValidationError("La materia no está habilitada para asesorías.")
        if not materia.ofertas.filter(semestre=self.semestre, se_imparte=True).exists():
            raise ValidationError("La materia no se imparte en este semestre.")
        self.materias.add(materia)

    def __str__(self):
        return f"{self.asesor}, {self.semestre}"


class Disponibilidad(models.Model):
    registro = models.ForeignKey(RegistroAsesor, on_delete=models.CASCADE, related_name="disponibilidades")
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    formato = models.CharField(max_length=10, choices=FORMATOS)
    ubicacion = models.CharField(max_length=200, blank=True)
    liga_virtual = models.URLField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["registro", "dia_semana", "hora_inicio"], name="unique_bloque_registro"
            ),
        ]

    def clean(self):
        if self.hora_inicio.minute not in (0, 30) or self.hora_inicio.second != 0:
            raise ValidationError("hora_inicio debe caer en la rejilla de 30 minutos.")
        if self.formato == "presencial" and not self.ubicacion:
            raise ValidationError("Falta ubicación para una disponibilidad presencial.")
        if self.formato == "virtual" and not self.liga_virtual:
            raise ValidationError("Falta liga virtual para una disponibilidad virtual.")

    @property
    def hora_fin(self):
        inicio = datetime.datetime.combine(datetime.date.min, self.hora_inicio)
        return (inicio + datetime.timedelta(minutes=30)).time()

    def __str__(self):
        return f"{self.registro} — {self.get_dia_semana_display()} {self.hora_inicio}"