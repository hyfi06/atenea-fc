from accounts.models import User
from carreras.models import Area, Carrera
from rest_framework.test import APITestCase


class CatalogoCarrerasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="a@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Test Area")
        self.carrera = Carrera.objects.create(
            clave=801, nombre="Test Carrera", area=self.area)

    def tearDown(self):
        self.carrera.delete()
        self.area.delete()
        self.user.delete()
        return super().tearDown()

    def test_sin_autenticacion_devuelve_401(self):
        response = self.client.get("/api/carreras/areas/")
        self.assertEqual(response.status_code, 401)

    def test_listar_areas(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/carreras/areas/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3+1) # 0002_seed_areas_carreras.py len(AREAS): 3 
        self.assertEqual(response.data[-1]["nombre"], "Test Area")

    def test_listar_carreras_incluye_area_anidada(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/carreras/carreras/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[-1]["nombre"], "Test Carrera")
        self.assertEqual(response.data[-1]["area"]["nombre"], "Test Area")

    def test_obtener_una_carrera(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/carreras/carreras/{self.carrera.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["clave"], 801)
