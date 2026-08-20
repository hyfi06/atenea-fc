from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from academico.servicios import semestre_vigente
from accounts.demo_data import (
    ALUMNOS_DEMO,
    ASESORES_DEMO,
    ASESORIAS_DEMO,
    EMAIL_ACADEMICO_DEMO_LOGIN,
    EMAIL_ALUMNO_DEMO_LOGIN,
    EMAIL_SAE_DEMO_LOGIN,
    PASSWORD_DEMO,
)
from accounts.models import HistoriaAcademica, PerfilAcademico, PerfilAlumno, PerfilSAE, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Carrera
from materias.models import Materia, OfertaMateria


class SembrarDemoTestsBase(TestCase):
    """Areas y carreras (101 Actuaría, 106 Física, 201 Biología, entre otras)
    ya existen: las siembra la migración 0002_seed_areas_carreras de
    `carreras`, que corre también en la base de datos de tests."""

    def setUp(self):
        semestre = semestre_vigente()
        # Una materia habilitada por área de los asesores activos (Matemáticas,
        # Física); Biología se deja sin materia a propósito, porque su único
        # asesor demo (DEMOTRAB3) queda pendiente y nunca la necesita.
        for clave, carrera_clave in [("9001", 101), ("9002", 106)]:
            carrera = Carrera.objects.get(clave=carrera_clave)
            materia = Materia.objects.create(
                clave=clave, nombre=f"Materia demo {carrera.nombre}", carrera=carrera,
                nivel=1, plan=2020, habilitada_asesorias=True,
            )
            OfertaMateria.objects.create(materia=materia, semestre=semestre, se_imparte=True)


class SembrarDemoTests(SembrarDemoTestsBase):
    def test_crea_los_tres_alumnos_demo_con_historia(self):
        call_command("sembrar_demo", stdout=StringIO())

        self.assertEqual(PerfilAlumno.objects.filter(
            numero_cuenta__in=[a["numero_cuenta"] for a in ALUMNOS_DEMO]).count(), 3)
        perfil = PerfilAlumno.objects.get(numero_cuenta="DEMO0001")
        self.assertEqual(perfil.user.email, "ana.demo@atenea.demo")
        self.assertEqual(perfil.historial.get().carrera.clave, 101)

    def test_crea_dos_asesores_activos_y_uno_pendiente(self):
        call_command("sembrar_demo", stdout=StringIO())

        activos = PerfilAsesorAcademico.objects.filter(
            user__perfil_academico__numero_trabajador__in=["DEMOTRAB1", "DEMOTRAB2"]
        )
        self.assertEqual(activos.count(), 2)
        for asesor in activos:
            self.assertTrue(asesor.activo)
            self.assertEqual(asesor.registros.get().disponibilidades.count(), 2)

        pendiente = PerfilAsesorAcademico.objects.get(
            user__perfil_academico__numero_trabajador="DEMOTRAB3"
        )
        self.assertFalse(pendiente.activo)
        self.assertTrue(pendiente.solicitado_por_el_usuario)
        self.assertEqual(pendiente.registros.count(), 0)

    def test_crea_las_tres_cuentas_fijas_con_password(self):
        call_command("sembrar_demo", stdout=StringIO())

        alumno = User.objects.get(email=EMAIL_ALUMNO_DEMO_LOGIN)
        self.assertTrue(alumno.check_password(PASSWORD_DEMO))
        self.assertTrue(hasattr(alumno, "perfil_alumno"))

        academico = User.objects.get(email=EMAIL_ACADEMICO_DEMO_LOGIN)
        self.assertTrue(academico.check_password(PASSWORD_DEMO))
        self.assertTrue(hasattr(academico, "perfil_academico"))
        self.assertFalse(hasattr(academico, "perfil_asesor_academico"))

        sae = User.objects.get(email=EMAIL_SAE_DEMO_LOGIN)
        self.assertTrue(sae.check_password(PASSWORD_DEMO))
        self.assertTrue(hasattr(sae, "perfil_sae"))

    def test_crea_seis_asesorias_con_la_distribucion_esperada(self):
        call_command("sembrar_demo", stdout=StringIO())

        self.assertEqual(Asesoria.objects.count(), 6)
        self.assertEqual(Asesoria.objects.filter(estado="realizada", asistio=True).count(), 2)
        self.assertEqual(Asesoria.objects.filter(estado="realizada", asistio=False).count(), 2)
        self.assertEqual(Asesoria.objects.filter(estado="cancelada").count(), 2)

        con_notas = Asesoria.objects.exclude(notas="")
        self.assertEqual(con_notas.count(), 1)
        self.assertEqual(con_notas.get().estado, "realizada")
        self.assertTrue(con_notas.get().asistio)

    def test_es_idempotente(self):
        call_command("sembrar_demo", stdout=StringIO())
        call_command("sembrar_demo", stdout=StringIO())

        self.assertEqual(PerfilAlumno.objects.filter(
            numero_cuenta__in=[a["numero_cuenta"] for a in ALUMNOS_DEMO]).count(), 3)
        self.assertEqual(Asesoria.objects.count(), 6)
        self.assertEqual(Disponibilidad.objects.count(), 4)
        self.assertEqual(
            User.objects.filter(email=EMAIL_ALUMNO_DEMO_LOGIN).count(), 1
        )

    def test_falla_si_no_hay_materias_habilitadas_en_un_area(self):
        OfertaMateria.objects.all().delete()
        Materia.objects.all().delete()

        with self.assertRaises(CommandError):
            call_command("sembrar_demo", stdout=StringIO(), stderr=StringIO())
