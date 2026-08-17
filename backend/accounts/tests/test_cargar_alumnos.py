import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase

from accounts.models import HistoriaAcademica, PerfilAlumno, User
from carreras.models import Area, Carrera

ENCABEZADO = "cuenta,ap1,ap2,nombre,carrera_id,curp,correo,gen"


def escribir_csv(*filas):
    ruta = Path(tempfile.mkdtemp()) / "alumnos.csv"
    ruta.write_text("\n".join([ENCABEZADO, *filas]) + "\n", encoding="utf-8")
    return str(ruta)


class CargarAlumnosTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area carga")
        self.carrera = Carrera.objects.create(clave=931, nombre="Actuaría Carga", area=self.area)
        self.otra = Carrera.objects.create(clave=932, nombre="Matemáticas Carga", area=self.area)

    def test_crea_user_perfil_e_historia(self):
        ruta = escribir_csv(
            "312000100,López,Ruiz,Ana,931,LORA000101MDFXXX01,ana@ciencias.unam.mx,2023"
        )
        call_command("cargar_alumnos", ruta, stdout=StringIO())

        perfil = PerfilAlumno.objects.get(numero_cuenta="312000100")
        self.assertEqual(perfil.user.email, "ana@ciencias.unam.mx")
        self.assertEqual(perfil.user.apellido1, "López")
        self.assertEqual(perfil.user.curp, "LORA000101MDFXXX01")
        self.assertEqual(perfil.correos_alternos, [])
        self.assertEqual(perfil.historial.get().carrera, self.carrera)
        self.assertEqual(perfil.historial.get().generacion, 2023)

    def test_es_idempotente(self):
        fila = "312000101,Sosa,Paz,Bea,931,,bea@ciencias.unam.mx,2023"
        ruta = escribir_csv(fila)
        call_command("cargar_alumnos", ruta, stdout=StringIO())
        call_command("cargar_alumnos", ruta, stdout=StringIO())

        self.assertEqual(User.objects.filter(email="bea@ciencias.unam.mx").count(), 1)
        self.assertEqual(HistoriaAcademica.objects.filter(
            perfil_alumno__numero_cuenta="312000101").count(), 1)

    def test_dos_filas_con_la_misma_cuenta_dan_dos_carreras(self):
        ruta = escribir_csv(
            "312000102,Mora,Vega,Cin,931,,cin@ciencias.unam.mx,2022",
            "312000102,Mora,Vega,Cin,932,,cin@ciencias.unam.mx,2025",
        )
        call_command("cargar_alumnos", ruta, stdout=StringIO())

        perfil = PerfilAlumno.objects.get(numero_cuenta="312000102")
        self.assertEqual(perfil.historial.count(), 2)

    def test_cuenta_existente_con_correo_distinto_lo_guarda_como_alterno(self):
        fila = "312000103,Paz,Sol,Dan,931,,dan@ciencias.unam.mx,2023"
        ruta = escribir_csv(fila)
        call_command("cargar_alumnos", ruta, stdout=StringIO())

        # Reaparece con un correo distinto: no se pisa el de login.
        ruta2 = escribir_csv("312000103,Paz,Sol,Dan,931,,dan.nuevo@ciencias.unam.mx,2023")
        call_command("cargar_alumnos", ruta2, stdout=StringIO())
        call_command("cargar_alumnos", ruta2, stdout=StringIO())  # no duplica

        perfil = PerfilAlumno.objects.get(numero_cuenta="312000103")
        self.assertEqual(perfil.user.email, "dan@ciencias.unam.mx")
        self.assertEqual(perfil.correos_alternos, ["dan.nuevo@ciencias.unam.mx"])

    def test_una_fila_mala_no_aborta_las_buenas(self):
        ruta = escribir_csv(
            "312000104,Ruiz,Paz,Eva,9999,,eva@ciencias.unam.mx,2023",
            "312000105,Sosa,Luz,Fer,931,,fer@ciencias.unam.mx,2023",
        )
        with self.assertRaises(CommandError):
            call_command("cargar_alumnos", ruta, stdout=StringIO(), stderr=StringIO())

        self.assertTrue(PerfilAlumno.objects.filter(numero_cuenta="312000105").exists())
        self.assertFalse(PerfilAlumno.objects.filter(numero_cuenta="312000104").exists())

    def test_encabezado_invalido_falla_de_inmediato(self):
        ruta = Path(tempfile.mkdtemp()) / "malo.csv"
        ruta.write_text("cuenta,correo\n1,a@b.com\n", encoding="utf-8")
        with self.assertRaises(CommandError):
            call_command("cargar_alumnos", str(ruta), stdout=StringIO(), stderr=StringIO())

    def test_archivo_inexistente_falla(self):
        with self.assertRaises(CommandError):
            call_command("cargar_alumnos", "/no/existe.csv", stdout=StringIO(), stderr=StringIO())
