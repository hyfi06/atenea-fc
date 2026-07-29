from django.db import IntegrityError, transaction
from django.test import TestCase

from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria


class MateriaClaveUnicaTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Área de Prueba")
        self.carrera = Carrera.objects.create(clave=990, nombre="Carrera de Prueba", area=area)

    def test_clave_unica(self):
        Materia.objects.create(
            clave="1801", nombre="Administración Actuarial", carrera=self.carrera,
            nivel=8, plan=2006,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Materia.objects.create(
                clave="1801", nombre="Otra materia", carrera=self.carrera,
                nivel=1, plan=2006,
            )

    def test_nivel_nulo_es_optativa(self):
        materia = Materia.objects.create(
            clave="1817", nombre="Administración de Riesgos", carrera=self.carrera,
            nivel=None, plan=2006,
        )
        self.assertIsNone(materia.nivel)


class OfertaMateriaConstraintTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Área de Prueba Oferta")
        carrera = Carrera.objects.create(clave=991, nombre="Carrera de Prueba Oferta", area=area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Administración Actuarial", carrera=carrera,
            nivel=8, plan=2006,
        )

    def test_una_oferta_por_materia_y_semestre(self):
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=False)

    def test_misma_materia_en_semestres_distintos(self):
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)
        OfertaMateria.objects.create(materia=self.materia, semestre="20272", se_imparte=False)
        self.assertEqual(self.materia.ofertas.count(), 2)
