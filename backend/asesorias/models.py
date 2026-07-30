from django.core.exceptions import ValidationError
from django.db import models

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