import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area


class DisponibilidadTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Test Area 1")
        self.user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        self.academico =PerfilAcademico.objects.create(user=self.user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def tearDown(self):
        self.registro.delete()
        self.asesor.delete()
        self.academico.delete()
        self.user.delete()
        self.area.delete()
        return super().tearDown()
      
    def test_bloque_valido_presencial(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 3",
        )
        disp.clean()  # no lanza
        disp.save()
        self.assertEqual(disp.hora_fin, datetime.time(10, 30))
        disp.delete()

    def test_bloque_valido_virtual(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 30),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        disp.clean()  # no lanza

    def test_hora_fuera_de_rejilla_falla(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 15),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        with self.assertRaises(ValidationError):
            disp.clean()

    def test_presencial_sin_ubicacion_falla(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial",
        )
        with self.assertRaises(ValidationError):
            disp.clean()

    def test_virtual_sin_liga_falla(self):
        disp = Disponibilidad(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual",
        )
        with self.assertRaises(ValidationError):
            disp.clean()

    def test_bloque_duplicado_falla(self):
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Disponibilidad.objects.create(
                registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
                formato="presencial", ubicacion="Salón 1",
            )

    def test_bloques_no_contiguos_del_mismo_dia(self):
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(9, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(14, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.assertEqual(self.registro.disponibilidades.count(), 2)