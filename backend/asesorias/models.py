from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

import datetime
from asesorias.servicios import ventana_agendable

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


class Asesoria(models.Model):
    alumno = models.ForeignKey("accounts.PerfilAlumno", on_delete=models.PROTECT, related_name="asesorias")
    disponibilidad = models.ForeignKey(Disponibilidad, on_delete=models.PROTECT, related_name="asesorias")
    materia = models.ForeignKey("materias.Materia", on_delete=models.PROTECT, related_name="asesorias")

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    formato = models.CharField(max_length=10, choices=FORMATOS)
    ubicacion = models.CharField(max_length=200, blank=True)
    liga_virtual = models.URLField(blank=True)

    estado = models.CharField(max_length=10, choices=ESTADOS_ASESORIA, default="agendada")
    asistio = models.BooleanField(null=True, default=None)
    notas = models.TextField(blank=True)

    cancelado_por = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    motivo_cancelacion = models.TextField(blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["disponibilidad", "fecha"],
                condition=models.Q(estado__in=["agendada", "realizada"]),
                name="unique_slot_disponibilidad_fecha_no_cancelada",
            ),
        ]

    def clean(self):
        if self.fecha.weekday() != self.disponibilidad.dia_semana:
            raise ValidationError("La fecha no coincide con el día de la disponibilidad.")
        inicio, fin = ventana_agendable()
        if not (inicio <= self.fecha <= fin):
            raise ValidationError("La fecha está fuera de la ventana agendable (semana en curso y la siguiente).")

    def marcar_asistencia(self, asistio: bool):
        inicio = timezone.make_aware(datetime.datetime.combine(self.fecha, self.hora_inicio))
        if timezone.now() < inicio:
            raise ValidationError("No se puede marcar asistencia antes de que ocurra la sesión.")
        self.asistio = asistio
        self.estado = "realizada"
        self.save()

    def guardar_notas(self, texto: str):
        if self.asistio is not True:
            raise ValidationError("No se pueden guardar notas si la sesión no ocurrió.")
        self.notas = texto
        self.save()

    def cancelar(self, usuario, motivo=""):
        if self.estado != "agendada":
            raise ValidationError("Solo se puede cancelar una sesión agendada.")
        self.estado = "cancelada"
        self.cancelado_por = usuario
        self.motivo_cancelacion = motivo
        self.save()
        from asesorias.tasks import enviar_notificacion_cancelacion
        transaction.on_commit(lambda: enviar_notificacion_cancelacion.delay(self.id))

    def __str__(self):
        return f"{self.alumno} — {self.disponibilidad.registro.asesor} — {self.fecha}"
