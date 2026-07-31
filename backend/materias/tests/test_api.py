from accounts.models import User
from carreras.models import Area, Carrera
from materias.models import Materia
from rest_framework.test import APITestCase


class CatalogoMateriasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Test area")
        self.carrera1 = Carrera.objects.create(clave=801, nombre="Test carrera 1", area=self.area)
        self.carrera2 = Carrera.objects.create(clave=802, nombre="Test carrera 2", area=self.area)
        self.materia_habilitada = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera1, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_no_habilitada = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera1, nivel=1, plan=2006,
            habilitada_asesorias=False,
        )
        self.materia_otra_carrera = Materia.objects.create(
            clave="1901", nombre="Topología", carrera=self.carrera2, nivel=3, plan=2006,
            habilitada_asesorias=True,
        )
        self.client.force_authenticate(user=self.user)
    
    def tearDown(self):
        self.materia_otra_carrera.delete()
        self.materia_no_habilitada.delete()
        self.materia_habilitada.delete()
        self.carrera2.delete()
        self.carrera1.delete()
        self.area.delete()
        self.user.delete()
        
        return super().tearDown()

    def test_listar_todas(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_filtrar_por_carrera(self):
        response = self.client.get(f"/api/materias/materias/?carrera={self.carrera1.id}")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data}
        self.assertEqual(claves, {"1801", "1802"})

    def test_filtrar_por_habilitada_asesorias(self):
        response = self.client.get("/api/materias/materias/?habilitada_asesorias=true")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data}
        self.assertEqual(claves, {"1801", "1901"})

    def test_filtrar_por_carrera_y_habilitada(self):
        response = self.client.get(
            f"/api/materias/materias/?carrera={self.carrera1.id}&habilitada_asesorias=true"
        )
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data}
        self.assertEqual(claves, {"1801"})