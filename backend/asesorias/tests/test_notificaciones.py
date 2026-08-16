import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia


class NotificacionesTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area Test")
        self.carrera = Carrera.objects.create(clave=901, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        self.academico = PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = crear_alumno(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        hoy = timezone.localdate()
        delta = (0 - hoy.weekday()) % 7 or 7
        self.proximo_lunes = hoy + datetime.timedelta(days=delta)
    
    def tearDown(self):
        self.alumno.delete()
        self.alumno_user.delete()
        self.registro.delete()
        self.asesor.delete()
        self.academico.delete()
        self.asesor_user.delete()
        self.materia.delete()
        self.carrera.delete()
        self.area.delete()
        return super().tearDown()

    @patch("asesorias.tasks.enviar_confirmacion_agenda.delay")
    def test_crear_asesoria_encola_confirmacion(self, mock_delay):
        with self.captureOnCommitCallbacks(execute=True):
            asesoria = Asesoria.objects.create(
                alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
                carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
                formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
            )
        mock_delay.assert_called_once_with(asesoria.id)
        asesoria.delete()

    @patch("asesorias.tasks.enviar_notificacion_cancelacion.delay")
    @patch("asesorias.tasks.enviar_confirmacion_agenda.delay")
    def test_cancelar_encola_notificacion_de_cancelacion(self, _mock_confirmacion, mock_cancelacion):
        with self.captureOnCommitCallbacks(execute=True):
            asesoria = Asesoria.objects.create(
                alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
                carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
                formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
            )
        with self.captureOnCommitCallbacks(execute=True):
            asesoria.cancelar(usuario=self.alumno.user)
        mock_cancelacion.assert_called_once_with(asesoria.id)
        asesoria.delete()

