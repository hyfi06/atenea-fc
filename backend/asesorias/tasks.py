from celery import shared_task
from django.core.mail import send_mail


@shared_task
def enviar_confirmacion_agenda(asesoria_id: int):
    from asesorias.models import Asesoria

    asesoria = Asesoria.objects.select_related(
        "alumno__user", "disponibilidad__registro__asesor__user", "materia"
    ).get(id=asesoria_id)
    asesor_email = asesoria.disponibilidad.registro.asesor.user.email
    send_mail(
        subject=f"Asesoría confirmada — {asesoria.materia.nombre} — {asesoria.fecha}",
        message=(
            f"Se agendó una asesoría de {asesoria.materia.nombre} el {asesoria.fecha} "
            f"a las {asesoria.hora_inicio}."
        ),
        from_email=None,
        recipient_list=[asesoria.alumno.user.email, asesor_email],
    )


@shared_task
def enviar_notificacion_cancelacion(asesoria_id: int):
    from asesorias.models import Asesoria

    asesoria = Asesoria.objects.select_related(
        "alumno__user", "disponibilidad__registro__asesor__user", "materia"
    ).get(id=asesoria_id)
    asesor_email = asesoria.disponibilidad.registro.asesor.user.email
    send_mail(
        subject=f"Asesoría cancelada — {asesoria.materia.nombre} — {asesoria.fecha}",
        message=(
            f"Se canceló la asesoría de {asesoria.materia.nombre} del {asesoria.fecha} "
            f"a las {asesoria.hora_inicio}. Motivo: {asesoria.motivo_cancelacion or 'no especificado'}."
        ),
        from_email=None,
        recipient_list=[asesoria.alumno.user.email, asesor_email],
    )


@shared_task
def enviar_notificacion_resincronizacion(asesoria_id: int):
    """Avisa al alumno y al asesor que cambiaron los datos de contacto de una
    sesión ya agendada (deuda 0005). Fecha y hora no cambian nunca por esta
    vía, y el correo lo dice explícitamente para que nadie llegue a destiempo.
    """
    from asesorias.models import Asesoria

    asesoria = Asesoria.objects.select_related(
        "alumno__user", "disponibilidad__registro__asesor__user", "materia"
    ).get(id=asesoria_id)
    asesor_email = asesoria.disponibilidad.registro.asesor.user.email
    if asesoria.formato == "virtual":
        detalle = f"Liga de la sesión: {asesoria.liga_virtual}"
    else:
        detalle = f"Ubicación de la sesión: {asesoria.ubicacion}"
    send_mail(
        subject=(
            f"Cambio en los datos de tu asesoría — {asesoria.materia.nombre} — {asesoria.fecha}"
        ),
        message=(
            f"El asesor actualizó los datos de la asesoría de {asesoria.materia.nombre} "
            f"del {asesoria.fecha} a las {asesoria.hora_inicio}. La fecha y la hora NO cambian. "
            f"Formato: {asesoria.get_formato_display()}. {detalle}"
        ),
        from_email=None,
        recipient_list=[asesoria.alumno.user.email, asesor_email],
    )

