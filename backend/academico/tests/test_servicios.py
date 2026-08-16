import datetime

from django.test import SimpleTestCase

from academico.servicios import semestre_vigente


class SemestreVigenteTests(SimpleTestCase):
    """Convención UNAM: el semestre AAAA-1 arranca en agosto del año anterior.

    Espejo exacto de `semestreActual` de
    `frontend/src/features/asesorias/logica.ts`. Si divergen, el frontend y el
    backend etiquetan el mismo registro con claves distintas.
    """

    def test_julio_a_diciembre_es_el_semestre_1_del_anio_siguiente(self):
        self.assertEqual(semestre_vigente(datetime.date(2026, 7, 1)), "20271")
        self.assertEqual(semestre_vigente(datetime.date(2026, 8, 1)), "20271")
        self.assertEqual(semestre_vigente(datetime.date(2026, 12, 31)), "20271")

    def test_enero_a_junio_es_el_semestre_2_del_anio_en_curso(self):
        self.assertEqual(semestre_vigente(datetime.date(2027, 1, 1)), "20272")
        self.assertEqual(semestre_vigente(datetime.date(2027, 3, 15)), "20272")
        self.assertEqual(semestre_vigente(datetime.date(2027, 6, 30)), "20272")

    def test_sin_argumento_usa_la_fecha_local(self):
        from django.utils import timezone

        hoy = timezone.localdate()
        esperado = f"{hoy.year}2" if hoy.month <= 6 else f"{hoy.year + 1}1"
        self.assertEqual(semestre_vigente(), esperado)
