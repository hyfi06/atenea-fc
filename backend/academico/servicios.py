import datetime

from django.utils import timezone


def semestre_vigente(hoy: datetime.date | None = None) -> str:
    """Clave `AAAAN` del semestre en curso según el calendario UNAM.

    Julio–diciembre pertenecen al semestre 1 del año siguiente (2026-08 ->
    "20271"); enero–junio, al semestre 2 del año en curso (2027-03 ->
    "20272"). Es la única fuente de la clave: `PeriodoAcademico` aporta las
    fechas del semestre, no decide cuál es.

    Espejo de `semestreActual` en
    `frontend/src/features/asesorias/logica.ts`.
    """
    if hoy is None:
        hoy = timezone.localdate()
    if hoy.month <= 6:
        return f"{hoy.year}2"
    return f"{hoy.year + 1}1"


def periodo_vigente(hoy: datetime.date | None = None):
    """El `PeriodoAcademico` cuya clave coincide con la heurística, o `None`.

    `None` significa "la SAE todavía no dio de alta este semestre", no "no
    hay semestre": la clave siempre existe (ver `semestre_vigente`).
    """
    from academico.models import PeriodoAcademico

    return PeriodoAcademico.objects.filter(semestre=semestre_vigente(hoy)).first()


def registro_asesores_abierto(hoy: datetime.date | None = None) -> bool:
    """Si hoy cae dentro de la ventana de registro del semestre vigente.

    Sin `PeriodoAcademico` dado de alta responde `False`: sin fechas no hay
    forma de afirmar que la ventana está abierta.
    """
    periodo = periodo_vigente(hoy)
    return periodo is not None and periodo.esta_abierto_el_registro(hoy)
