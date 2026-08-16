import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, PerfilSAE, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia
from rest_framework.test import APITestCase

# El directorio no lleva corte; la constante sólo se usa para dimensionar el
# fixture del test que lo comprueba.
LIMITE_AUTOCOMPLETAR_ASESORES_ESPERADO = 20


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
        self.alumno1 = crear_alumno(
            user=self.alumno1_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.alumno2_user = User.objects.create_user(
            email="alumno2@ciencias.unam.mx", password="x", first_name="Rosa",
        )
        self.alumno2 = crear_alumno(
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

    def test_admin_asesorias_rechaza_escritura(self):
        # Solo lectura: la superficie admin no expone métodos de escritura.
        self.client.force_authenticate(user=self.sae_user)
        for metodo in (self.client.post, self.client.patch, self.client.delete):
            respuesta = metodo("/api/asesorias/admin/asesorias/")
            self.assertEqual(respuesta.status_code, 405)


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
        self.alumno = crear_alumno(
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


class AdminAsesoresApiTests(APITestCase):
    def setUp(self):
        from asesorias.servicios import semestre_vigente

        self.semestre = semestre_vigente()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia1 = Materia.objects.create(
            clave="1821", nombre="Topología", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia2 = Materia.objects.create(
            clave="1822", nombre="Variable Compleja", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        # Asesor activo con 2 materias en el semestre vigente y 1 en otro.
        self.activo_user = User.objects.create_user(
            email="zeta@ciencias.unam.mx", password="x", first_name="Zoe",
        )
        PerfilAcademico.objects.create(user=self.activo_user, numero_trabajador="30001")
        self.asesor_activo = PerfilAsesorAcademico.objects.create(
            user=self.activo_user, area=self.area, activo=True,
        )
        registro_vigente = RegistroAsesor.objects.create(
            asesor=self.asesor_activo, semestre=self.semestre,
        )
        registro_vigente.materias.add(self.materia1, self.materia2)
        registro_viejo = RegistroAsesor.objects.create(asesor=self.asesor_activo, semestre="20191")
        registro_viejo.materias.add(self.materia1)

        # Asesor inactivo sin registro en el semestre vigente.
        self.inactivo_user = User.objects.create_user(
            email="alfa@ciencias.unam.mx", password="x", first_name="Aldo",
        )
        PerfilAcademico.objects.create(user=self.inactivo_user, numero_trabajador="30002")
        self.asesor_inactivo = PerfilAsesorAcademico.objects.create(
            user=self.inactivo_user, area=self.area, activo=False,
        )

        self.sae_user = User.objects.create_user(email="sae-dir@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_lista_todos_los_asesores_ordenados_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        self.assertEqual(response.status_code, 200)
        nombres = [a["nombre"] for a in response.data]
        self.assertEqual(nombres, sorted(nombres))
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_activo.id, self.asesor_inactivo.id})

    def test_incluye_area_y_activo(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_inactivo.id)
        self.assertEqual(fila["area_nombre"], "Matemáticas")
        self.assertFalse(fila["activo"])
        self.assertEqual(fila["nombre"], self.inactivo_user.nombre_completo)

    def test_cuenta_materias_solo_del_semestre_vigente(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_activo.id)
        self.assertEqual(fila["num_materias_semestre_vigente"], 2)

    def test_asesor_sin_registro_vigente_cuenta_cero(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_inactivo.id)
        self.assertEqual(fila["num_materias_semestre_vigente"], 0)

    def test_incluye_numero_trabajador(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_activo.id)
        self.assertEqual(fila["numero_trabajador"], "30001")

    def test_asesor_sin_perfil_academico_reporta_numero_trabajador_vacio(self):
        sin_perfil_user = User.objects.create_user(
            email="sin-perfil@ciencias.unam.mx", password="x", first_name="Nadia",
        )
        sin_perfil = PerfilAsesorAcademico.objects.create(
            user=sin_perfil_user, area=self.area, activo=True,
        )
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        self.assertEqual(response.status_code, 200)
        fila = next(a for a in response.data if a["perfil_id"] == sin_perfil.id)
        self.assertEqual(fila["numero_trabajador"], "")

    def test_sin_buscar_devuelve_todos(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_activo.id, self.asesor_inactivo.id})

    def test_busca_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=zo")
        self.assertEqual(response.status_code, 200)
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_activo.id})

    def test_busca_por_numero_de_trabajador(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=30002")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_inactivo.id})

    def test_busqueda_sin_coincidencias_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=zzzzz")
        self.assertEqual(response.data, [])

    def test_la_busqueda_conserva_el_orden_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=3000")
        nombres = [a["nombre"] for a in response.data]
        self.assertEqual(nombres, sorted(nombres))

    def test_la_busqueda_respeta_el_limite_de_resultados(self):
        from asesorias.views import LIMITE_AUTOCOMPLETAR_ASESORES

        for indice in range(LIMITE_AUTOCOMPLETAR_ASESORES + 5):
            user = User.objects.create_user(
                email=f"masivo{indice}@ciencias.unam.mx", password="x", first_name="Masivo",
            )
            PerfilAcademico.objects.create(user=user, numero_trabajador=f"9000{indice:02d}")
            PerfilAsesorAcademico.objects.create(user=user, area=self.area, activo=True)
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=masivo")
        self.assertEqual(len(response.data), LIMITE_AUTOCOMPLETAR_ASESORES)

    def test_el_directorio_sin_buscar_no_lleva_corte(self):
        for indice in range(LIMITE_AUTOCOMPLETAR_ASESORES_ESPERADO + 5):
            user = User.objects.create_user(
                email=f"pleno{indice}@ciencias.unam.mx", password="x", first_name="Pleno",
            )
            PerfilAcademico.objects.create(user=user, numero_trabajador=f"8000{indice:02d}")
            PerfilAsesorAcademico.objects.create(user=user, area=self.area, activo=True)
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        # Los 2 del setUp + los 25 recién creados: el directorio va completo.
        self.assertEqual(len(response.data), 27)

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.activo_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        self.assertEqual(response.status_code, 403)


class AdminAsesorDetalleApiTests(APITestCase):
    def setUp(self):
        from asesorias.servicios import semestre_vigente

        self.semestre = semestre_vigente()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia_vigente = Materia.objects.create(
            clave="1831", nombre="Cálculo III", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_vieja = Materia.objects.create(
            clave="1832", nombre="Ecuaciones Diferenciales", carrera=self.carrera, nivel=1,
            plan=2006, habilitada_asesorias=True,
        )

        self.asesor_user = User.objects.create_user(
            email="detalle@ciencias.unam.mx", password="x", first_name="Ana",
        )
        self.asesor_user.apellido1 = "López"
        self.asesor_user.save()
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="40001")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)

        self.registro_vigente = RegistroAsesor.objects.create(
            asesor=self.asesor, semestre=self.semestre,
        )
        self.registro_vigente.materias.add(self.materia_vigente)
        self.disp_vigente = Disponibilidad.objects.create(
            registro=self.registro_vigente, dia_semana=1, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 4",
        )

        self.registro_viejo = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20191")
        self.registro_viejo.materias.add(self.materia_vieja)
        self.disp_vieja = Disponibilidad.objects.create(
            registro=self.registro_viejo, dia_semana=3, hora_inicio=datetime.time(16, 30),
            formato="virtual", liga_virtual="https://meet.example.com/viejo",
        )

        self.sae_user = User.objects.create_user(email="sae-det@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_detalle_por_defecto_usa_el_semestre_vigente(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["perfil_id"], self.asesor.id)
        self.assertEqual(response.data["nombre"], "Ana López")
        self.assertEqual(response.data["area_nombre"], "Matemáticas")
        self.assertTrue(response.data["activo"])
        self.assertEqual(response.data["semestre"], self.semestre)
        self.assertEqual(
            [m["clave"] for m in response.data["materias"]], ["1831"]
        )

    def test_materias_incluyen_id_clave_y_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(
            response.data["materias"][0],
            {"id": self.materia_vigente.id, "clave": "1831", "nombre": "Cálculo III"},
        )

    def test_disponibilidades_incluyen_hora_fin_y_formato(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(
            response.data["disponibilidades"][0],
            {
                "id": self.disp_vigente.id,
                "dia_semana": 1,
                "hora_inicio": "10:00:00",
                "hora_fin": "10:30:00",
                "formato": "presencial",
                "ubicacion": "Salón 4",
                "liga_virtual": "",
                "activa": True,
            },
        )

    def test_semestre_explicito_devuelve_ese_registro(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(
            f"/api/asesorias/admin/asesores/{self.asesor.id}/?semestre=20191"
        )
        self.assertEqual(response.data["semestre"], "20191")
        self.assertEqual([m["clave"] for m in response.data["materias"]], ["1832"])
        self.assertEqual(
            [d["id"] for d in response.data["disponibilidades"]], [self.disp_vieja.id]
        )

    def test_semestre_sin_registro_devuelve_listas_vacias(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(
            f"/api/asesorias/admin/asesores/{self.asesor.id}/?semestre=19991"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["semestre"], "19991")
        self.assertEqual(response.data["materias"], [])
        self.assertEqual(response.data["disponibilidades"], [])

    def test_perfil_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/999999/")
        self.assertEqual(response.status_code, 404)

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(response.status_code, 403)


class AdminAlumnosApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")

        self.juan_user = User.objects.create_user(
            email="juan@ciencias.unam.mx", password="x", first_name="Juan",
        )
        self.juan_user.apellido1 = "Pérez"
        self.juan_user.save()
        self.juan = crear_alumno(
            user=self.juan_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        self.rosa_user = User.objects.create_user(
            email="rosa@ciencias.unam.mx", password="x", first_name="Rosa",
        )
        self.rosa_user.apellido1 = "Gómez"
        self.rosa_user.save()
        self.rosa = crear_alumno(
            user=self.rosa_user, numero_cuenta="420000001", carrera=self.carrera, generacion=2024,
        )

        self.sae_user = User.objects.create_user(email="sae-alu@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_busca_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=jua")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [{"perfil_id": self.juan.id, "nombre": "Juan Pérez", "numero_cuenta": "312345678", "correos_alternos": []}],
        )

    def test_busca_por_apellido(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=góm")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.rosa.id})

    def test_busca_por_numero_de_cuenta(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=4200")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.rosa.id})

    def test_busqueda_sin_coincidencias_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=zzzzz")
        self.assertEqual(response.data, [])

    def test_respeta_el_limite_de_resultados(self):
        from asesorias.views import LIMITE_AUTOCOMPLETAR_ALUMNOS

        for indice in range(LIMITE_AUTOCOMPLETAR_ALUMNOS + 5):
            user = User.objects.create_user(
                email=f"masivo{indice}@ciencias.unam.mx", password="x", first_name="Masivo",
            )
            crear_alumno(
                user=user, numero_cuenta=f"5000000{indice:02d}", carrera=self.carrera,
                generacion=2025,
            )
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=masivo")
        self.assertEqual(len(response.data), LIMITE_AUTOCOMPLETAR_ALUMNOS)

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.juan_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=jua")
        self.assertEqual(response.status_code, 403)

    def test_el_sae_ve_los_correos_alternos_del_alumno(self):
        self.juan.correos_alternos = ["juan.viejo@gmail.com"]
        self.juan.save()
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=Juan")
        fila = next(f for f in response.data if f["perfil_id"] == self.juan.id)
        self.assertEqual(fila["correos_alternos"], ["juan.viejo@gmail.com"])
