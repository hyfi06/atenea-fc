from django.db import migrations

AREAS = ["Matemáticas", "Física", "Biología"]

# (clave, nombre, area, alias, acepta_nuevo_ingreso, siass_id, dgeci_id, siassypp_id)
CARRERAS = [
    (101, "Actuaría", "Matemáticas", ["ACTUARIA", "ACT"], True, 1, 11, 1),
    (201, "Biología", "Biología", ["BIOLOGIA", "BIO"], True, 28, 16, 39),
    (104, "Ciencias de la Computación", "Matemáticas",
     ["CIENCIAS DE LA COMPUTACION", "C. COMPUTACION", "CC"], True, 4, 12, 4),
    (127, "Ciencias de la Tierra", "Física", [
        "CIENCIAS DE LA TIERRA",
        "CIENCIAS DE LA TIERRA - CAMPUS CU",
        "CIENCIAS DE LA TIERRA - CU",
        "CIENCIAS DE LA TIERRA - JURIQUILLA",
        "CIENCIAS DE LA TIERRA - CAMPUS JURIQUILLA",
        "CIENCIAS DE LA TIERRA, CIENCIAS ACUATICAS",
        "CIENCIAS DE LA TIERRA, CIENCIAS AMBIENTALES",
        "CIENCIAS DE LA TIERRA, CIENCIAS ATMOSFERICAS",
        "CIENCIAS DE LA TIERRA, CIENCIAS ESPACIALES",
        "CIENCIAS DE LA TIERRA, CIENCIAS DE LA TIERRA SOLIDA",
        "CT",
    ], False, 27, 15, 27),
    (106, "Física", "Física", ["FISICA", "FIS"], True, 6, 13, 6),
    (134, "Física Biomédica", "Física", ["FISICA BIOMEDICA", "FB"], True, 96, 10, 34),
    (217, "Manejo Sustentable de Zonas Costeras", "Biología", [
        "MANEJO SUSTENTABLE DE ZONAS COSTERAS", "MANEJO SUSTENTABLE", "MSZC",
    ], False, 44, 17, 55),
    (122, "Matemáticas", "Matemáticas", ["MATEMATICAS", "MAT"], True, 22, 14, 22),
    (136, "Matemáticas Aplicadas", "Matemáticas",
     ["MATEMATICAS APLICADAS", "APLICADAS", "MA"], True, 119, 182, 36),
]


def sembrar(apps, schema_editor):
    Area = apps.get_model("carreras", "Area")
    Carrera = apps.get_model("carreras", "Carrera")

    areas_por_nombre = {}
    for nombre in AREAS:
        areas_por_nombre[nombre], _ = Area.objects.get_or_create(nombre=nombre)

    for clave, nombre, area_nombre, alias, nuevo_ingreso, siass_id, dgeci_id, siassypp_id in CARRERAS:
        Carrera.objects.get_or_create(
            clave=clave,
            defaults={
                "nombre": nombre,
                "area": areas_por_nombre[area_nombre],
                "alias": alias,
                "acepta_nuevo_ingreso": nuevo_ingreso,
                "siass_id": siass_id,
                "dgeci_id": dgeci_id,
                "siassypp_id": siassypp_id,
            },
        )


def despoblar(apps, schema_editor):
    Area = apps.get_model("carreras", "Area")
    Carrera = apps.get_model("carreras", "Carrera")
    Carrera.objects.filter(clave__in=[c[0] for c in CARRERAS]).delete()
    Area.objects.filter(nombre__in=AREAS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("carreras", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sembrar, despoblar),
    ]
