from django.db import migrations


def copiar_carrera_al_historial(apps, schema_editor):
    PerfilAlumno = apps.get_model("accounts", "PerfilAlumno")
    HistoriaAcademica = apps.get_model("accounts", "HistoriaAcademica")
    for perfil in PerfilAlumno.objects.exclude(carrera__isnull=True).iterator():
        HistoriaAcademica.objects.get_or_create(
            perfil_alumno=perfil,
            carrera_id=perfil.carrera_id,
            defaults={"generacion": perfil.generacion or 0},
        )


def vaciar_historial(apps, schema_editor):
    # Reversa deliberadamente destructiva y acotada: la migración solo crea
    # filas a partir de la columna denormalizada, así que deshacerla es
    # borrar exactamente lo que creó. No intenta reconstruir
    # PerfilAlumno.carrera porque en 0007 esa columna ya no existe.
    HistoriaAcademica = apps.get_model("accounts", "HistoriaAcademica")
    HistoriaAcademica.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_historiaacademica")]

    operations = [
        migrations.RunPython(copiar_carrera_al_historial, vaciar_historial),
    ]
