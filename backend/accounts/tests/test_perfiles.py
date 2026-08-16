from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
from carreras.models import Area, Carrera


class PerfilAlumnoTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=901, nombre="Carrera Test", area=self.area)

    def test_numero_cuenta_unico(self):
        user1 = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        user2 = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        crear_alumno(user=user1, numero_cuenta="312345678", carrera=self.carrera, generacion=2023)
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_alumno(user=user2, numero_cuenta="312345678", carrera=self.carrera, generacion=2023)

    def test_un_user_no_puede_tener_dos_perfiles_alumno(self):
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        crear_alumno(user=user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023)
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_alumno(user=user, numero_cuenta="399999999", carrera=self.carrera, generacion=2023)


class PerfilAcademicoTests(TestCase):
    def test_numero_trabajador_unico(self):
        user1 = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        user2 = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user1, numero_trabajador="12345")
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAcademico.objects.create(user=user2, numero_trabajador="12345")


class PerfilSAETests(TestCase):
    def test_un_user_no_puede_tener_dos_perfiles_sae(self):
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilSAE.objects.create(user=user)

    def test_nace_activo_y_es_accesible_por_related_name(self):
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae2@ciencias.unam.mx", password="x")
        perfil = PerfilSAE.objects.create(user=user)
        user.refresh_from_db()
        self.assertTrue(perfil.activo)
        self.assertTrue(hasattr(user, "perfil_sae"))
        self.assertEqual(user.perfil_sae.id, perfil.id)

    def test_usuario_sin_perfil_sae_no_tiene_el_atributo(self):
        user = User.objects.create_user(email="nadie@ciencias.unam.mx", password="x")
        self.assertFalse(hasattr(user, "perfil_sae"))


class HistoriaAcademicaTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area historia")
        self.carrera_a = Carrera.objects.create(clave=971, nombre="Carrera A Test", area=self.area)
        self.carrera_b = Carrera.objects.create(clave=972, nombre="Carrera B Test", area=self.area)
        self.user = User.objects.create_user(email="historia@ciencias.unam.mx", password="x")
        self.perfil = PerfilAlumno.objects.create(user=self.user, numero_cuenta="312000001")

    def test_un_alumno_puede_tener_dos_carreras_simultaneas(self):
        from accounts.models import HistoriaAcademica

        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2023
        )
        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_b, generacion=2025
        )
        self.assertEqual(self.perfil.historial.count(), 2)

    def test_no_se_repite_la_misma_carrera_para_el_mismo_alumno(self):
        from accounts.models import HistoriaAcademica

        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2023
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistoriaAcademica.objects.create(
                perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2024
            )

    def test_borrar_el_perfil_borra_su_historial(self):
        from accounts.models import HistoriaAcademica

        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2023
        )
        self.perfil.delete()
        self.assertEqual(HistoriaAcademica.objects.count(), 0)


class CorreosAlternosTests(TestCase):
    def test_nace_como_lista_vacia(self):
        user = User.objects.create_user(email="ca@ciencias.unam.mx", password="x")
        perfil = PerfilAlumno.objects.create(user=user, numero_cuenta="312000010")
        perfil.refresh_from_db()
        self.assertEqual(perfil.correos_alternos, [])

    def test_guarda_varios_correos(self):
        user = User.objects.create_user(email="cb@ciencias.unam.mx", password="x")
        perfil = PerfilAlumno.objects.create(
            user=user, numero_cuenta="312000011",
            correos_alternos=["viejo@gmail.com", "otro@ciencias.unam.mx"],
        )
        perfil.refresh_from_db()
        self.assertEqual(len(perfil.correos_alternos), 2)