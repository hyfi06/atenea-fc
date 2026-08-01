from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User
from carreras.models import Area, Carrera


class PerfilAlumnoTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=901, nombre="Carrera Test", area=self.area)

    def test_numero_cuenta_unico(self):
        user1 = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        user2 = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=user1, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAlumno.objects.create(
                user=user2, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
            )

    def test_un_user_no_puede_tener_dos_perfiles_alumno(self):
        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAlumno.objects.create(
                user=user, numero_cuenta="399999999", carrera=self.carrera, generacion=2023,
            )


class PerfilAcademicoTests(TestCase):
    def test_numero_trabajador_unico(self):
        user1 = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        user2 = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user1, numero_trabajador="12345")
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAcademico.objects.create(user=user2, numero_trabajador="12345")