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
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

    def test_respuesta_trae_el_envelope_de_paginacion(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()), {"count", "next", "previous", "results"}
        )
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_detalle_no_trae_envelope(self):
        response = self.client.get(f"/api/materias/materias/{self.materia_habilitada.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["clave"], "1801")

    def test_filtrar_por_carrera(self):
        response = self.client.get(f"/api/materias/materias/?carrera={self.carrera1.id}")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801", "1802"})

    def test_filtrar_por_habilitada_asesorias(self):
        response = self.client.get("/api/materias/materias/?habilitada_asesorias=true")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801", "1901"})

    def test_filtrar_por_carrera_y_habilitada(self):
        response = self.client.get(
            f"/api/materias/materias/?carrera={self.carrera1.id}&habilitada_asesorias=true"
        )
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801"})

    def test_buscar_por_nombre_parcial_insensible_a_mayusculas(self):
        response = self.client.get("/api/materias/materias/?search=TOPO")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1901"})

    def test_buscar_por_clave(self):
        response = self.client.get("/api/materias/materias/?search=1802")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1802"})

    def test_buscar_combinado_con_carrera_y_habilitada(self):
        response = self.client.get(
            f"/api/materias/materias/?search=a&carrera={self.carrera1.id}"
            "&habilitada_asesorias=true"
        )
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801"})

    def test_buscar_sin_coincidencias_devuelve_lista_vacia(self):
        response = self.client.get("/api/materias/materias/?search=zzzzz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])


class PaginacionMateriasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Area paginacion")
        self.carrera = Carrera.objects.create(clave=803, nombre="Carrera paginacion", area=self.area)
        Materia.objects.bulk_create(
            [
                Materia(
                    clave=f"9{indice:03d}",
                    nombre=f"Materia {indice:03d}",
                    carrera=self.carrera,
                    nivel=1,
                    plan=2006,
                    habilitada_asesorias=True,
                )
                for indice in range(60)
            ]
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        Materia.objects.filter(carrera=self.carrera).delete()
        self.carrera.delete()
        self.area.delete()
        self.user.delete()

        return super().tearDown()

    def test_primera_pagina_trae_50_y_apunta_a_la_siguiente(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 60)
        self.assertEqual(len(response.data["results"]), 50)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_segunda_pagina_trae_el_resto_y_cierra_la_secuencia(self):
        response = self.client.get("/api/materias/materias/?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_paginas_no_repiten_materias(self):
        primera = self.client.get("/api/materias/materias/")
        segunda = self.client.get("/api/materias/materias/?page=2")
        claves = [m["clave"] for m in primera.data["results"]] + [
            m["clave"] for m in segunda.data["results"]
        ]
        self.assertEqual(len(claves), 60)
        self.assertEqual(len(set(claves)), 60)

    def test_pagina_fuera_de_rango_devuelve_404(self):
        response = self.client.get("/api/materias/materias/?page=99")
        self.assertEqual(response.status_code, 404)

    def test_busqueda_acotada_cabe_en_una_pagina(self):
        # "007" coincide con el nombre "Materia 007" y con la clave "9007" —
        # la misma fila, una sola vez: SearchFilter une los campos con OR.
        response = self.client.get("/api/materias/materias/?search=007")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertIsNone(response.data["next"])