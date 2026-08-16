import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PeriodoAcademico(models.Model):
    """Un semestre con sus fechas reales.

    Alta y edición manuales desde el admin de Django por la SAE cada
    semestre, mismo criterio que `PerfilSAE`/`PerfilAsesorAcademico`
    (ADR 0027 decisión 4). No modela subdivisiones internas del calendario
    (exámenes, vacaciones): deuda 0001 queda parcialmente resuelta.
    """

    semestre = models.CharField(max_length=5, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    registro_asesores_inicio = models.DateField()
    registro_asesores_fin = models.DateField()

    class Meta:
        ordering = ["-semestre"]
        verbose_name = "periodo académico"
        verbose_name_plural = "periodos académicos"

    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin del semestre es anterior a la de inicio.")
        if self.registro_asesores_fin < self.registro_asesores_inicio:
            raise ValidationError("La ventana de registro de asesores termina antes de abrir.")

    def esta_abierto_el_registro(self, hoy: datetime.date | None = None) -> bool:
        if hoy is None:
            hoy = timezone.localdate()
        return self.registro_asesores_inicio <= hoy <= self.registro_asesores_fin

    def __str__(self):
        return self.semestre
