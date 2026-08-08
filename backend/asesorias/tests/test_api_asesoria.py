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

    def test_cancelacion_expone_motivo_y_rol_de_quien_cancelo(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/",
            {"motivo": "Se empalmó con un examen."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["motivo_cancelacion"], "Se empalmó con un examen.")
        self.assertEqual(response.data["cancelado_por"], self.alumno_user.id)
        self.assertEqual(response.data["cancelado_por_rol"], "alumno")

    def test_el_asesor_ve_el_motivo_de_una_cancelacion_del_alumno(self):
        self.asesoria.cancelar(usuario=self.alumno_user, motivo="Ya no lo necesito.")

        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["motivo_cancelacion"], "Ya no lo necesito.")
        self.assertEqual(response.data["cancelado_por_rol"], "alumno")

    def test_cancelacion_del_asesor_reporta_rol_asesor(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/",
            {"motivo": "Junta académica."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cancelado_por_rol"], "asesor")

    def test_sesion_no_cancelada_reporta_campos_vacios(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.data["motivo_cancelacion"], "")
        self.assertIsNone(response.data["cancelado_por"])
        self.assertIsNone(response.data["cancelado_por_rol"])


class NombresEnAsesoriaApiTests(AsesoriaApiTestsBase):
    def setUp(self):
        super().setUp()
        self.alumno_user.first_name = "Ana"
        self.alumno_user.apellido1 = "López"
        self.alumno_user.apellido2 = "Ruiz"
        self.alumno_user.save()
        self.asesor_user.first_name = "Beto"
        self.asesor_user.apellido1 = "Martínez"
        self.asesor_user.save()
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes,
            hora_inicio=self.disponibilidad.hora_inicio, formato=self.disponibilidad.formato,
            liga_virtual=self.disponibilidad.liga_virtual,
        )

    def test_el_asesor_ve_el_nombre_del_alumno(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["alumno_nombre"], "Ana López Ruiz")
        self.assertEqual(response.data["alumno"], self.alumno.id)

    def test_el_alumno_ve_el_nombre_del_asesor(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["asesor_nombre"], "Beto Martínez")

    def test_listar_no_dispara_consultas_por_sesion(self):
        """Regresión de N+1: los nombres se resuelven con select_related."""
        for delta in (7, 14):
            Asesoria.objects.create(
                alumno=self.otro_alumno, disponibilidad=self.disponibilidad,
                materia=self.materia, carrera=self.carrera,
                fecha=self.proximo_lunes + datetime.timedelta(days=delta),
                hora_inicio=self.disponibilidad.hora_inicio,
                formato=self.disponibilidad.formato,
                liga_virtual=self.disponibilidad.liga_virtual,
            )
        self.client.force_authenticate(user=self.asesor_user)

        with self.assertNumQueries(2):
            response = self.client.get("/api/asesorias/asesorias/")

        self.assertEqual(len(response.data), 3)


class FiltroSemestreApiTests(AsesoriaApiTestsBase):
    def setUp(self):
        super().setUp()
        # Un segundo registro/disponibilidad del mismo asesor, en otro semestre.
        self.registro_viejo = RegistroAsesor.objects.create(
            asesor=self.asesor, semestre="20262",
        )
        self.disponibilidad_vieja = Disponibilidad.objects.create(
            registro=self.registro_viejo, dia_semana=0, hora_inicio=datetime.time(12, 0),
            formato="virtual", liga_virtual="https://meet.example.com/z",
        )
        self.sesion_actual = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes,
            hora_inicio=self.disponibilidad.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/x",
        )
        self.sesion_vieja = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad_vieja, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes - datetime.timedelta(days=7 * 20),
            hora_inicio=self.disponibilidad_vieja.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/z", estado="realizada", asistio=True,
        )

    def test_sin_filtro_devuelve_todas(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filtra_por_semestre(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/?semestre=20262")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.sesion_vieja.id)

    def test_semestre_desconocido_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/?semestre=19991")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_el_alumno_tambien_puede_filtrar(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/asesorias/?semestre=20271")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.sesion_actual.id)

    def test_listar_semestres_del_asesor_en_orden_descendente(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/semestres/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ["20271", "20262"])

    def test_listar_semestres_solo_incluye_los_del_usuario(self):
        otro_user = User.objects.create_user(email="otro_asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_user, numero_trabajador="99999")
        PerfilAsesorAcademico.objects.create(user=otro_user, area=self.area)
        self.client.force_authenticate(user=otro_user)

        response = self.client.get("/api/asesorias/asesorias/semestres/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
