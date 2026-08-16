import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase

from academico.models import PeriodoAcademico
from academico.servicios import periodo_vigente, registro_asesores_abierto, semestre_vigente


def crear_periodo(semestre="20271", **overrides):
    valores = {
        "fecha_inicio": datetime.date(2026, 8, 10),
        "fecha_fin": datetime.date(2026, 12, 4),
        "registro_asesores_inicio": datetime.date(2026, 7, 1),
        "registro_asesores_fin": datetime.date(2026, 8, 31),
    }
    valores.update(overrides)
    return PeriodoAcademico.objects.create(semestre=semestre, **valores)


class PeriodoAcademicoTests(TestCase):
    def test_semestre_unico(self):
        crear_periodo()
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_periodo()

    def test_registro_abierto_dentro_de_la_ventana(self):
        periodo = crear_periodo()
        self.assertTrue(periodo.esta_abierto_el_registro(datetime.date(2026, 7, 15)))
        self.assertTrue(periodo.esta_abierto_el_registro(datetime.date(2026, 7, 1)))
        self.assertTrue(periodo.esta_abierto_el_registro(datetime.date(2026, 8, 31)))

    def test_registro_cerrado_fuera_de_la_ventana(self):
        periodo = crear_periodo()
        self.assertFalse(periodo.esta_abierto_el_registro(datetime.date(2026, 6, 30)))
        self.assertFalse(periodo.esta_abierto_el_registro(datetime.date(2026, 9, 1)))


class PeriodoVigenteTests(TestCase):
    def test_devuelve_el_periodo_cuya_clave_coincide_con_la_heuristica(self):
        esperado = crear_periodo(semestre=semestre_vigente())
        crear_periodo(semestre="19991")
        self.assertEqual(periodo_vigente(), esperado)

    def test_devuelve_none_si_la_sae_no_dio_de_alta_el_periodo(self):
        crear_periodo(semestre="19991")
        self.assertIsNone(periodo_vigente())

    def test_registro_abierto_es_false_sin_periodo_vigente(self):
        self.assertFalse(registro_asesores_abierto())
