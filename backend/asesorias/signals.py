from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Asesoria
from .tasks import enviar_confirmacion_agenda


@receiver(post_save, sender=Asesoria)
def notificar_agenda(sender, instance, created, **kwargs):
    if created:
        enviar_confirmacion_agenda.delay(instance.id)
