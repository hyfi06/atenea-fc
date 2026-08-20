from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from academico.servicios import semestre_vigente
from accounts.demo_data import (
    ALUMNOS_DEMO,
    ASESORES_DEMO,
    EMAIL_ACADEMICO_DEMO_LOGIN,
    EMAIL_ALUMNO_DEMO_LOGIN,
    EMAIL_SAE_DEMO_LOGIN,
)
from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria


class LimpiarDemoTests(TestCase):
    def setUp(self):
        semestre = semestre_vigente()
        for clave, carrera_clave in [("9001", 101), ("9002", 106)]:
            carrera = Carrera.objects.get(clave=carrera_clave)
            materia = Materia.objects.create(
                clave=clave, nombre=f"Materia demo {carrera.nombre}", carrera=carrera,
                nivel=1, plan=2020, habilitada_asesorias=True,
            )
            OfertaMateria.objects.create(materia=materia, semestre=semestre, se_imparte=True)

    def test_borra_las_identidades_desechables_por_completo(self):
        call_command("sembrar_demo", stdout=StringIO())
        call_command("limpiar_demo", stdout=StringIO())

        cuentas = [a["numero_cuenta"] for a in ALUMNOS_DEMO]
        numeros = [a["numero_trabajador"] for a in ASESORES_DEMO]
        self.assertEqual(PerfilAlumno.objects.filter(numero_cuenta__in=cuentas).count(), 0)
        self.assertEqual(PerfilAcademico.objects.filter(numero_trabajador__in=numeros).count(), 0)
        self.assertEqual(Asesoria.objects.count(), 0)
        self.assertEqual(RegistroAsesor.objects.count(), 0)
        self.assertEqual(Disponibilidad.objects.count(), 0)

    def test_no_borra_los_users_de_las_cuentas_fijas(self):
        call_command("sembrar_demo", stdout=StringIO())
        call_command("limpiar_demo", stdout=StringIO())

        for email in (EMAIL_ALUMNO_DEMO_LOGIN, EMAIL_ACADEMICO_DEMO_LOGIN, EMAIL_SAE_DEMO_LOGIN):
            self.assertTrue(User.objects.filter(email=email).exists())
        self.assertTrue(hasattr(User.objects.get(email=EMAIL_ALUMNO_DEMO_LOGIN), "perfil_alumno"))
        self.assertTrue(hasattr(User.objects.get(email=EMAIL_ACADEMICO_DEMO_LOGIN), "perfil_academico"))
        self.assertTrue(hasattr(User.objects.get(email=EMAIL_SAE_DEMO_LOGIN), "perfil_sae"))

    def test_borra_asesorias_agendadas_en_vivo_por_el_alumno_fijo(self):
        call_command("sembrar_demo", stdout=StringIO())
        alumno_fijo = PerfilAlumno.objects.get(user__email=EMAIL_ALUMNO_DEMO_LOGIN)
        disponibilidad = Disponibilidad.objects.first()
        materia = disponibilidad.registro.materias.first()
        Asesoria.objects.create(
            alumno=alumno_fijo, disponibilidad=disponibilidad, materia=materia,
            carrera=materia.carrera, fecha=timezone.localdate(),
            hora_inicio=disponibilidad.hora_inicio, formato=disponibilidad.formato,
            liga_virtual=disponibilidad.liga_virtual, estado="agendada",
        )

        call_command("limpiar_demo", stdout=StringIO())

        self.assertEqual(Asesoria.objects.filter(alumno=alumno_fijo).count(), 0)
        # El perfil del alumno fijo se conserva: solo se borró lo agendado en vivo.
        self.assertTrue(PerfilAlumno.objects.filter(user__email=EMAIL_ALUMNO_DEMO_LOGIN).exists())

    def test_revierte_el_alta_de_asesor_hecha_en_vivo_por_el_academico_fijo(self):
        call_command("sembrar_demo", stdout=StringIO())
        academico_fijo = PerfilAcademico.objects.get(user__email=EMAIL_ACADEMICO_DEMO_LOGIN)
        PerfilAsesorAcademico.objects.create(
            user=academico_fijo.user, area=Area.objects.first(), activo=True,
        )

        call_command("limpiar_demo", stdout=StringIO())

        academico_user = User.objects.get(email=EMAIL_ACADEMICO_DEMO_LOGIN)
        self.assertFalse(hasattr(academico_user, "perfil_asesor_academico"))
        self.assertTrue(hasattr(academico_user, "perfil_academico"))

    def test_es_seguro_correr_sin_haber_sembrado_antes(self):
        call_command("limpiar_demo", stdout=StringIO())  # no debe tronar
