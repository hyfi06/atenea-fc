import datetime

from django.utils import timezone


def ventana_agendable(hoy: datetime.date | None = None) -> tuple[datetime.date, datetime.date]:
    if hoy is None:
        hoy = timezone.localdate()
    lunes_de_esta_semana = hoy - datetime.timedelta(days=hoy.weekday())
    domingo_que_cierra_semana_siguiente = lunes_de_esta_semana + datetime.timedelta(days=13)
    return hoy, domingo_que_cierra_semana_siguiente