import datetime

from academico.models import PeriodoAcademico
from academico.servicios import semestre_vigente
from accounts.models import PerfilAcademico, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area
from rest_framework.test import APITestCase


class AsesorPendienteApiTests(APITestCase):
    def setUp(self):
        self.semestre = semestre_vigente()
        PeriodoAcademico.objects.create(
            semestre=self.semestre,
            fecha_inicio=datetime.date(2000, 1, 1),
            fecha_fin=datetime.date(2099, 12, 31),
            registro_asesores_inicio=datetime.date(2000, 1, 1),
            registro_asesores_fin=datetime.date(2099, 12, 31),
        )
        self.area = Area.objects.create(nombre="Area pendiente")

        self.pendiente_user = User.objects.create_user(
            email="pendiente@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.pendiente_user, numero_trabajador="90001")
        self.pendiente = PerfilAsesorAcademico.objects.create(
            user=self.pendiente_user, area=self.area, activo=False)
        self.registro_pendiente = RegistroAsesor.objects.create(
            asesor=self.pendiente, semestre=self.semestre)

        self.aprobado_user = User.objects.create_user(
            email="aprobado@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.aprobado_user, numero_trabajador="90002")
        self.aprobado = PerfilAsesorAcademico.objects.create(
            user=self.aprobado_user, area=self.area, activo=True)

    def test_pendiente_no_puede_crear_registro(self):
        self.client.force_authenticate(user=self.pendiente_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 403)

    def test_pendiente_no_puede_listar_registros(self):
        self.client.force_authenticate(user=self.pendiente_user)
        response = self.client.get("/api/asesorias/registros/")
        self.assertEqual(response.status_code, 403)

    def test_pendiente_no_puede_crear_disponibilidad(self):
        self.client.force_authenticate(user=self.pendiente_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro_pendiente.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 403)

    def test_aprobado_sigue_creando_registro(self):
        self.client.force_authenticate(user=self.aprobado_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 201)

    def test_aprobado_sigue_creando_disponibilidad(self):
        registro = RegistroAsesor.objects.create(asesor=self.aprobado, semestre=self.semestre)
        self.client.force_authenticate(user=self.aprobado_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Disponibilidad.objects.filter(id=response.data["id"]).exists())
