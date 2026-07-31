import datetime

from django.test import SimpleTestCase

from asesorias.servicios import ventana_agendable


class VentanaAgendableTests(SimpleTestCase):
    def test_lunes_devuelve_hoy_y_domingo_de_la_semana_siguiente(self):
        lunes = datetime.date(2026, 8, 3)  # lunes
        inicio, fin = ventana_agendable(lunes)
        self.assertEqual(inicio, lunes)
        self.assertEqual(fin, datetime.date(2026, 8, 16))  # domingo, 13 días después

    def test_miercoles_devuelve_hoy_y_domingo_de_la_semana_siguiente(self):
        miercoles = datetime.date(2026, 8, 5)
        inicio, fin = ventana_agendable(miercoles)
        self.assertEqual(inicio, miercoles)
        self.assertEqual(fin, datetime.date(2026, 8, 16))  # mismo domingo que si fuera lunes

    def test_domingo_devuelve_hoy_y_domingo_de_la_semana_siguiente(self):
        domingo = datetime.date(2026, 8, 9)  # domingo, cierra la semana en curso
        inicio, fin = ventana_agendable(domingo)
        self.assertEqual(inicio, domingo)
        self.assertEqual(fin, datetime.date(2026, 8, 16))

    def test_sin_argumento_usa_hoy(self):
        inicio, _fin = ventana_agendable()
        from django.utils import timezone
        self.assertEqual(inicio, timezone.localdate())