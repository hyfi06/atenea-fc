from django.db import IntegrityError, transaction
from django.test import TestCase

from carreras.models import Area, Carrera


class CarreraUnicidadTests(TestCase):
    def setUp(self):
        # Area de prueba propia, independiente de las áreas sembradas
        self.area = Area.objects.create(nombre="Área de Prueba")

    def test_clave_unica(self):
        Carrera.objects.create(clave=999, nombre="Test Carrera 1", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=999, nombre="Otra", area=self.area)

    def test_nombre_unico(self):
        Carrera.objects.create(clave=998, nombre="Test Carrera Única", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=997, nombre="Test Carrera Única", area=self.area)

    def test_ids_externos_nulos_no_chocan_entre_si(self):
        # dos carreras sin siass_id no deben violar la unicidad (NULL != NULL en Postgres)
        Carrera.objects.create(clave=996, nombre="Test Carrera A", area=self.area)
        Carrera.objects.create(clave=995, nombre="Test Carrera B", area=self.area)


class CarreraResolveTests(TestCase):
    def setUp(self):
        # Create self-contained test carrera (not dependent on seeded data)
        # Use test-only clave to avoid coupling with seed migration
        area = Area.objects.create(nombre="Test Area")
        self.actuaria = Carrera.objects.create(
            clave=990, nombre="Test Carrera", area=area, alias=["TEST_CARRERA", "TC", "CARRERA_PRUEBÁ"]
        )

    def tearDown(self):
        # Clean up test-created carrera and area
        # Delete carrera first, then area (protected foreign key)
        area = self.actuaria.area
        self.actuaria.delete()
        area.delete()

    def test_resolve_por_nombre_exacto(self):
        self.assertEqual(Carrera.objects.resolve("Test Carrera"), self.actuaria)

    def test_resolve_por_alias_sin_acentos_ni_mayusculas(self):
        self.assertEqual(Carrera.objects.resolve("carrera_prueba"), self.actuaria)

    def test_resolve_no_encontrada(self):
        with self.assertRaises(Carrera.DoesNotExist):
            Carrera.objects.resolve("Carrera Inexistente")
