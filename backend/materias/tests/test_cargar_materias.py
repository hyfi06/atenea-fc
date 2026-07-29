import csv
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from carreras.models import Area, Carrera
from materias.models import Materia


def escribir_csv(filas):
    archivo = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    escritor = csv.DictWriter(archivo, fieldnames=["Carrera", "Clave", "Materia", "Nivel", "Plan"])
    escritor.writeheader()
    escritor.writerows(filas)
    archivo.close()
    return archivo.name


class CargarMateriasTests(TestCase):
    def test_crea_materias_nuevas(self):
        csv_path = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Administración Actuarial",
             "Nivel": "8", "Plan": "2006"},
            {"Carrera": "ACT", "Clave": "1817", "Materia": "Administración de Riesgos",
             "Nivel": "", "Plan": "2006"},
        ])

        call_command("cargar_materias", csv_path)

        self.assertEqual(Materia.objects.count(), 2)
        optativa = Materia.objects.get(clave="1817")
        self.assertIsNone(optativa.nivel)
        self.assertEqual(optativa.carrera.clave, 101)

    def test_correr_dos_veces_es_idempotente(self):
        csv_path = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Administración Actuarial",
             "Nivel": "8", "Plan": "2006"},
        ])

        call_command("cargar_materias", csv_path)
        call_command("cargar_materias", csv_path)

        self.assertEqual(Materia.objects.count(), 1)

    def test_actualiza_materia_existente(self):
        csv_path = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Nombre viejo",
             "Nivel": "8", "Plan": "2006"},
        ])
        call_command("cargar_materias", csv_path)

        csv_path_v2 = escribir_csv([
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Nombre corregido",
             "Nivel": "8", "Plan": "2006"},
        ])
        call_command("cargar_materias", csv_path_v2)

        materia = Materia.objects.get(clave="1801")
        self.assertEqual(materia.nombre, "Nombre corregido")
        self.assertEqual(Materia.objects.count(), 1)

    def test_fila_con_carrera_no_reconocida_no_crea_materia_ni_aborta(self):
        csv_path = escribir_csv([
            {"Carrera": "Carrera Inexistente", "Clave": "9999", "Materia": "No debe crearse",
             "Nivel": "1", "Plan": "2006"},
            {"Carrera": "Actuaría", "Clave": "1801", "Materia": "Administración Actuarial",
             "Nivel": "8", "Plan": "2006"},
        ])

        call_command("cargar_materias", csv_path)

        self.assertFalse(Materia.objects.filter(clave="9999").exists())
        self.assertTrue(Materia.objects.filter(clave="1801").exists())
