import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class AsesoriaApiTestsBase(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        self.otro_alumno_user = User.objects.create_user(email="otro_alumno@ciencias.unam.mx", password="x")
        self.otro_alumno = PerfilAlumno.objects.create(
            user=self.otro_alumno_user, numero_cuenta="312345679", carrera=self.carrera, generacion=2023,
        )

        self.proximo_lunes = self._proximo_dia_semana(0)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        delta = delta or 7
        return hoy + datetime.timedelta(days=delta)


class AgendarAsesoriaApiTests(AsesoriaApiTestsBase):
    def test_alumno_agenda_exitosamente(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["formato"], "virtual")
        self.assertEqual(response.data["estado"], "agendada")
        self.assertEqual(response.data["carrera"], self.alumno.carrera_id)

    def test_asesor_no_puede_agendar(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 403)

    def test_fecha_que_no_coincide_con_dia_semana_devuelve_400(self):
        martes = self.proximo_lunes + datetime.timedelta(days=1)
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(martes),
        })
        self.assertEqual(response.status_code, 400)

    def test_doble_booking_devuelve_409(self):
        Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 409)


class ListarAsesoriaApiTests(AsesoriaApiTestsBase):
    def test_alumno_solo_ve_sus_propias_sesiones(self):
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes + datetime.timedelta(days=7),
            hora_inicio=self.disponibilidad.hora_inicio, formato=self.disponibilidad.formato,
            liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/asesorias/")
        self.assertEqual(len(response.data), 1)

    def test_asesor_ve_las_sesiones_de_sus_disponibilidades(self):
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/")
        self.assertEqual(len(response.data), 1)


class CicloDeVidaAsesoriaApiTests(AsesoriaApiTestsBase):
    def setUp(self):
        super().setUp()
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )

    def test_asesor_marca_asistencia_y_guarda_notas(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/marcar_asistencia/", {"asistio": True}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "realizada")

        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/notas/", {"texto": "Repasamos series de Taylor."}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["notas"], "Repasamos series de Taylor.")

    def test_alumno_no_puede_marcar_asistencia(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/marcar_asistencia/", {"asistio": True}
        )
        self.assertEqual(response.status_code, 403)

    def test_asesor_no_dueño_no_puede_marcar_asistencia(self):
        otro_user = User.objects.create_user(email="otro_asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_user, numero_trabajador="99999")
        PerfilAsesorAcademico.objects.create(user=otro_user, area=self.area)
        self.client.force_authenticate(user=otro_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/marcar_asistencia/", {"asistio": True}
        )
        self.assertEqual(response.status_code, 403)

    def test_guardar_notas_sin_asistencia_confirmada_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/notas/", {"texto": "texto"}
        )
        self.assertEqual(response.status_code, 400)

    def test_alumno_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)

    def test_alumno_ajeno_no_puede_cancelar(self):
        self.client.force_authenticate(user=self.otro_alumno_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 403)

    def test_asesor_dueño_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)

    def test_asesor_no_dueño_no_puede_cancelar(self):
        otro_user = User.objects.create_user(email="otro_asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_user, numero_trabajador="99999")
        PerfilAsesorAcademico.objects.create(user=otro_user, area=self.area)
        self.client.force_authenticate(user=otro_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 403)
