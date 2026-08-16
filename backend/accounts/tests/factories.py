"""Helpers de construcción para tests.

`crear_alumno` existe para que los tests no tengan que saber que la carrera
del alumno dejó de vivir en `PerfilAlumno` y pasó a `HistoriaAcademica`
(ADR 0027 decisión 1): la firma es la misma que tenía
`PerfilAlumno.objects.create` antes del cambio.
"""

from accounts.models import HistoriaAcademica, PerfilAlumno


def crear_alumno(user, numero_cuenta, carrera=None, generacion=2023):
    perfil = PerfilAlumno.objects.create(user=user, numero_cuenta=numero_cuenta)
    if carrera is not None:
        HistoriaAcademica.objects.create(
            perfil_alumno=perfil, carrera=carrera, generacion=generacion
        )
    return perfil
