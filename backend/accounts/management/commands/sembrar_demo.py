from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

import datetime

from academico.servicios import semestre_vigente
from accounts.demo_data import (
    ALUMNOS_DEMO,
    ASESORES_DEMO,
    ASESORIAS_DEMO,
    CARRERA_CLAVE_ALUMNO_FIJO,
    EMAIL_ACADEMICO_DEMO_LOGIN,
    EMAIL_ALUMNO_DEMO_LOGIN,
    EMAIL_SAE_DEMO_LOGIN,
    NUMERO_CUENTA_ALUMNO_FIJO,
    NUMERO_TRABAJADOR_ACADEMICO_FIJO,
    PASSWORD_DEMO,
)
from accounts.models import HistoriaAcademica, PerfilAcademico, PerfilAlumno, PerfilSAE, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia


class Command(BaseCommand):
    help = (
        "Siembra alumnos, asesores, asesorías y 3 cuentas de login fijas de muestra "
        "en staging, para hacer una demostración. Idempotente: seguro de volver a "
        "correr. Ver también limpiar_demo."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        semestre = semestre_vigente()

        alumnos = {a["numero_cuenta"]: self._crear_alumno(a) for a in ALUMNOS_DEMO}
        asesores = {a["numero_trabajador"]: self._crear_asesor(a, semestre) for a in ASESORES_DEMO}
        self._crear_cuentas_fijas()

        creadas = actualizadas = 0
        for fila in ASESORIAS_DEMO:
            alumno = alumnos[fila["alumno"]]
            info_asesor = asesores[fila["asesor"]]
            disponibilidad = info_asesor["disponibilidades"][fila["disponibilidad"]]
            _, creada = self._crear_asesoria(fila, alumno, disponibilidad, info_asesor["materia"])
            if creada:
                creadas += 1
            else:
                actualizadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"Demo sembrada: {len(alumnos)} alumnos, {len(asesores)} asesores, "
            f"3 cuentas fijas, asesorías: {creadas} creadas / {actualizadas} actualizadas."
        ))

    def _crear_alumno(self, datos):
        try:
            carrera = Carrera.objects.get(clave=datos["carrera_clave"])
        except Carrera.DoesNotExist as exc:
            raise CommandError(
                f"No existe la carrera clave={datos['carrera_clave']}. "
                "¿Corrieron las migraciones de carreras?"
            ) from exc

        perfil = PerfilAlumno.objects.select_related("user").filter(
            numero_cuenta=datos["numero_cuenta"]
        ).first()
        if perfil is None:
            user = User.objects.create_user(email=datos["email"], password=None)
            perfil = PerfilAlumno.objects.create(user=user, numero_cuenta=datos["numero_cuenta"])
        else:
            user = perfil.user

        user.first_name = datos["nombre"]
        user.apellido1 = datos["ap1"]
        user.apellido2 = datos["ap2"]
        user.email = datos["email"]
        user.save()

        HistoriaAcademica.objects.update_or_create(
            perfil_alumno=perfil, carrera=carrera, defaults={"generacion": datos["generacion"]},
        )
        return perfil

    def _crear_asesor(self, datos, semestre):
        area = Area.objects.filter(nombre=datos["area"]).first()
        if area is None:
            raise CommandError(
                f"No existe el área '{datos['area']}'. ¿Corrieron las migraciones de carreras?"
            )

        academico = PerfilAcademico.objects.select_related("user").filter(
            numero_trabajador=datos["numero_trabajador"]
        ).first()
        if academico is None:
            user = User.objects.create_user(email=datos["email"], password=None)
            academico = PerfilAcademico.objects.create(
                user=user, numero_trabajador=datos["numero_trabajador"]
            )
        else:
            user = academico.user

        user.first_name = datos["nombre"]
        user.apellido1 = datos["ap1"]
        user.apellido2 = datos["ap2"]
        user.email = datos["email"]
        user.save()

        asesor, _ = PerfilAsesorAcademico.objects.update_or_create(
            user=user,
            defaults={
                "area": area,
                "activo": datos["activo"],
                "solicitado_por_el_usuario": datos["pendiente"],
            },
        )

        materia = None
        disponibilidades = []
        if datos["activo"]:
            materia = Materia.objects.filter(
                carrera__area=area, habilitada_asesorias=True,
                ofertas__semestre=semestre, ofertas__se_imparte=True,
            ).distinct().first()
            if materia is None:
                raise CommandError(
                    f"No hay materias habilitadas para asesorías en el área "
                    f"'{area.nombre}' con oferta en el semestre {semestre}. "
                    "Corran cargar_materias y cargar_oferta antes de sembrar la demo."
                )
            registro, _ = RegistroAsesor.objects.update_or_create(asesor=asesor, semestre=semestre)
            registro.materias.set([materia])
            for bloque in datos["disponibilidades"]:
                disponibilidad, _ = Disponibilidad.objects.update_or_create(
                    registro=registro, dia_semana=bloque["dia_semana"],
                    hora_inicio=bloque["hora_inicio"],
                    defaults={
                        "formato": bloque["formato"],
                        "ubicacion": bloque.get("ubicacion", ""),
                        "liga_virtual": bloque.get("liga_virtual", ""),
                        "activa": True,
                    },
                )
                disponibilidades.append(disponibilidad)

        return {"asesor": asesor, "materia": materia, "disponibilidades": disponibilidades}

    def _crear_cuentas_fijas(self):
        alumno_user, _ = User.objects.get_or_create(
            email=EMAIL_ALUMNO_DEMO_LOGIN, defaults={"first_name": "Alumno", "apellido1": "Demo"},
        )
        alumno_user.set_password(PASSWORD_DEMO)
        alumno_user.save()
        perfil, _ = PerfilAlumno.objects.get_or_create(
            user=alumno_user, defaults={"numero_cuenta": NUMERO_CUENTA_ALUMNO_FIJO},
        )
        carrera = Carrera.objects.get(clave=CARRERA_CLAVE_ALUMNO_FIJO)
        HistoriaAcademica.objects.update_or_create(
            perfil_alumno=perfil, carrera=carrera, defaults={"generacion": 2023},
        )

        academico_user, _ = User.objects.get_or_create(
            email=EMAIL_ACADEMICO_DEMO_LOGIN, defaults={"first_name": "Académico", "apellido1": "Demo"},
        )
        academico_user.set_password(PASSWORD_DEMO)
        academico_user.save()
        # Sin PerfilAsesorAcademico a propósito: esta cuenta hace el flujo de
        # alta de asesor en vivo durante la demo.
        PerfilAcademico.objects.get_or_create(
            user=academico_user, defaults={"numero_trabajador": NUMERO_TRABAJADOR_ACADEMICO_FIJO},
        )

        sae_user, _ = User.objects.get_or_create(
            email=EMAIL_SAE_DEMO_LOGIN, defaults={"first_name": "SAE", "apellido1": "Demo"},
        )
        sae_user.set_password(PASSWORD_DEMO)
        sae_user.save()
        PerfilSAE.objects.get_or_create(user=sae_user, defaults={"activo": True})

    def _crear_asesoria(self, fila, alumno, disponibilidad, materia):
        fecha = self._fecha_pasada(disponibilidad.dia_semana, fila["semanas_atras"])
        defaults = {
            "materia": materia,
            "carrera": materia.carrera,
            "hora_inicio": disponibilidad.hora_inicio,
            "formato": disponibilidad.formato,
            "ubicacion": disponibilidad.ubicacion,
            "liga_virtual": disponibilidad.liga_virtual,
            "fecha": fecha,
            "estado": fila["estado"],
            "asistio": fila.get("asistio"),
            "notas": fila.get("notas", ""),
            "motivo_cancelacion": fila.get("motivo_cancelacion", ""),
            "cancelado_por": alumno.user if fila["estado"] == "cancelada" else None,
        }
        return Asesoria.objects.update_or_create(
            disponibilidad=disponibilidad, alumno=alumno, defaults=defaults,
        )

    @staticmethod
    def _fecha_pasada(dia_semana: int, semanas_atras: int) -> datetime.date:
        """Última ocurrencia de `dia_semana` hace `semanas_atras` semanas.

        Se recalcula contra "hoy" en cada corrida — así una siembra repetida
        semanas después sigue viéndose reciente en vez de arrastrar fechas
        cada vez más viejas.
        """
        hoy = timezone.localdate()
        lunes_de_esta_semana = hoy - datetime.timedelta(days=hoy.weekday())
        lunes_objetivo = lunes_de_esta_semana - datetime.timedelta(weeks=semanas_atras)
        return lunes_objetivo + datetime.timedelta(days=dia_semana)
