import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
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
        self.alumno = crear_alumno(
            self.alumno_user, "312345678", carrera=self.carrera, generacion=2023,
        )

        self.otro_alumno_user = User.objects.create_user(email="otro_alumno@ciencias.unam.mx", password="x")
        self.otro_alumno = crear_alumno(
            self.otro_alumno_user, "312345679", carrera=self.carrera, generacion=2023,
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
        self.assertEqual(response.data["carrera"], self.carrera.id)

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


class DobleRolListadoApiTests(AsesoriaApiTestsBase):
    """Un usuario con perfil de alumno Y de asesor ve la unión de sus sesiones:
    las que agendó como alumno y las que recibe como asesor (deuda 0011)."""

    def setUp(self):
        super().setUp()
        # Promover al asesor a también-alumno.
        self.asesor_como_alumno = PerfilAlumno.objects.create(
            user=self.asesor_user, numero_cuenta="312345680", carrera=self.carrera, generacion=2023,
        )
        # Sesión donde es ASESOR (sobre su propia disponibilidad, semestre 20271).
        self.sesion_como_asesor = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        # Disponibilidad de OTRO asesor, en otro semestre, donde él es el ALUMNO.
        self.otro_asesor_user = User.objects.create_user(email="otro_asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_asesor_user, numero_trabajador="70003")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_asesor_user, area=self.area)
        self.registro_otro = RegistroAsesor.objects.create(asesor=self.otro_asesor, semestre="20262")
        self.disponibilidad_otro = Disponibilidad.objects.create(
            registro=self.registro_otro, dia_semana=1, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/o",
        )
        self.sesion_como_alumno = Asesoria.objects.create(
            alumno=self.asesor_como_alumno, disponibilidad=self.disponibilidad_otro, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes + datetime.timedelta(days=1),
            hora_inicio=self.disponibilidad_otro.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/o",
        )

    def test_listado_devuelve_la_union_de_ambos_lados(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/")

        self.assertEqual(response.status_code, 200)
        ids = {fila["id"] for fila in response.data}
        self.assertEqual(ids, {self.sesion_como_asesor.id, self.sesion_como_alumno.id})

    def test_semestres_incluye_los_de_ambos_lados(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/semestres/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"20271", "20262"})


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


class NotasOcultasApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.registro.agregar_materia(self.materia)
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        from asesorias.models import Asesoria
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=datetime.date.today(), hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
            estado="realizada", asistio=True, notas="El alumno debe repasar límites.",
        )

    def test_alumno_no_recibe_notas_en_list(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/asesorias/")
        self.assertTrue(response.data)
        self.assertNotIn("notas", response.data[0])

    def test_alumno_no_recibe_notas_en_retrieve(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")
        self.assertNotIn("notas", response.data)

    def test_asesor_dueno_si_recibe_notas(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")
        self.assertIn("notas", response.data)
        self.assertEqual(response.data["notas"], "El alumno debe repasar límites.")

    def test_miembro_sae_si_recibe_notas(self):
        from accounts.models import PerfilSAE
        from asesorias.serializers import AsesoriaSerializer
        from rest_framework.test import APIRequestFactory

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        request = APIRequestFactory().get("/")
        request.user = sae_user

        data = AsesoriaSerializer(self.asesoria, context={"request": request}).data

        self.assertIn("notas", data)
        self.assertEqual(data["notas"], "El alumno debe repasar límites.")

    def test_usuario_sin_rol_no_recibe_notas(self):
        from asesorias.serializers import AsesoriaSerializer
        from rest_framework.test import APIRequestFactory

        externo = User.objects.create_user(email="externo@ciencias.unam.mx", password="x")
        request = APIRequestFactory().get("/")
        request.user = externo

        data = AsesoriaSerializer(self.asesoria, context={"request": request}).data

        self.assertNotIn("notas", data)


class CarreraAlAgendarApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.carrera_ajena = Carrera.objects.create(clave=901, nombre="Carrera Ajena Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.get_or_create(materia=self.materia, semestre="20271", defaults={"se_imparte": True})

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.registro.agregar_materia(self.materia)
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = crear_alumno(
            self.alumno_user, "312345678", carrera=self.carrera, generacion=2023,
        )
        self.proximo_lunes = self._proximo_dia_semana(0)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        return hoy + datetime.timedelta(days=delta or 7)

    def _payload(self, **extra):
        payload = {
            "disponibilidad": self.disponibilidad.id,
            "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        }
        payload.update(extra)
        return payload

    def test_agendar_con_carrera_propia_devuelve_201(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera=self.carrera.id)
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["carrera"], self.carrera.id)

    def test_omitir_carrera_usa_la_del_alumno(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["carrera"], self.carrera.id)

    def test_carrera_ajena_devuelve_400(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera=self.carrera_ajena.id)
        )
        self.assertEqual(response.status_code, 400)

    def test_snapshot_conserva_carrera_si_cambia_el_perfil(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 201, response.data)
        self.alumno.historial.update(carrera=self.carrera_ajena)
        from asesorias.models import Asesoria
        asesoria = Asesoria.objects.get(pk=response.data["id"])
        self.assertEqual(asesoria.carrera_id, self.carrera.id)


class AgendarConHistorialTests(APITestCase):
    """La carrera del payload se valida contra HistoriaAcademica, no contra
    un campo denormalizado del perfil (ADR 0027 decisión 2)."""

    def setUp(self):
        from accounts.models import HistoriaAcademica, PerfilAcademico, User
        from accounts.tests.factories import crear_alumno
        from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
        from carreras.models import Area, Carrera
        from materias.models import Materia, OfertaMateria
        from asesorias.servicios import semestre_vigente
        import datetime

        self.area = Area.objects.create(nombre="Area historial agendar")
        self.carrera_a = Carrera.objects.create(clave=951, nombre="Carrera HA Test", area=self.area)
        self.carrera_b = Carrera.objects.create(clave=952, nombre="Carrera HB Test", area=self.area)
        self.carrera_ajena = Carrera.objects.create(
            clave=953, nombre="Carrera HC Ajena Test", area=self.area
        )
        self.materia = Materia.objects.create(
            clave="1951", nombre="Álgebra HA", carrera=self.carrera_a, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(
            materia=self.materia, semestre=semestre_vigente(), se_imparte=True
        )

        asesor_user = User.objects.create_user(email="asesor.ha@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=asesor_user, numero_trabajador="91234")
        asesor = PerfilAsesorAcademico.objects.create(user=asesor_user, area=self.area)
        registro = RegistroAsesor.objects.create(asesor=asesor, semestre=semestre_vigente())
        registro.materias.add(self.materia)
        hoy = datetime.date.today()
        self.disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=hoy.weekday(), hora_inicio=datetime.time(9, 0),
            formato="virtual", liga_virtual="https://zoom.us/j/1",
        )
        self.fecha = hoy

        self.user = User.objects.create_user(email="alumno.ha@ciencias.unam.mx", password="x")
        self.perfil = crear_alumno(self.user, "312000055", carrera=self.carrera_a, generacion=2023)
        self.HistoriaAcademica = HistoriaAcademica
        self.client.force_authenticate(user=self.user)

    def _payload(self, carrera_id=None):
        cuerpo = {
            "disponibilidad": self.disponibilidad.id,
            "fecha": self.fecha.isoformat(),
            "materia": self.materia.id,
        }
        if carrera_id is not None:
            cuerpo["carrera"] = carrera_id
        return cuerpo

    def test_con_una_sola_carrera_el_payload_puede_omitirla(self):
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["carrera"], self.carrera_a.id)

    def test_con_dos_carreras_la_carrera_es_obligatoria(self):
        self.HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_b, generacion=2025
        )
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 400)
        self.assertIn("carrera", response.data)

    def test_con_dos_carreras_acepta_cualquiera_de_las_suyas(self):
        self.HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_b, generacion=2025
        )
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera_id=self.carrera_b.id)
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["carrera"], self.carrera_b.id)

    def test_rechaza_una_carrera_que_no_es_del_alumno(self):
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera_id=self.carrera_ajena.id)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("carrera", response.data)
