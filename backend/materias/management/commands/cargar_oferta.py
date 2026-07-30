import csv
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import DataError, IntegrityError, transaction

from carreras.models import normalizar
from materias.models import Materia, OfertaMateria

VALORES_VERDADEROS = {"1", "TRUE", "SI"}
VALORES_FALSOS = {"0", "FALSE", "NO"}


class Command(BaseCommand):
    help = "Carga la oferta de materias de un semestre desde un CSV (columnas: Clave,SeImparte)"

    def add_arguments(self, parser):
        parser.add_argument("semestre")
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        semestre = options["semestre"]
        if not re.fullmatch(r"\d{4}[12]", semestre):
            raise CommandError(
                f"Semestre inválido '{semestre}': se espera formato AAAAN, ej. 20271"
            )

        creadas = 0
        actualizadas = 0
        errores = 0

        try:
            archivo = open(options["csv_path"], newline="", encoding="utf-8")
        except (FileNotFoundError, OSError) as exc:
            raise CommandError(f"No se pudo abrir el archivo '{options['csv_path']}': {exc}")

        with archivo:
            lector = csv.DictReader(archivo)
            columnas_requeridas = {"Clave", "SeImparte"}
            columnas_presentes = set(lector.fieldnames or [])
            columnas_faltantes = columnas_requeridas - columnas_presentes
            if columnas_faltantes:
                raise CommandError(
                    f"Encabezado del CSV inválido: faltan las columnas {sorted(columnas_faltantes)}"
                )

            for numero_fila, fila in enumerate(lector, start=2):
                try:
                    clave = fila["Clave"].strip()
                    materia = Materia.objects.get(clave=clave)
                except Materia.DoesNotExist:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: no existe una Materia con clave '{clave}'")
                    continue
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                try:
                    valor_normalizado = normalizar(fila["SeImparte"])
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                if valor_normalizado in VALORES_VERDADEROS:
                    se_imparte = True
                elif valor_normalizado in VALORES_FALSOS:
                    se_imparte = False
                else:
                    errores += 1
                    self.stderr.write(
                        f"Fila {numero_fila}: valor de SeImparte no reconocido '{fila['SeImparte']}'"
                    )
                    continue

                try:
                    with transaction.atomic():
                        _, creada = OfertaMateria.objects.update_or_create(
                            materia=materia,
                            semestre=semestre,
                            defaults={"se_imparte": se_imparte},
                        )
                except (ValueError, KeyError, TypeError, AttributeError, DataError, IntegrityError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                if creada:
                    creadas += 1
                else:
                    actualizadas += 1

        resumen = (
            f"Oferta {semestre}: {creadas} creadas, {actualizadas} actualizadas, {errores} filas con error"
        )
        if errores:
            raise CommandError(resumen)
        self.stdout.write(self.style.SUCCESS(resumen))
