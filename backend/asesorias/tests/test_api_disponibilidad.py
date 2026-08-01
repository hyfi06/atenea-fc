import datetime

from accounts.models import PerfilAcademico, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area
from rest_framework.test import APITestCase


class DisponibilidadApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Test Area")

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        self.academico = PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

        self.otro_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        self.otro_academico = PerfilAcademico.objects.create(user=self.otro_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_user, area=self.area)
        self.registro_ajeno = RegistroAsesor.objects.create(asesor=self.otro_asesor, semestre="20271")

    def tearDown(self):
        self.registro_ajeno.delete()
        self.otro_asesor.delete()
        self.otro_academico.delete()
        self.otro_user.delete()
        self.registro.delete()
        self.asesor.delete()
        self.academico.delete()
        self.asesor_user.delete()
        self.area.delete()

    def test_asesor_crea_disponibilidad_virtual(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 201)
        Disponibilidad.objects.get(id=response.data["id"]).delete()  # Cleanup

    def test_crear_en_registro_ajeno_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro_ajeno.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 400)
        Disponibilidad.objects.filter(registro=self.registro_ajeno).delete()  # Cleanup

    def test_hora_fuera_de_rejilla_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:15:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 400)

    def test_presencial_sin_ubicacion_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "presencial",
        })
        self.assertEqual(response.status_code, 400)

    def test_bloque_duplicado_devuelve_400(self):
        disp = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "presencial", "ubicacion": "Salón 1",
        })
        self.assertEqual(response.status_code, 400)
        disp.delete()  # Cleanup

    def test_listar_solo_ve_las_propias(self):
        disp1 = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        disp2 = Disponibilidad.objects.create(
            registro=self.registro_ajeno, dia_semana=0, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/disponibilidades/")
        self.assertEqual(len(response.data), 1)
        disp1.delete()
        disp2.delete()  # Cleanup

    def test_editar_disponibilidad_ajena_devuelve_403(self):
        disp_ajena = Disponibilidad.objects.create(
            registro=self.registro_ajeno, dia_semana=0, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.patch(f"/api/asesorias/disponibilidades/{disp_ajena.id}/", {"activa": False})
        self.assertEqual(response.status_code, 403)
        disp_ajena.delete()  # Cleanup

    def test_eliminar_propia_disponibilidad(self):
        disp = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.delete(f"/api/asesorias/disponibilidades/{disp.id}/")
        self.assertEqual(response.status_code, 204)
        disp.delete()  # Cleanup

