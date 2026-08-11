import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, PerfilSAE, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia
from rest_framework.test import APITestCase


class AdminAsesoriasApiTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        # Asesor A — registro en el semestre "20262".
        self.asesor_a_user = User.objects.create_user(
            email="asesor-a@ciencias.unam.mx", password="x", first_name="Ana",
        )
        self.asesor_a_user.apellido1 = "López"
        self.asesor_a_user.save()
        PerfilAcademico.objects.create(user=self.asesor_a_user, numero_trabajador="10001")
        self.asesor_a = PerfilAsesorAcademico.objects.create(user=self.asesor_a_user, area=self.area)
        self.registro_a = RegistroAsesor.objects.create(asesor=self.asesor_a, semestre="20262")
        self.registro_a.materias.add(self.materia)
        self.disp_a = Disponibilidad.objects.create(
            registro=self.registro_a, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 4",
        )

        # Asesor B — registro en el semestre "20261".
        self.asesor_b_user = User.objects.create_user(
            email="asesor-b@ciencias.unam.mx", password="x", first_name="Beto",
        )
        PerfilAcademico.objects.create(user=self.asesor_b_user, numero_trabajador="10002")
        self.asesor_b = PerfilAsesorAcademico.objects.create(user=self.asesor_b_user, area=self.area)
        self.registro_b = RegistroAsesor.objects.create(asesor=self.asesor_b, semestre="20261")
        self.registro_b.materias.add(self.materia)
        self.disp_b = Disponibilidad.objects.create(
            registro=self.registro_b, dia_semana=1, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/b",
        )

        self.alumno1_user = User.objects.create_user(
            email="alumno1@ciencias.unam.mx", password="x", first_name="Juan",
        )
        self.alumno1 = PerfilAlumno.objects.create(
            user=self.alumno1_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.alumno2_user = User.objects.create_user(
            email="alumno2@ciencias.unam.mx", password="x", first_name="Rosa",
        )
        self.alumno2 = PerfilAlumno.objects.create(
            user=self.alumno2_user, numero_cuenta="312345679", carrera=self.carrera, generacion=2024,
        )

        # Futura agendada: asesor A / alumno 1.
        self.futura_a = Asesoria.objects.create(
            alumno=self.alumno1, disponibilidad=self.disp_a, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy + datetime.timedelta(days=3),
            hora_inicio=datetime.time(10, 0), formato="presencial", ubicacion="Salón 4",
            estado="agendada",
        )
        # Futura agendada: asesor B / alumno 2.
        self.futura_b = Asesoria.objects.create(
            alumno=self.alumno2, disponibilidad=self.disp_b, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy + datetime.timedelta(days=5),
            hora_inicio=datetime.time(11, 0), formato="virtual",
            liga_virtual="https://meet.example.com/b", estado="agendada",
        )
        # Pasada realizada con notas: asesor B / alumno 2 (semestre "20261").
        self.pasada_b = Asesoria.objects.create(
            alumno=self.alumno2, disponibilidad=self.disp_b, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy - datetime.timedelta(days=30),
            hora_inicio=datetime.time(11, 0), formato="virtual",
            liga_virtual="https://meet.example.com/b",
            estado="realizada", asistio=True, notas="Repasar límites.",
        )
        # Futura cancelada: asesor A / alumno 2.
        self.cancelada_a = Asesoria.objects.create(
            alumno=self.alumno2, disponibilidad=self.disp_a, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy + datetime.timedelta(days=10),
            hora_inicio=datetime.time(10, 0), formato="presencial", ubicacion="Salón 4",
            estado="cancelada",
        )

        self.sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_por_defecto_lista_proximas_agendadas_de_todos(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 200)
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_a.id, self.futura_b.id})

    def test_orden_ascendente_por_fecha(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        fechas = [a["fecha"] for a in response.data]
        self.assertEqual(fechas, sorted(fechas))

    def test_incluye_ambos_nombres(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        fila = next(a for a in response.data if a["id"] == self.futura_a.id)
        self.assertEqual(fila["alumno_nombre"], self.alumno1_user.nombre_completo)
        self.assertEqual(fila["asesor_nombre"], self.asesor_a_user.nombre_completo)

    def test_incluye_notas(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?semestre=20261")
        fila = next(a for a in response.data if a["id"] == self.pasada_b.id)
        self.assertEqual(fila["notas"], "Repasar límites.")

    def test_filtra_por_asesor(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesorias/?asesor={self.asesor_a.id}")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_a.id})

    def test_filtra_por_alumno(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesorias/?alumno={self.alumno2.id}")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_b.id})

    def test_filtra_por_semestre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?semestre=20261")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_b.id, self.pasada_b.id})

    def test_filtra_por_estado(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?estado=cancelada")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.cancelada_a.id})

    def test_semestre_inexistente_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?semestre=19991")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_filtro_no_numerico_se_ignora(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?asesor=abc&alumno=xyz")
        self.assertEqual(response.status_code, 200)
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_a.id, self.futura_b.id})

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.alumno1_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 403)

    def test_asesor_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_a_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 403)

    def test_sin_autenticar_recibe_401(self):
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 401)


class AdminSemestresApiTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1811", nombre="Geometría", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        self.alumno_user = User.objects.create_user(email="alumno-sem@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="313111111", carrera=self.carrera, generacion=2023,
        )

        # Dos asesores distintos, cada uno con su registro en un semestre
        # distinto: ninguno es el usuario que consulta.
        self.disponibilidades = {}
        for indice, (correo, trabajador, semestre, dia) in enumerate(
            [
                ("asesor-sem-a@ciencias.unam.mx", "20001", "20261", 0),
                ("asesor-sem-b@ciencias.unam.mx", "20002", "20262", 1),
            ]
        ):
            user = User.objects.create_user(email=correo, password="x")
            PerfilAcademico.objects.create(user=user, numero_trabajador=trabajador)
            asesor = PerfilAsesorAcademico.objects.create(user=user, area=self.area)
            registro = RegistroAsesor.objects.create(asesor=asesor, semestre=semestre)
            registro.materias.add(self.materia)
            disponibilidad = Disponibilidad.objects.create(
                registro=registro, dia_semana=dia, hora_inicio=datetime.time(9 + indice, 0),
                formato="virtual", liga_virtual=f"https://meet.example.com/{indice}",
            )
            self.disponibilidades[semestre] = disponibilidad
            Asesoria.objects.create(
                alumno=self.alumno, disponibilidad=disponibilidad, materia=self.materia,
                carrera=self.carrera, fecha=self.hoy - datetime.timedelta(days=10 + indice),
                hora_inicio=disponibilidad.hora_inicio, formato="virtual",
                liga_virtual=disponibilidad.liga_virtual, estado="realizada", asistio=True,
            )

        self.sae_user = User.objects.create_user(email="sae-sem@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_lista_todos_los_semestres_del_sistema_descendente(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/semestres/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ["20262", "20261"])

    def test_no_duplica_semestres(self):
        segunda = self.disponibilidades["20261"]
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=segunda, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy - datetime.timedelta(days=17),
            hora_inicio=segunda.hora_inicio, formato="virtual",
            liga_virtual=segunda.liga_virtual, estado="realizada", asistio=True,
        )
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/semestres/")
        self.assertEqual(response.data, ["20262", "20261"])

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/admin/semestres/")
        self.assertEqual(response.status_code, 403)
