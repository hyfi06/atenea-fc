import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia


class AsesoriaTestsBase(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
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
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        # Próximo lunes (dia_semana=0) en el pasado o futuro según el test lo necesite.
        self.proximo_lunes = self._proximo_dia_semana(0)
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)
        
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

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        delta = delta or 7
        return hoy + datetime.timedelta(days=delta)

    def _crear_asesoria(self, fecha, **overrides):
        defaults = dict(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=fecha, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        defaults.update(overrides)
        return Asesoria.objects.create(**defaults)


class AsesoriaConstraintTests(AsesoriaTestsBase):
    def test_fecha_no_coincide_con_dia_semana_falla_en_clean(self):
        martes = self.proximo_lunes + datetime.timedelta(days=1)
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=martes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        with self.assertRaises(ValidationError):
            asesoria.clean()

    def test_fecha_fuera_de_la_ventana_agendable_falla_en_clean(self):
        fecha_lejana = self.proximo_lunes + datetime.timedelta(days=28)
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=fecha_lejana, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        with self.assertRaises(ValidationError):
            asesoria.clean()


    def test_doble_booking_mismo_slot_mismo_dia_falla(self):
        asesoria = self._crear_asesoria(self.proximo_lunes)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._crear_asesoria(self.proximo_lunes)
        asesoria.delete()

    def test_slot_distinto_fecha_no_choca(self):
        asesoria1 = self._crear_asesoria(self.proximo_lunes)
        otro_lunes = self.proximo_lunes + datetime.timedelta(days=7)
        asesoria2 = self._crear_asesoria(otro_lunes)
        self.assertEqual(Asesoria.objects.count(), 2)
        asesoria1.delete()
        asesoria2.delete()

    def test_cancelar_libera_el_slot(self):
        asesoria = self._crear_asesoria(self.proximo_lunes)
        asesoria.cancelar(usuario=self.alumno.user)
        asesoria2 = self._crear_asesoria(self.proximo_lunes)
        self.assertEqual(Asesoria.objects.filter(fecha=self.proximo_lunes).count(), 2)
        asesoria.delete()
        asesoria2.delete()


class AsesoriaCicloDeVidaTests(AsesoriaTestsBase):
    def test_marcar_asistencia_antes_de_tiempo_falla(self):
        asesoria = self._crear_asesoria(self.proximo_lunes)
        with self.assertRaises(ValidationError):
            asesoria.marcar_asistencia(True)
        asesoria.delete()

    def test_marcar_asistencia_despues_de_la_fecha(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(True)
        asesoria.refresh_from_db()
        self.assertTrue(asesoria.asistio)
        self.assertEqual(asesoria.estado, "realizada")
        asesoria.delete()

    def test_guardar_notas_sin_asistencia_falla(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        with self.assertRaises(ValidationError):
            asesoria.guardar_notas("texto")
        asesoria.delete()

    def test_guardar_notas_con_asistencia_confirmada(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(True)
        asesoria.guardar_notas("Repasamos series de Taylor.")
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.notas, "Repasamos series de Taylor.")
        asesoria.delete()

    def test_guardar_notas_con_asistencia_falsa_falla(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(False)
        with self.assertRaises(ValidationError):
            asesoria.guardar_notas("texto")
        asesoria.delete()

    def test_cancelar_sesion_no_agendada_falla(self):
        asesoria = self._crear_asesoria(self.lunes_pasado)
        asesoria.marcar_asistencia(True)
        with self.assertRaises(ValidationError):
            asesoria.cancelar(usuario=self.alumno.user)
        asesoria.delete()