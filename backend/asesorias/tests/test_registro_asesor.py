import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria


class RegistroAsesorTests(TestCase):
    def setUp(self):
        self.area_mate = Area.objects.create(nombre="Test Area 1")
        self.area_bio = Area.objects.create(nombre="Test Area 2")
        self.carrera = Carrera.objects.create(clave=801, nombre="Test Carrera 1", area=self.area_mate)
        self.carrera_bio = Carrera.objects.create(clave=901, nombre="Test Carrera 2", area=self.area_bio)

        user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=user, area=self.area_mate)

        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def _materia(self, **overrides):
        defaults = dict(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        defaults.update(overrides)
        return Materia.objects.create(**defaults)

    def test_unique_asesor_semestre(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def test_agregar_materia_exitoso(self):
        materia = self._materia()
        OfertaMateria.objects.create(materia=materia, semestre="20271", se_imparte=True)
        self.registro.agregar_materia(materia)
        self.assertIn(materia, self.registro.materias.all())

    def test_agregar_materia_de_otra_area_no_falla(self):
        materia = self._materia(clave="2001", carrera=self.carrera_bio)
        OfertaMateria.objects.create(materia=materia, semestre="20271", se_imparte=True)
        self.registro.agregar_materia(materia)
        self.assertIn(materia, self.registro.materias.all())

    def test_agregar_materia_no_habilitada_falla(self):
        materia = self._materia(clave="1802", habilitada_asesorias=False)
        OfertaMateria.objects.create(materia=materia, semestre="20271", se_imparte=True)
        with self.assertRaises(ValidationError):
            self.registro.agregar_materia(materia)

    def test_agregar_materia_sin_oferta_del_semestre_falla(self):
        materia = self._materia(clave="1803")
        with self.assertRaises(ValidationError):
            self.registro.agregar_materia(materia)


class QuitarMateriaTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)
        self.user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def test_quitar_una_materia_del_registro(self):
        self.registro.agregar_materia(self.materia)

        self.registro.quitar_materia(self.materia)

        self.assertNotIn(self.materia, self.registro.materias.all())

    def test_quitar_una_materia_que_no_esta_levanta_validation_error(self):
        with self.assertRaises(ValidationError):
            self.registro.quitar_materia(self.materia)

    def test_quitar_una_materia_no_cancela_las_asesorias_agendadas(self):
        """La promesa explícita del diálogo de confirmación: 'Las asesorías
        ya agendadas no se cancelan.'"""
        self.registro.agregar_materia(self.materia)
        disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        alumno = crear_alumno(
            user=alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        asesoria = Asesoria.objects.create(
            alumno=alumno, disponibilidad=disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=timezone.localdate() + datetime.timedelta(days=7),
            hora_inicio=datetime.time(10, 0), formato="virtual",
            liga_virtual="https://meet.example.com/x",
        )

        self.registro.quitar_materia(self.materia)

        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "agendada")