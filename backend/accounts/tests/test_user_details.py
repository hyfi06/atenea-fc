from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import PerfilAsesorAcademico
from carreras.models import Area, Carrera
from rest_framework.test import APITestCase


class UserDetailsApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)

    def test_usuario_sin_perfiles_reporta_roles_vacios(self):
        user = User.objects.create_user(email="nadie@ciencias.unam.mx", password="x")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], [])
        self.assertIsNone(response.data["perfil_alumno"])
        self.assertIsNone(response.data["perfil_academico"])
        self.assertIsNone(response.data["perfil_asesor_academico"])

    def test_alumno_reporta_su_rol_y_su_perfil(self):
        user = User.objects.create_user(
            email="alumna@ciencias.unam.mx", password="x", first_name="Ana",
        )
        user.apellido1 = "López"
        user.apellido2 = "Ruiz"
        user.save()
        perfil = PerfilAlumno.objects.create(
            user=user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], ["alumno"])
        self.assertEqual(response.data["nombre_completo"], "Ana López Ruiz")
        self.assertEqual(response.data["apellido1"], "López")
        self.assertEqual(
            response.data["perfil_alumno"],
            {
                "id": perfil.id,
                "numero_cuenta": "312345678",
                "carrera": self.carrera.id,
                "carrera_nombre": "Carrera Test",
                "generacion": 2023,
            },
        )

    def test_asesor_academico_reporta_ambos_roles(self):
        user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        perfil_asesor = PerfilAsesorAcademico.objects.create(user=user, area=self.area)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(response.data["roles"]), ["academico", "asesor_academico"])
        self.assertEqual(
            response.data["perfil_asesor_academico"],
            {
                "id": perfil_asesor.id,
                "area": self.area.id,
                "area_nombre": "Area test",
                "activo": True,
            },
        )
        self.assertEqual(response.data["perfil_academico"]["numero_trabajador"], "12345")

    def test_asesor_inactivo_conserva_el_rol_y_reporta_activo_false(self):
        """El rol sigue el criterio de la permission class EsAsesorAcademico,
        que solo comprueba que el perfil exista."""
        user = User.objects.create_user(email="inactivo@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="54321")
        PerfilAsesorAcademico.objects.create(user=user, area=self.area, activo=False)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertIn("asesor_academico", response.data["roles"])
        self.assertFalse(response.data["perfil_asesor_academico"]["activo"])

    def test_nombre_completo_cae_al_email_si_no_hay_nombre(self):
        user = User.objects.create_user(email="sin-nombre@ciencias.unam.mx", password="x")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.data["nombre_completo"], "sin-nombre@ciencias.unam.mx")

    def test_los_campos_de_perfil_no_son_escribibles(self):
        user = User.objects.create_user(email="rw@ciencias.unam.mx", password="x")
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            "/api/auth/user/",
            {"first_name": "Nuevo", "apellido1": "Hackeado", "roles": ["academico"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Nuevo")
        self.assertEqual(user.apellido1, "")
        self.assertEqual(response.data["roles"], [])

    def test_el_login_devuelve_los_roles_en_el_body(self):
        """El mismo serializer alimenta la clave 'user' de /api/auth/login/,
        así que el SPA obtiene el rol sin una segunda llamada."""
        user = User.objects.create_user(email="login@ciencias.unam.mx", password="ClaveSegura123!")
        PerfilAlumno.objects.create(
            user=user, numero_cuenta="312345679", carrera=self.carrera, generacion=2024,
        )

        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "ClaveSegura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["roles"], ["alumno"])

    def test_miembro_sae_reporta_el_rol_sae(self):
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=user)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], ["sae"])

    def test_usuario_sin_perfil_sae_no_reporta_el_rol(self):
        user = User.objects.create_user(email="no-sae@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=user, numero_cuenta="312999999", carrera=self.carrera, generacion=2023,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertNotIn("sae", response.data["roles"])

    def test_sae_inactivo_conserva_el_rol(self):
        """El rol depende de que el perfil exista, no de `activo` — mismo
        criterio que EsAsesorAcademico y que la permission EsMiembroSAE."""
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae-inactivo@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=user, activo=False)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertIn("sae", response.data["roles"])
