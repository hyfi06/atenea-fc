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
