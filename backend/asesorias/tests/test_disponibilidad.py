import datetime
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
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
        self.alumno = crear_alumno(
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


class DesactivarDisponibilidadTests(SesionesFuturasTests):
    def test_desactivar_sin_cancelar_conserva_las_sesiones(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        canceladas = self.disponibilidad.desactivar(usuario=self.asesor_user)

        self.assertEqual(canceladas, 0)
        self.disponibilidad.refresh_from_db()
        self.assertFalse(self.disponibilidad.activa)
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "agendada")

    def test_desactivar_cancelando_cancela_solo_las_futuras(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        pasada = self._crear_asesoria(hoy - datetime.timedelta(days=7))

        canceladas = self.disponibilidad.desactivar(
            usuario=self.asesor_user, cancelar_sesiones=True, motivo="Cambio de horario.",
        )

        self.assertEqual(canceladas, 1)
        self.disponibilidad.refresh_from_db()
        self.assertFalse(self.disponibilidad.activa)
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "cancelada")
        self.assertEqual(futura.motivo_cancelacion, "Cambio de horario.")
        self.assertEqual(futura.cancelado_por, self.asesor_user)
        pasada.refresh_from_db()
        self.assertEqual(pasada.estado, "agendada")

    def test_motivo_vacio_usa_el_texto_por_defecto(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        self.disponibilidad.desactivar(usuario=self.asesor_user, cancelar_sesiones=True)

        futura.refresh_from_db()
        self.assertEqual(futura.motivo_cancelacion, "El asesor dio de baja este horario.")


class DesactivarDentroDeLaVentanaTests(SesionesFuturasTests):
    """Caso borde explícito del spec: la baja de un bloque por parte del asesor
    cancela también las sesiones que arrancan en menos de 2 horas — no es el
    alumno cancelando de último minuto, es el asesor invalidando el bloque."""

    def _bloque_que_arranca_en_menos_de_dos_horas(self):
        """Bloque cuya hora en punto cae entre 30 y 90 minutos en el futuro.

        `ahora + 90 min` truncado a la hora en punto da una separación de
        `60 - minuto` (si el minuto es < 30) o `120 - minuto` (si es >= 30):
        siempre > 30 min, así que entra en `sesiones_futuras()` sin carrera con
        el reloj, y siempre < 120 min, así que cae dentro de la ventana mínima.

        Vive en un registro aparte (otro semestre) para no chocar con el
        UniqueConstraint (registro, dia_semana, hora_inicio) del fixture base.
        """
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20262")
        pronto = timezone.localtime() + datetime.timedelta(minutes=90)
        hora = datetime.time(pronto.hour, 0)
        disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=pronto.weekday(), hora_inicio=hora,
            formato="virtual", liga_virtual="https://meet.example.com/pronto",
        )
        asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=pronto.date(), hora_inicio=hora,
            formato="virtual", liga_virtual="https://meet.example.com/pronto",
        )
        return disponibilidad, asesoria

    def test_la_sesion_esta_dentro_de_la_ventana_y_es_futura(self):
        """Guarda del propio fixture: si esto falla, los dos tests de abajo no
        prueban lo que dicen probar."""
        disponibilidad, asesoria = self._bloque_que_arranca_en_menos_de_dos_horas()

        self.assertEqual(list(disponibilidad.sesiones_futuras()), [asesoria])
        with self.assertRaises(ValidationError):
            asesoria.cancelar(usuario=self.asesor_user)

    def test_desactivar_cancela_aunque_falten_menos_de_dos_horas(self):
        disponibilidad, asesoria = self._bloque_que_arranca_en_menos_de_dos_horas()

        canceladas = disponibilidad.desactivar(
            usuario=self.asesor_user, cancelar_sesiones=True, motivo="Me enfermé.",
        )

        self.assertEqual(canceladas, 1)
        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "cancelada")
        self.assertEqual(asesoria.motivo_cancelacion, "Me enfermé.")
        disponibilidad.refresh_from_db()
        self.assertFalse(disponibilidad.activa)


class ResincronizarSesionesFuturasTests(SesionesFuturasTests):
    """Deuda 0005: corregir un dato del bloque se propaga a las sesiones ya
    agendadas que todavía no ocurren."""

    def test_actualiza_el_snapshot_de_las_sesiones_futuras(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        actualizadas = self.disponibilidad.resincronizar_sesiones_futuras()

        self.assertEqual(actualizadas, [futura])
        futura.refresh_from_db()
        self.assertEqual(futura.liga_virtual, "https://meet.example.com/CORREGIDA")

    def test_propaga_tambien_formato_y_ubicacion(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        self.disponibilidad.formato = "presencial"
        self.disponibilidad.ubicacion = "Salón 25, Yelizcalli"
        self.disponibilidad.liga_virtual = ""
        self.disponibilidad.save()
        self.disponibilidad.resincronizar_sesiones_futuras()

        futura.refresh_from_db()
        self.assertEqual(futura.formato, "presencial")
        self.assertEqual(futura.ubicacion, "Salón 25, Yelizcalli")
        self.assertEqual(futura.liga_virtual, "")

    def test_no_toca_la_hora_de_inicio(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        hora_original = futura.hora_inicio

        self.disponibilidad.hora_inicio = datetime.time(15, 30)
        self.disponibilidad.save()
        self.disponibilidad.resincronizar_sesiones_futuras()

        futura.refresh_from_db()
        self.assertEqual(futura.hora_inicio, hora_original)

    def test_no_toca_sesiones_pasadas_ni_canceladas(self):
        hoy = timezone.localdate()
        pasada = self._crear_asesoria(hoy - datetime.timedelta(days=7))
        cancelada = self._crear_asesoria(
            hoy + datetime.timedelta(days=14), estado="cancelada",
        )

        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        actualizadas = self.disponibilidad.resincronizar_sesiones_futuras()

        self.assertEqual(actualizadas, [])
        pasada.refresh_from_db()
        self.assertEqual(pasada.liga_virtual, "https://meet.example.com/x")
        cancelada.refresh_from_db()
        self.assertEqual(cancelada.liga_virtual, "https://meet.example.com/x")

    @patch("asesorias.tasks.enviar_notificacion_resincronizacion.delay")
    def test_encola_una_notificacion_por_sesion_afectada(self, mock_delay):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        self._crear_asesoria(hoy - datetime.timedelta(days=7))

        self.disponibilidad.liga_virtual = "https://meet.example.com/CORREGIDA"
        self.disponibilidad.save()
        with self.captureOnCommitCallbacks(execute=True):
            self.disponibilidad.resincronizar_sesiones_futuras()

        mock_delay.assert_called_once_with(futura.id)