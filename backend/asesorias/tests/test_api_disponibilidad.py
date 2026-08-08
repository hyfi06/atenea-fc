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


class SesionesFuturasApiTests(APITestCase):
    def setUp(self):
        from accounts.models import PerfilAlumno
        from asesorias.models import Asesoria
        from carreras.models import Carrera
        from materias.models import Materia

        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.otro_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_user, area=self.area)

        self.alumno_user = User.objects.create_user(
            email="alumno@ciencias.unam.mx", password="x", first_name="Ana",
        )
        self.alumno_user.apellido1 = "López"
        self.alumno_user.save()
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.Asesoria = Asesoria

    def _crear_asesoria_futura(self, dias):
        from django.utils import timezone
        return self.Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=timezone.localdate() + datetime.timedelta(days=dias),
            hora_inicio=self.disponibilidad.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/x",
        )

    def test_devuelve_total_y_lista_minima(self):
        self._crear_asesoria_futura(7)
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        sesion = response.data["sesiones"][0]
        self.assertEqual(sesion["alumno_nombre"], "Ana López")
        self.assertEqual(sesion["materia_nombre"], "Álgebra")
        self.assertIn("fecha", sesion)
        self.assertIn("hora_inicio", sesion)

    def test_bloque_sin_sesiones_devuelve_total_cero(self):
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"total": 0, "sesiones": []})

    def test_bloque_ajeno_devuelve_403(self):
        self.client.force_authenticate(user=self.otro_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 403)

    def test_alumno_no_puede_consultar(self):
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 403)

