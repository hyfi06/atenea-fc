from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico
from carreras.models import Area


class PerfilAsesorAcademicoTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Test Area")
        self.user = User.objects.create_user(
            email="a@ciencias.unam.mx", password="x")

    def tearDown(self):
        self.area.delete()
        self.user.delete()

    def test_requiere_perfil_academico(self):
        asesor = PerfilAsesorAcademico(user=self.user, area=self.area)
        with self.assertRaises(ValidationError):
            asesor.clean()

    def test_se_crea_con_perfil_academico(self):
        academico = PerfilAcademico.objects.create(
            user=self.user, numero_trabajador="12345")
        asesor = PerfilAsesorAcademico(user=self.user, area=self.area)
        asesor.clean()  # no lanza
        asesor.save()
        self.assertEqual(PerfilAsesorAcademico.objects.count(), 1)
        asesor.delete()
        academico.delete()

    def test_un_user_no_puede_tener_dos_perfiles_de_asesor(self):
        academico = PerfilAcademico.objects.create(
            user=self.user, numero_trabajador="12345")
        asesor1 = PerfilAsesorAcademico.objects.create(
            user=self.user, area=self.area)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilAsesorAcademico.objects.create(
                user=self.user, area=self.area)
        academico.delete()
        asesor1.delete()
