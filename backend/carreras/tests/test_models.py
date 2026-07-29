from django.db import IntegrityError, transaction
from django.test import TestCase

from carreras.models import Area, Carrera


class CarreraUnicidadTests(TestCase):
    def setUp(self):
        # Use seeded area instead of creating one
        self.area = Area.objects.get(nombre="Matemáticas")

    def test_clave_unica(self):
        # Use a new clave that doesn't exist in seeded data
        carrera = Carrera.objects.create(clave=999, nombre="Test Carrera 1", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=999, nombre="Otra", area=self.area)
        carrera.delete()

    def test_nombre_unico(self):
        # Use a new name that doesn't exist in seeded data
        carrera = Carrera.objects.create(clave=998, nombre="Test Carrera Única", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=997, nombre="Test Carrera Única", area=self.area)
        carrera.delete()

    def test_ids_externos_nulos_no_chocan_entre_si(self):
        # Use new claves that don't exist in seeded data
        carrera1 = Carrera.objects.create(clave=996, nombre="Test Carrera A", area=self.area)
        # dos carreras sin siass_id no deben violar la unicidad (NULL != NULL en Postgres)
        carrera2 = Carrera.objects.create(clave=995, nombre="Test Carrera B", area=self.area)
        carrera1.delete()
        carrera2.delete()


class CarreraResolveTests(TestCase):
    def setUp(self):
        # Use seeded carrera instead of creating one
        self.actuaria = Carrera.objects.get(clave=101)

    def test_resolve_por_nombre_exacto(self):
        self.assertEqual(Carrera.objects.resolve("Actuaría"), self.actuaria)

    def test_resolve_por_alias_sin_acentos_ni_mayusculas(self):
        self.assertEqual(Carrera.objects.resolve("actuaria"), self.actuaria)

    def test_resolve_no_encontrada(self):
        with self.assertRaises(Carrera.DoesNotExist):
            Carrera.objects.resolve("Carrera Inexistente")
