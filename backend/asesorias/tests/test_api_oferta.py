import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.servicios import semestre_vigente
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class OfertaApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.otra_carrera = Carrera.objects.create(clave=900, nombre="Carrera Ajena Test", area=self.area)

        self.materia_con_asesor = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_sin_asesor = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.get_or_create(
            materia=self.materia_con_asesor, semestre=semestre_vigente(), defaults={"se_imparte": True}
        )

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre=semestre_vigente())
        self.registro.materias.add(self.materia_con_asesor)
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = crear_alumno(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

    def test_oferta_solo_materias_con_asesor_disponible(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.status_code, 200)
        ids = {m["materia_id"] for m in response.data}
        self.assertIn(self.materia_con_asesor.id, ids)
        self.assertNotIn(self.materia_sin_asesor.id, ids)

    def test_oferta_incluye_num_asesores_y_carrera(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/")
        fila = next(m for m in response.data if m["materia_id"] == self.materia_con_asesor.id)
        self.assertEqual(fila["num_asesores"], 1)
        self.assertEqual(fila["carrera_id"], self.carrera.id)
        self.assertEqual(fila["nombre"], "Álgebra")

    def test_materia_con_disponibilidad_inactiva_no_aparece(self):
        Disponibilidad.objects.filter(registro=self.registro).update(activa=False)
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.data, [])

    def test_filtra_por_carrera(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/oferta/?carrera={self.otra_carrera.id}")
        self.assertEqual(response.data, [])

    def test_filtra_por_busqueda_de_nombre(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/?buscar=álge")
        ids = {m["materia_id"] for m in response.data}
        self.assertEqual(ids, {self.materia_con_asesor.id})

    def test_no_alumno_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.status_code, 403)

    def test_miembro_sae_puede_consultar_la_oferta(self):
        from accounts.models import PerfilSAE

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        self.client.force_authenticate(user=sae_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.status_code, 200)
        ids = {m["materia_id"] for m in response.data}
        self.assertIn(self.materia_con_asesor.id, ids)

    def test_num_asesores_cuadra_con_lista_de_asesores(self):
        # Regresión de FIX-1: num_asesores debe contar registros con
        # disponibilidad activa, igual que AsesoresDeMateriaView. Un asesor con
        # dos registros (dos semestres) sobre la misma materia produce dos filas
        # en la lista de asesores; num_asesores debe reflejar ese mismo conteo.
        segundo_asesor_user = User.objects.create_user(email="asesor2@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=segundo_asesor_user, numero_trabajador="67890")
        segundo_asesor = PerfilAsesorAcademico.objects.create(user=segundo_asesor_user, area=self.area)
        registro_segundo = RegistroAsesor.objects.create(asesor=segundo_asesor, semestre=semestre_vigente())
        registro_segundo.materias.add(self.materia_con_asesor)
        Disponibilidad.objects.create(
            registro=registro_segundo, dia_semana=2, hora_inicio=datetime.time(12, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )

        # Segundo registro del PRIMER asesor, en otro semestre, misma materia.
        registro_primero_otro_sem = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20272")
        registro_primero_otro_sem.materias.add(self.materia_con_asesor)
        Disponibilidad.objects.create(
            registro=registro_primero_otro_sem, dia_semana=3, hora_inicio=datetime.time(13, 0),
            formato="presencial", ubicacion="Salón 5",
        )

        self.client.force_authenticate(user=self.alumno_user)
        oferta = self.client.get("/api/asesorias/oferta/")
        fila = next(m for m in oferta.data if m["materia_id"] == self.materia_con_asesor.id)
        asesores = self.client.get(f"/api/asesorias/oferta/{self.materia_con_asesor.id}/asesores/")
        self.assertEqual(fila["num_asesores"], len(asesores.data))


class AsesoresDeMateriaApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_sin_asesores = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre=semestre_vigente())
        self.registro.materias.add(self.materia)
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=1, hora_inicio=datetime.time(11, 0),
            formato="presencial", ubicacion="Salón 4",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = crear_alumno(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

    def test_lista_asesores_con_identidad_y_formatos(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia.id}/asesores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        fila = response.data[0]
        self.assertEqual(fila["registro_id"], self.registro.id)
        self.assertEqual(fila["asesor_nombre"], self.asesor_user.nombre_completo)
        self.assertEqual(fila["area_nombre"], "Matemáticas")
        self.assertEqual(sorted(fila["formatos"]), ["presencial", "virtual"])

    def test_materia_sin_asesores_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia_sin_asesores.id}/asesores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_materia_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/999999/asesores/")
        self.assertEqual(response.status_code, 404)

    def test_no_alumno_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia.id}/asesores/")
        self.assertEqual(response.status_code, 403)

    def test_miembro_sae_puede_consultar_los_asesores_de_la_materia(self):
        from accounts.models import PerfilSAE

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        self.client.force_authenticate(user=sae_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia.id}/asesores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class OfertaScopeSemestreTests(APITestCase):
    """La oferta refleja el semestre vigente y a los asesores activos, no
    todo lo que tenga Disponibilidad.activa (deuda 0012, ADR 0027)."""

    def setUp(self):
        from accounts.models import PerfilAcademico, User
        from accounts.tests.factories import crear_alumno
        from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
        from asesorias.servicios import semestre_vigente
        from carreras.models import Area, Carrera
        from materias.models import Materia
        import datetime

        self.area = Area.objects.create(nombre="Area scope")
        self.carrera = Carrera.objects.create(clave=941, nombre="Carrera Scope Test", area=self.area)
        self.materia_vieja = Materia.objects.create(
            clave="1941", nombre="Materia Vieja", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_inactiva = Materia.objects.create(
            clave="1942", nombre="Materia De Inactivo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        def asesor(email, trabajador, activo=True):
            u = User.objects.create_user(email=email, password="x")
            PerfilAcademico.objects.create(user=u, numero_trabajador=trabajador)
            return PerfilAsesorAcademico.objects.create(user=u, area=self.area, activo=activo)

        registro_viejo = RegistroAsesor.objects.create(asesor=asesor("v@ciencias.unam.mx", "94001"), semestre="20191")
        registro_viejo.materias.add(self.materia_vieja)
        registro_inactivo = RegistroAsesor.objects.create(
            asesor=asesor("i@ciencias.unam.mx", "94002", activo=False), semestre=semestre_vigente()
        )
        registro_inactivo.materias.add(self.materia_inactiva)
        for registro in (registro_viejo, registro_inactivo):
            Disponibilidad.objects.create(
                registro=registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
                formato="virtual", liga_virtual="https://zoom.us/j/2", activa=True,
            )

        self.alumno_user = User.objects.create_user(email="alumno.scope@ciencias.unam.mx", password="x")
        crear_alumno(self.alumno_user, "312000033", carrera=self.carrera)
        self.client.force_authenticate(user=self.alumno_user)

    def test_la_oferta_ignora_registros_de_semestres_pasados(self):
        nombres = [fila["nombre"] for fila in self.client.get("/api/asesorias/oferta/").data]
        self.assertNotIn("Materia Vieja", nombres)

    def test_la_oferta_ignora_a_los_asesores_inactivos(self):
        nombres = [fila["nombre"] for fila in self.client.get("/api/asesorias/oferta/").data]
        self.assertNotIn("Materia De Inactivo", nombres)

    def test_asesores_de_materia_ignora_registros_de_semestres_pasados(self):
        response = self.client.get(f"/api/asesorias/oferta/{self.materia_vieja.id}/asesores/")
        self.assertEqual(response.data, [])

    def test_la_busqueda_ignora_registros_de_semestres_pasados(self):
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia_vieja.id}"
        )
        self.assertEqual(response.data, [])
