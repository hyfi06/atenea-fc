import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import DataError, IntegrityError, transaction

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

        try:
            archivo = open(options["csv_path"], newline="", encoding="utf-8")
        except (FileNotFoundError, OSError) as exc:
            raise CommandError(f"No se pudo abrir el archivo '{options['csv_path']}': {exc}")

        with archivo:
            lector = csv.DictReader(archivo)
            columnas_requeridas = {"Carrera", "Clave", "Materia", "Nivel", "Plan"}
            columnas_presentes = set(lector.fieldnames or [])
            columnas_faltantes = columnas_requeridas - columnas_presentes
            if columnas_faltantes:
                raise CommandError(
                    f"Encabezado del CSV inválido: faltan las columnas {sorted(columnas_faltantes)}"
                )

            for numero_fila, fila in enumerate(lector, start=2):
                try:
                    carrera = Carrera.objects.resolve(fila["Carrera"])
                except Carrera.DoesNotExist as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                try:
                    nivel_texto = fila["Nivel"].strip()
                    with transaction.atomic():
                        _, creada = Materia.objects.update_or_create(
                            clave=fila["Clave"].strip(),
                            defaults={
                                "nombre": fila["Materia"].strip(),
                                "carrera": carrera,
                                "nivel": int(nivel_texto) if nivel_texto else None,
                                "plan": int(fila["Plan"].strip()),
                            },
                        )
                except (ValueError, KeyError, TypeError, AttributeError, DataError, IntegrityError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                if creada:
                    creadas += 1
                else:
                    actualizadas += 1

        resumen = f"Materias: {creadas} creadas, {actualizadas} actualizadas, {errores} filas con error"
        if errores:
            raise CommandError(resumen)
        self.stdout.write(self.style.SUCCESS(resumen))
