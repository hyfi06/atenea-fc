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

