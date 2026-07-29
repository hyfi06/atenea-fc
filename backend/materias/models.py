from django.db import models


class Materia(models.Model):
    clave = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    carrera = models.ForeignKey(
        "carreras.Carrera", on_delete=models.PROTECT, related_name="materias"
    )
    nivel = models.PositiveSmallIntegerField(null=True, blank=True)
    plan = models.PositiveIntegerField()
    habilitada_asesorias = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.clave} — {self.nombre}"


class OfertaMateria(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT, related_name="ofertas")
    semestre = models.CharField(max_length=5)
    se_imparte = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["materia", "semestre"], name="unique_oferta_materia_semestre"
            )
        ]

    def __str__(self):
        return f"{self.materia.clave} — {self.semestre}"
