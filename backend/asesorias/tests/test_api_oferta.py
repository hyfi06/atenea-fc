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
