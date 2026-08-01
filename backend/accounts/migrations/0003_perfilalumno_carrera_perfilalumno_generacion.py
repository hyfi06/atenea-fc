import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carreras', '0003_alter_area_options_alter_carrera_options'),
        ('accounts', '0002_perfilacademico_perfilalumno'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilalumno',
            name='carrera',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='alumnos', to='carreras.carrera'),
        ),
        migrations.AddField(
            model_name='perfilalumno',
            name='generacion',
            field=models.PositiveSmallIntegerField(),
        ),
    ]
