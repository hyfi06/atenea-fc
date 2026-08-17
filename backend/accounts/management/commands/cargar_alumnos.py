import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import DataError, IntegrityError, transaction

from accounts.models import HistoriaAcademica, PerfilAlumno, User
from carreras.models import Carrera

COLUMNAS_REQUERIDAS = {"cuenta", "ap1", "ap2", "nombre", "carrera_id", "curp", "correo", "gen"}


class Command(BaseCommand):
    help = (
        "Carga o actualiza alumnos desde un CSV (columnas: "
        "cuenta,ap1,ap2,nombre,carrera_id,curp,correo,gen). "
        "Upsert por número de cuenta; una fila por carrera."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        creados = 0
        actualizados = 0
        errores = 0

        try:
            archivo = open(options["csv_path"], newline="", encoding="utf-8")
        except (FileNotFoundError, OSError) as exc:
            raise CommandError(f"No se pudo abrir el archivo '{options['csv_path']}': {exc}")

        with archivo:
            lector = csv.DictReader(archivo)
            faltantes = COLUMNAS_REQUERIDAS - set(lector.fieldnames or [])
            if faltantes:
                raise CommandError(
                    f"Encabezado del CSV inválido: faltan las columnas {sorted(faltantes)}"
                )

            for numero_fila, fila in enumerate(lector, start=2):
                try:
                    carrera = Carrera.objects.get(clave=int(fila["carrera_id"].strip()))
                except Carrera.DoesNotExist as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                try:
                    # Una transacción por fila: una fila mala se descarta entera
                    # sin dejar a medias el User que ya se había creado, y sin
                    # abortar las filas buenas (mismo criterio que cargar_materias).
                    with transaction.atomic():
                        creado = self._cargar_fila(fila, carrera)
                except (ValueError, KeyError, TypeError, AttributeError, DataError, IntegrityError) as exc:
                    errores += 1
                    self.stderr.write(f"Fila {numero_fila}: {exc}")
                    continue

                if creado:
                    creados += 1
                else:
                    actualizados += 1

        resumen = f"Alumnos: {creados} creados, {actualizados} actualizados, {errores} filas con error"
        if errores:
            raise CommandError(resumen)
        self.stdout.write(self.style.SUCCESS(resumen))

    def _cargar_fila(self, fila, carrera) -> bool:
        """Escribe una fila del CSV en User + PerfilAlumno + HistoriaAcademica.

        Devuelve True si el alumno se creó, False si ya existía y se actualizó.
        """
        cuenta = fila["cuenta"].strip()
        correo = fila["correo"].strip().lower()
        curp = fila["curp"].strip().upper() or None

        perfil = PerfilAlumno.objects.select_related("user").filter(numero_cuenta=cuenta).first()

        if perfil is None:
            # Alumno nuevo: el correo de la fila es el de login.
            user = User.objects.create(
                email=correo,
                first_name=fila["nombre"].strip(),
                apellido1=fila["ap1"].strip(),
                apellido2=fila["ap2"].strip(),
                curp=curp,
            )
            perfil = PerfilAlumno.objects.create(user=user, numero_cuenta=cuenta)
            creado = True
        else:
            user = perfil.user
            user.first_name = fila["nombre"].strip()
            user.apellido1 = fila["ap1"].strip()
            user.apellido2 = fila["ap2"].strip()
            if curp:
                user.curp = curp
            if correo != user.email and correo not in perfil.correos_alternos:
                # La cuenta ya existe con otro correo: no se pisa el correo de
                # login (Task 17 respuesta de Héctor) — se guarda como alterno.
                perfil.correos_alternos = [*perfil.correos_alternos, correo]
                perfil.save(update_fields=["correos_alternos"])
            user.save()
            creado = False

        generacion_texto = fila["gen"].strip()
        HistoriaAcademica.objects.update_or_create(
            perfil_alumno=perfil,
            carrera=carrera,
            defaults={"generacion": int(generacion_texto)},
        )
        return creado
