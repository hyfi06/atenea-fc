from django.db import IntegrityError, transaction
from django.test import TestCase

from carreras.models import Area, Carrera


class CarreraUnicidadTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")

    def test_clave_unica(self):
        Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=101, nombre="Otra", area=self.area)

    def test_nombre_unico(self):
        Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carrera.objects.create(clave=102, nombre="Actuaría", area=self.area)

    def test_ids_externos_nulos_no_chocan_entre_si(self):
        Carrera.objects.create(clave=101, nombre="Actuaría", area=self.area)
        # dos carreras sin siass_id no deben violar la unicidad (NULL != NULL en Postgres)
        Carrera.objects.create(clave=102, nombre="Biología", area=self.area)


class CarreraResolveTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Matemáticas")
        self.actuaria = Carrera.objects.create(
            clave=101, nombre="Actuaría", area=area, alias=["ACTUARIA", "ACT"]
        )

    def test_resolve_por_nombre_exacto(self):
        self.assertEqual(Carrera.objects.resolve("Actuaría"), self.actuaria)

    def test_resolve_por_alias_sin_acentos_ni_mayusculas(self):
        self.assertEqual(Carrera.objects.resolve("actuaria"), self.actuaria)

    def test_resolve_no_encontrada(self):
        with self.assertRaises(Carrera.DoesNotExist):
            Carrera.objects.resolve("Carrera Inexistente")
