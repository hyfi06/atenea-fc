from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase

class RegistroAsesorApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrer test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.oferta = OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        self.academico = PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)

        self.otro_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        self.otro_academico = PerfilAcademico.objects.create(user=self.otro_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_user, area=self.area)
        self.registro_ajeno = RegistroAsesor.objects.create(asesor=self.otro_asesor, semestre="20271")

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        from accounts.models import PerfilAlumno
        self.alumno = PerfilAlumno.objects.create(user=self.alumno_user, numero_cuenta="312345678")
        
    def tearDown(self):
        self.alumno.delete()
        self.alumno_user.delete()
        self.registro_ajeno.delete()
        self.otro_asesor.delete()
        self.otro_academico.delete()
        self.otro_user.delete()
        self.asesor.delete()
        self.academico.delete()
        self.asesor_user.delete()
        self.oferta.delete()
        self.materia.delete()
        self.carrera.delete()
        self.area.delete()
        return super().tearDown()

    def test_alumno_no_puede_crear_registro(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": "20271"})
        self.assertEqual(response.status_code, 403)

    def test_asesor_crea_su_registro(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": "20271"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RegistroAsesor.objects.get(id=response.data["id"]).asesor, self.asesor)
        RegistroAsesor.objects.get(id=response.data["id"]).delete()

    def test_listar_solo_ve_sus_propios_registros(self):
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/registros/")
        self.assertEqual(len(response.data), 1)
        registro.delete()

    def test_agregar_materia_exitoso(self):
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/", {"materia_id": self.materia.id}
        )
        self.assertEqual(response.status_code, 200)
        registro.refresh_from_db()
        self.assertIn(self.materia, registro.materias.all())
        registro.delete()

    def test_agregar_materia_no_habilitada_devuelve_400(self):
        materia_no_habilitada = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=False,
        )
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/", {"materia_id": materia_no_habilitada.id}
        )
        self.assertEqual(response.status_code, 400)
        registro.delete()
        materia_no_habilitada.delete()

    def test_agregar_materia_a_registro_ajeno_devuelve_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/registros/{self.registro_ajeno.id}/materias/", {"materia_id": self.materia.id}
        )
        self.assertEqual(response.status_code, 403)