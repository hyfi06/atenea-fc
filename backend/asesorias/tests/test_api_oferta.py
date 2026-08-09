import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
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
            materia=self.materia_con_asesor, semestre="20271", defaults={"se_imparte": True}
        )

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.registro.materias.add(self.materia_con_asesor)
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
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

    def test_num_asesores_cuadra_con_lista_de_asesores(self):
        # Regresión de FIX-1: num_asesores debe contar registros con
        # disponibilidad activa, igual que AsesoresDeMateriaView. Un asesor con
        # dos registros (dos semestres) sobre la misma materia produce dos filas
        # en la lista de asesores; num_asesores debe reflejar ese mismo conteo.
        segundo_asesor_user = User.objects.create_user(email="asesor2@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=segundo_asesor_user, numero_trabajador="67890")
        segundo_asesor = PerfilAsesorAcademico.objects.create(user=segundo_asesor_user, area=self.area)
        registro_segundo = RegistroAsesor.objects.create(asesor=segundo_asesor, semestre="20271")
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
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
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
        self.alumno = PerfilAlumno.objects.create(
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
