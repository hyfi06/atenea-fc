import csv

from django.core.management.base import BaseCommand

from carreras.models import Carrera
from materias.models import Materia


class Command(BaseCommand):
    help = "Carga o actualiza el catálogo de materias desde un CSV (columnas: Carrera,Clave,Materia,Nivel,Plan)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        creadas = 0
        actualizadas = 0
        errores = 0

        with open(options["csv_path"], newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for numero_fila, fila in enumerate(lector, start=2):
                try:
                    carrera = Carrera.objects.resolve(fila["Carrera"])
                except Carrera.DoesNotExist as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                nivel_texto = fila["Nivel"].strip()
                _, creada = Materia.objects.update_or_create(
                    clave=fila["Clave"].strip(),
                    defaults={
                        "nombre": fila["Materia"].strip(),
                        "carrera": carrera,
                        "nivel": int(nivel_texto) if nivel_texto else None,
                        "plan": int(fila["Plan"].strip()),
                    },
                )
                if creada:
                    creadas += 1
                else:
                    actualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Materias: {creadas} creadas, {actualizadas} actualizadas, {errores} filas con error"
            )
        )
