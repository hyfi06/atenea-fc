import datetime

from rest_framework.test import APITestCase

from academico.servicios import semestre_vigente
from academico.tests.test_periodo import crear_periodo
from accounts.models import User

RUTA = "/api/academico/periodo-vigente/"


class PeriodoVigenteApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="quien.sea@ciencias.unam.mx", password="x")

    def test_requiere_sesion(self):
        self.assertEqual(self.client.get(RUTA).status_code, 401)

    def test_404_si_la_sae_no_dio_de_alta_el_periodo(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get(RUTA).status_code, 404)

    def test_devuelve_el_detalle_del_periodo_vigente(self):
        crear_periodo(
            semestre=semestre_vigente(),
            registro_asesores_inicio=datetime.date(2000, 1, 1),
            registro_asesores_fin=datetime.date(2099, 12, 31),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(RUTA)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["semestre"], semestre_vigente())
        self.assertTrue(response.data["registro_asesores_abierto"])

    def test_registro_cerrado_fuera_de_la_ventana(self):
        crear_periodo(
            semestre=semestre_vigente(),
            registro_asesores_inicio=datetime.date(2000, 1, 1),
            registro_asesores_fin=datetime.date(2000, 1, 31),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(RUTA)
        self.assertFalse(response.data["registro_asesores_abierto"])
