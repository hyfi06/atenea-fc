import csv

from django.core.management.base import BaseCommand

from materias.models import Materia, OfertaMateria

VALORES_VERDADEROS = {"1", "TRUE", "SI", "SÍ"}


class Command(BaseCommand):
    help = "Carga la oferta de materias de un semestre desde un CSV (columnas: Clave,SeImparte)"

    def add_arguments(self, parser):
        parser.add_argument("semestre")
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        semestre = options["semestre"]
        creadas = 0
        actualizadas = 0
        errores = 0

        with open(options["csv_path"], newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for numero_fila, fila in enumerate(lector, start=2):
                clave = fila["Clave"].strip()
                try:
                    materia = Materia.objects.get(clave=clave)
                except Materia.DoesNotExist:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: no existe una Materia con clave '{clave}'")
                    continue

                se_imparte = fila["SeImparte"].strip().upper() in VALORES_VERDADEROS
                _, creada = OfertaMateria.objects.update_or_create(
                    materia=materia,
                    semestre=semestre,
                    defaults={"se_imparte": se_imparte},
                )
                if creada:
                    creadas += 1
                else:
                    actualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Oferta {semestre}: {creadas} creadas, {actualizadas} actualizadas, {errores} filas con error"
            )
        )
