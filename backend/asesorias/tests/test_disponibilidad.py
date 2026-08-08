import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia


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


class SesionesFuturasTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

    def _crear_asesoria(self, fecha, estado="agendada"):
        return Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=fecha, hora_inicio=self.disponibilidad.hora_inicio,
            formato="virtual", liga_virtual="https://meet.example.com/x", estado=estado,
        )

    def test_incluye_solo_las_agendadas_que_no_han_ocurrido(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        self._crear_asesoria(hoy - datetime.timedelta(days=7))
        self._crear_asesoria(hoy + datetime.timedelta(days=14), estado="cancelada")

        futuras = list(self.disponibilidad.sesiones_futuras())

        self.assertEqual(futuras, [futura])

    def test_una_sesion_de_hoy_que_ya_empezo_no_cuenta_como_futura(self):
        hoy = timezone.localdate()
        temprano = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=hoy.weekday(),
            hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=temprano, materia=self.materia,
            carrera=self.carrera, fecha=hoy, hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )

        self.assertEqual(list(temprano.sesiones_futuras()), [])

    def test_sin_sesiones_devuelve_vacio(self):
        self.assertEqual(list(self.disponibilidad.sesiones_futuras()), [])