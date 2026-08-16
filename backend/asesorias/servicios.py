import datetime

from django.utils import timezone

# Reexport: `semestre_vigente` vive en `academico` desde el ADR 0027. La copia
# que estaba aquí usaba la convención vieja (enero–junio -> semestre 1 del año
# en curso) y difería del frontend. Se conserva el nombre importable para no
# tocar los call sites de `asesorias/views.py`.
from academico.servicios import semestre_vigente  # noqa: F401


def ventana_agendable(hoy: datetime.date | None = None) -> tuple[datetime.date, datetime.date]:
    if hoy is None:
        hoy = timezone.localdate()
    lunes_de_esta_semana = hoy - datetime.timedelta(days=hoy.weekday())
    domingo_que_cierra_semana_siguiente = lunes_de_esta_semana + datetime.timedelta(days=13)
    return hoy, domingo_que_cierra_semana_siguiente