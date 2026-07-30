from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico, RegistroAsesor
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