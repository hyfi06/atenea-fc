from django.contrib import admin
from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User


class AdminRegistrationTests(TestCase):
    def test_perfil_alumno_registrado(self):
        self.assertIn(PerfilAlumno, admin.site._registry)

    def test_perfil_academico_registrado(self):
        self.assertIn(PerfilAcademico, admin.site._registry)

    def test_user_registrado(self):
        self.assertIn(User, admin.site._registry)

    def test_perfil_sae_registrado(self):
        from accounts.models import PerfilSAE

        self.assertIn(PerfilSAE, admin.site._registry)
