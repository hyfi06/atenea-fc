from django.test import TestCase

from carreras.models import Area, Carrera


class SeedAreasCarrerasTests(TestCase):
    def test_tres_areas(self):
        self.assertEqual(Area.objects.count(), 3)
        self.assertTrue(Area.objects.filter(nombre="Matemáticas").exists())
        self.assertTrue(Area.objects.filter(nombre="Física").exists())
        self.assertTrue(Area.objects.filter(nombre="Biología").exists())

    def test_nueve_carreras(self):
        self.assertEqual(Carrera.objects.count(), 9)

    def test_ciencias_de_la_tierra_sin_nuevo_ingreso(self):
        carrera = Carrera.objects.get(clave=127)
        self.assertFalse(carrera.acepta_nuevo_ingreso)
        self.assertEqual(carrera.area.nombre, "Física")

    def test_actuaria_en_area_matematicas_con_ids_externos(self):
        carrera = Carrera.objects.get(clave=101)
        self.assertEqual(carrera.area.nombre, "Matemáticas")
        self.assertEqual(carrera.siass_id, 1)
        self.assertEqual(carrera.dgeci_id, 11)
        self.assertEqual(carrera.siassypp_id, 1)
