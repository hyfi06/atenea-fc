from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    apellido1 = models.CharField(_("apellido1"), max_length=150, blank=True)
    apellido2 = models.CharField(_("apellido2"), max_length=150, blank=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def nombre_completo(self):
        partes = [self.first_name, self.apellido1, self.apellido2]
        return " ".join(p for p in partes if p) or self.email

    def __str__(self):
        return self.email


class PerfilAlumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_alumno")
    numero_cuenta = models.CharField(max_length=10, unique=True)
    # Transitorios: los reemplaza HistoriaAcademica y se borran en la migración
    # 0007, una vez que ningún lector los usa (ADR 0027 decisión 1).
    carrera = models.ForeignKey(
        "carreras.Carrera", on_delete=models.PROTECT, related_name="alumnos",
        null=True, blank=True,
    )
    generacion = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero_cuenta}, {self.user.email}"


class HistoriaAcademica(models.Model):
    """Una inscripción del alumno a una carrera.

    Sin `unique_together` sobre `perfil_alumno` solo: un mismo número de
    cuenta puede cursar dos carreras a la vez o iniciar una segunda
    (ADR 0027 decisión 1). Lo que sí es único es el par: la misma carrera
    no se registra dos veces para el mismo alumno.
    """

    perfil_alumno = models.ForeignKey(
        PerfilAlumno, on_delete=models.CASCADE, related_name="historial"
    )
    carrera = models.ForeignKey(
        "carreras.Carrera", on_delete=models.PROTECT, related_name="historial_alumnos"
    )
    generacion = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["generacion", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["perfil_alumno", "carrera"], name="unique_historia_alumno_carrera"
            ),
        ]

    def __str__(self):
        return f"{self.perfil_alumno.numero_cuenta} — {self.carrera} ({self.generacion})"


class PerfilAcademico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_academico")
    numero_trabajador = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.numero_trabajador}, {self.user.email}"


class PerfilSAE(models.Model):
    """Miembro de la Secretaría de Asuntos Estudiantiles.

    Patrón PerfilX de ADR 0012: el rol se deriva de que el perfil exista
    (`hasattr(user, "perfil_sae")`). Vive en `accounts` y no en `asesorias`
    porque otros servicios de la SAE reutilizarán la misma identidad.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_sae")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"SAE — {self.user.email}"
