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
        return f"Asesor <{self.user.email}>"
