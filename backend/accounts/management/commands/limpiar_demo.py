from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.demo_data import (
    ALUMNOS_DEMO,
    ASESORES_DEMO,
    EMAIL_ACADEMICO_DEMO_LOGIN,
    EMAIL_ALUMNO_DEMO_LOGIN,
)
from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, PerfilAsesorAcademico, RegistroAsesor


class Command(BaseCommand):
    help = (
        "Revierte lo sembrado por sembrar_demo, incluido lo que la demo en vivo haya "
        "podido generar sobre las cuentas fijas (una asesoría agendada por el alumno, "
        "un alta de asesor completada por el académico), para que la siguiente demo "
        "arranque del mismo estado. Los User de las cuentas fijas nunca se borran."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        alumnos_borrados = self._borrar_alumnos_desechables()
        asesores_borrados = self._borrar_asesores_desechables()
        asesorias_revertidas = self._revertir_alumno_fijo()
        academico_revertido = self._revertir_academico_fijo()

        self.stdout.write(self.style.SUCCESS(
            f"Demo limpiada: {alumnos_borrados} alumnos y {asesores_borrados} asesores "
            f"desechables borrados; {asesorias_revertidas} asesoría(s) del alumno fijo "
            f"borradas; alta de asesor del académico fijo "
            f"{'revertida' if academico_revertido else 'sin cambios'}."
        ))

    def _borrar_alumnos_desechables(self):
        cuentas = [a["numero_cuenta"] for a in ALUMNOS_DEMO]
        perfiles = PerfilAlumno.objects.filter(numero_cuenta__in=cuentas)
        n = perfiles.count()
        # Asesoria.alumno es PROTECT: hay que vaciar las asesorías antes de
        # poder borrar los User (que en cascada se llevan PerfilAlumno e
        # HistoriaAcademica).
        Asesoria.objects.filter(alumno__in=perfiles).delete()
        User.objects.filter(perfil_alumno__in=perfiles).delete()
        return n

    def _borrar_asesores_desechables(self):
        numeros = [a["numero_trabajador"] for a in ASESORES_DEMO]
        academicos = PerfilAcademico.objects.filter(numero_trabajador__in=numeros)
        n = academicos.count()
        asesores = PerfilAsesorAcademico.objects.filter(user__perfil_academico__in=academicos)
        # Mismo orden que arriba: Asesoria.disponibilidad es PROTECT y
        # RegistroAsesor.asesor también, así que se vacían de adentro hacia
        # afuera antes de borrar los User.
        Asesoria.objects.filter(disponibilidad__registro__asesor__in=asesores).delete()
        RegistroAsesor.objects.filter(asesor__in=asesores).delete()
        User.objects.filter(perfil_academico__in=academicos).delete()
        return n

    def _revertir_alumno_fijo(self):
        """Borra solo lo que el alumno fijo haya agendado en vivo durante la
        demo; conserva su User, PerfilAlumno e HistoriaAcademica."""
        perfil = PerfilAlumno.objects.filter(user__email=EMAIL_ALUMNO_DEMO_LOGIN).first()
        if perfil is None:
            return 0
        return Asesoria.objects.filter(alumno=perfil).delete()[0]

    def _revertir_academico_fijo(self):
        """Si el académico fijo completó en vivo el alta de asesor, la
        deshace por completo; conserva su User y PerfilAcademico."""
        asesor = PerfilAsesorAcademico.objects.filter(
            user__email=EMAIL_ACADEMICO_DEMO_LOGIN
        ).first()
        if asesor is None:
            return False
        Asesoria.objects.filter(disponibilidad__registro__asesor=asesor).delete()
        RegistroAsesor.objects.filter(asesor=asesor).delete()
        asesor.delete()
        return True
