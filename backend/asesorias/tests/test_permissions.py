from types import SimpleNamespace

from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.permissions import EsAlumno, EsAsesorAcademico, EsDuenoDelRegistro
from carreras.models import Area

import datetime


class PermissionsTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Área test")
        self.asesor_user = User.objects.create_user(
            email="asesor@ciencias.unam.mx", password="x")
        self.academico =PerfilAcademico.objects.create(
            user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(
            user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(
            asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.otro_asesor_user = User.objects.create_user(
            email="otro@ciencias.unam.mx", password="x")
        self.otro_academico = PerfilAcademico.objects.create(
            user=self.otro_asesor_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(
            user=self.otro_asesor_user, area=self.area)

        self.alumno_user = User.objects.create_user(
            email="alumno@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678")

    def tearDown(self):
        self.alumno_user.delete()
        self.otro_asesor.delete()
        self.otro_academico.delete()
        self.otro_asesor_user.delete()
        self.disponibilidad.delete()
        self.registro.delete()
        self.academico.delete()
        self.asesor.delete()
        self.asesor_user.delete()
        
        return super().tearDown()

    def test_es_alumno_true_para_usuario_con_perfil_alumno(self):
        request = SimpleNamespace(user=self.alumno_user)
        self.assertTrue(EsAlumno().has_permission(request, None))

    def test_es_alumno_false_para_asesor(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertFalse(EsAlumno().has_permission(request, None))

    def test_es_asesor_academico_true_para_asesor(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertTrue(EsAsesorAcademico().has_permission(request, None))

    def test_es_asesor_academico_false_para_alumno(self):
        request = SimpleNamespace(user=self.alumno_user)
        self.assertFalse(EsAsesorAcademico().has_permission(request, None))

    def test_dueño_del_registro_true_para_su_propio_registro(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertTrue(EsDuenoDelRegistro().has_object_permission(
            request, None, self.registro))

    def test_dueño_del_registro_false_para_otro_asesor(self):
        request = SimpleNamespace(user=self.otro_asesor_user)
        self.assertFalse(EsDuenoDelRegistro().has_object_permission(
            request, None, self.registro))

    def test_dueño_del_registro_true_para_su_propia_disponibilidad(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertTrue(EsDuenoDelRegistro().has_object_permission(
            request, None, self.disponibilidad))

    def test_dueño_del_registro_false_para_disponibilidad_de_otro_asesor(self):
        request = SimpleNamespace(user=self.otro_asesor_user)
        self.assertFalse(EsDuenoDelRegistro().has_object_permission(
            request, None, self.disponibilidad))
