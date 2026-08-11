import datetime

from django.utils import timezone


def ventana_agendable(hoy: datetime.date | None = None) -> tuple[datetime.date, datetime.date]:
    if hoy is None:
        hoy = timezone.localdate()
    lunes_de_esta_semana = hoy - datetime.timedelta(days=hoy.weekday())
    domingo_que_cierra_semana_siguiente = lunes_de_esta_semana + datetime.timedelta(days=13)
    return hoy, domingo_que_cierra_semana_siguiente


def semestre_vigente(hoy: datetime.date | None = None) -> str:
    """Clave del semestre en curso, formato `YYYYN` (el de RegistroAsesor).

    Espejo de `semestreActual` del frontend: enero–junio -> 1, julio–diciembre
    -> 2. Es una convención de calendario, no un modelo (deuda 0001).
    """
    if hoy is None:
        hoy = timezone.localdate()
    numero = "1" if hoy.month <= 6 else "2"
    return f"{hoy.year}{numero}"