from unittest.mock import patch

from rest_framework.test import APITestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico
from carreras.models import Area

RUTA = "/api/asesorias/asesores/solicitud/"


class SolicitudAsesorTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area solicitud")
        self.academico_user = User.objects.create_user(email="aca@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.academico_user, numero_trabajador="70001")
        self.externo_user = User.objects.create_user(email="ext@ciencias.unam.mx", password="x")

    def test_requiere_perfil_academico(self):
        self.client.force_authenticate(user=self.externo_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertEqual(response.status_code, 403)

    def test_el_academico_crea_su_perfil_de_asesor(self):
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertEqual(response.status_code, 201)
        perfil = PerfilAsesorAcademico.objects.get(user=self.academico_user)
        self.assertEqual(perfil.area, self.area)
        self.assertTrue(perfil.solicitado_por_el_usuario)

    @patch("asesorias.views.validar_academico_activo", return_value=False)
    def test_con_el_stub_el_perfil_nace_inactivo(self, mock_validar):
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertFalse(response.data["activo"])

    def test_se_activa_solo_si_la_validacion_externa_lo_confirma(self):
        self.client.force_authenticate(user=self.academico_user)
        with patch("asesorias.views.validar_academico_activo", return_value=True):
            response = self.client.post(RUTA, {"area": self.area.id})
        self.assertTrue(response.data["activo"])

    def test_no_se_puede_solicitar_dos_veces(self):
        PerfilAsesorAcademico.objects.create(user=self.academico_user, area=self.area)
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertEqual(response.status_code, 409)

    def test_area_inexistente_da_400(self):
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": 999999})
        self.assertEqual(response.status_code, 400)
