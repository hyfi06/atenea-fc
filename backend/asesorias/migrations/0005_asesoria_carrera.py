import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carreras', '0003_alter_area_options_alter_carrera_options'),
        ('asesorias', '0004_asesoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='asesoria',
            name='carrera',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='asesorias', to='carreras.carrera'),
        ),
    ]
