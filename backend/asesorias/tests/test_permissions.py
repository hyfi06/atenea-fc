from types import SimpleNamespace

from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.permissions import EsAlumno, EsAsesorAcademico, EsDuenoDelRegistro, EsDuenoDeLaAsesoria
from carreras.models import Area, Carrera
from materias.models import Materia

import datetime


class PermissionsTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Área test")
        self.carrera = Carrera.objects.create(clave=901, nombre="Carrera Test", area=self.area)
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
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023)

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


class EsDuenoDeLaAsesoriaDobleRolTests(TestCase):
    """Un usuario con perfil de alumno Y de asesor es dueño de la sesión si es
    su alumno o su asesor — no solo del lado de alumno (deuda 0011)."""

    def setUp(self):
        self.area = Area.objects.create(nombre="Área test")
        self.carrera = Carrera.objects.create(clave=902, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1902", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        # Usuario con doble rol: es asesor (con registro/disponibilidad propios)
        # y a la vez alumno.
        self.doble_user = User.objects.create_user(email="doble@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.doble_user, numero_trabajador="70001")
        self.doble_asesor = PerfilAsesorAcademico.objects.create(user=self.doble_user, area=self.area)
        self.doble_alumno = PerfilAlumno.objects.create(
            user=self.doble_user, numero_cuenta="311111111", carrera=self.carrera, generacion=2023)
        self.registro_doble = RegistroAsesor.objects.create(asesor=self.doble_asesor, semestre="20271")
        self.disponibilidad_doble = Disponibilidad.objects.create(
            registro=self.registro_doble, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/d",
        )

        # Otro asesor (dueño de una disponibilidad distinta) y otro alumno.
        self.otro_asesor_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_asesor_user, numero_trabajador="70002")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_asesor_user, area=self.area)
        self.registro_otro = RegistroAsesor.objects.create(asesor=self.otro_asesor, semestre="20271")
        self.disponibilidad_otro = Disponibilidad.objects.create(
            registro=self.registro_otro, dia_semana=1, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/o",
        )
        self.otro_alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.otro_alumno = PerfilAlumno.objects.create(
            user=self.otro_alumno_user, numero_cuenta="322222222", carrera=self.carrera, generacion=2023)

        fecha = datetime.date(2027, 8, 9)
        # Sesión donde doble_user es el ASESOR (el alumno es otro).
        self.asesoria_como_asesor = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad_doble, materia=self.materia,
            carrera=self.carrera, fecha=fecha, hora_inicio=self.disponibilidad_doble.hora_inicio,
            formato="virtual", liga_virtual="https://meet.example.com/d",
        )
        # Sesión donde doble_user es el ALUMNO (el asesor es otro).
        self.asesoria_como_alumno = Asesoria.objects.create(
            alumno=self.doble_alumno, disponibilidad=self.disponibilidad_otro, materia=self.materia,
            carrera=self.carrera, fecha=fecha, hora_inicio=self.disponibilidad_otro.hora_inicio,
            formato="virtual", liga_virtual="https://meet.example.com/o",
        )
        # Sesión ajena: doble_user no es ni alumno ni asesor.
        self.asesoria_ajena = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad_otro, materia=self.materia,
            carrera=self.carrera, fecha=fecha + datetime.timedelta(days=7),
            hora_inicio=self.disponibilidad_otro.hora_inicio,
            formato="virtual", liga_virtual="https://meet.example.com/o",
        )

    def test_true_cuando_es_el_asesor_dueño_aunque_tenga_perfil_alumno(self):
        request = SimpleNamespace(user=self.doble_user)
        self.assertTrue(EsDuenoDeLaAsesoria().has_object_permission(
            request, None, self.asesoria_como_asesor))

    def test_true_cuando_es_el_alumno_de_la_sesion(self):
        request = SimpleNamespace(user=self.doble_user)
        self.assertTrue(EsDuenoDeLaAsesoria().has_object_permission(
            request, None, self.asesoria_como_alumno))

    def test_false_cuando_no_es_ni_alumno_ni_asesor_de_la_sesion(self):
        request = SimpleNamespace(user=self.doble_user)
        self.assertFalse(EsDuenoDeLaAsesoria().has_object_permission(
            request, None, self.asesoria_ajena))
