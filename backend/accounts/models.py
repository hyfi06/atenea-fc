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
    carrera = models.ForeignKey("carreras.Carrera", on_delete=models.PROTECT, related_name="alumnos")
    generacion = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.numero_cuenta}, {self.user.email}"


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
