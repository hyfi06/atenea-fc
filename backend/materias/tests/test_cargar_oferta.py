import csv
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from carreras.models import Area, Carrera
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
        area = Area.objects.create(nombre="Área de Prueba")
        carrera = Carrera.objects.create(clave=970, nombre="Carrera de Prueba", area=area)
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

        with self.assertRaises(CommandError):
            call_command("cargar_oferta", "20271", csv_path)

        self.assertEqual(OfertaMateria.objects.filter(materia=self.materia).count(), 1)

    def test_semestre_invalido_lanza_command_error(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "1"}])

        for semestre_invalido in ("2027", "20273", "abcde"):
            with self.assertRaises(CommandError):
                call_command("cargar_oferta", semestre_invalido, csv_path)

        self.assertFalse(OfertaMateria.objects.filter(materia=self.materia).exists())

    def test_valor_se_imparte_no_reconocido_no_crea_oferta(self):
        csv_path = escribir_csv([{"Clave": "1801", "SeImparte": "tal-vez"}])

        with self.assertRaises(CommandError):
            call_command("cargar_oferta", "20271", csv_path)

        self.assertFalse(
            OfertaMateria.objects.filter(materia=self.materia, semestre="20271").exists()
        )

    def test_archivo_inexistente_lanza_command_error(self):
        with self.assertRaises(CommandError):
            call_command("cargar_oferta", "20271", "/ruta/que/no/existe.csv")
