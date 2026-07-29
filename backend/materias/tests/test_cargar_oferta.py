import csv
import tempfile

from django.core.management import call_command
from django.test import TestCase

from carreras.models import Carrera
from materias.models import Materia, OfertaMateria


def escribir_csv(filas):
    archivo = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    escritor = csv.DictWriter(archivo, fieldnames=["Clave", "SeImparte"])
    escritor.writeheader()
    escritor.writerows(filas)
    archivo.close()
    return archivo.name


class CargarOfertaTests(TestCase):
    def setUp(self):
        carrera = Carrera.objects.get(clave=101)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Administración Actuarial", carrera=carrera,
            nivel=8, plan=2006,
        )

    def test_crea_oferta_nueva(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])

        call_command("cargar_oferta", "20271", csv_path)

        oferta = OfertaMateria.objects.get(materia=self.materia, semestre="20271")
        self.assertTrue(oferta.se_imparte)

    def test_correr_dos_veces_es_idempotente(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])

        call_command("cargar_oferta", "20271", csv_path)
        call_command("cargar_oferta", "20271", csv_path)

        self.assertEqual(
            OfertaMateria.objects.filter(materia=self.materia, semestre="20271").count(), 1
        )

    def test_actualiza_se_imparte_del_mismo_semestre(self):
        csv_path_v1 = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])
        call_command("cargar_oferta", "20271", csv_path_v1)

        csv_path_v2 = escribir_csv([{"Clave": "1801", "SeImparte": "0"}])
        call_command("cargar_oferta", "20271", csv_path_v2)

        oferta = OfertaMateria.objects.get(materia=self.materia, semestre="20271")
        self.assertFalse(oferta.se_imparte)

    def test_semestres_distintos_no_se_pisan(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])
        call_command("cargar_oferta", "20271", csv_path)
        call_command("cargar_oferta", "20272", csv_path)

        self.assertEqual(OfertaMateria.objects.filter(materia=self.materia).count(), 2)

    def test_fila_con_clave_no_reconocida_no_crea_oferta_ni_aborta(self):
        csv_path = escribir_csv([
            {"Clave": "9999", "SeImparte": "1"},
            {"Clave": "1801", "SeImparte": "1"},
        ])

        call_command("cargar_oferta", "20271", csv_path)

        self.assertEqual(OfertaMateria.objects.filter(materia=self.materia).count(), 1)
