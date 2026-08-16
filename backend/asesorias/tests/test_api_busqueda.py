import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.servicios import ventana_agendable
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class BuscarDisponibilidadApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia, _ = Materia.objects.get_or_create(
            clave="1801", defaults={"nombre": "Álgebra", "carrera": self.carrera, "nivel": 1, "plan": 2006,
            "habilitada_asesorias": True}
        )
        OfertaMateria.objects.get_or_create(materia=self.materia, semestre="20271", defaults={"se_imparte": True})

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.registro.agregar_materia(self.materia)
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = crear_alumno(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        self.proximo_lunes = self._proximo_dia_semana(0)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        delta = delta or 7
        return hoy + datetime.timedelta(days=delta)

    def test_alumno_encuentra_disponibilidad_dentro_de_la_ventana(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        self.assertEqual(response.status_code, 200)
        fechas = {r["fecha"] for r in response.data}
        self.assertIn(str(self.proximo_lunes), fechas)

    def test_no_devuelve_fechas_fuera_de_la_ventana(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        _inicio, fin = ventana_agendable()
        for resultado in response.data:
            fecha = datetime.date.fromisoformat(resultado["fecha"])
            self.assertLessEqual(fecha, fin)

    def test_excluye_slot_ya_agendado(self):
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        resultados_ese_lunes = [
            r for r in response.data
            if r["fecha"] == str(self.proximo_lunes) and r["disponibilidad_id"] == self.disponibilidad.id
        ]
        self.assertEqual(resultados_ese_lunes, [])

    def test_filtra_por_materia_sin_coincidencia(self):
        otra_materia = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={otra_materia.id}"
        )
        self.assertEqual(response.data, [])

    def test_asesor_no_puede_usar_la_busqueda(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/disponibilidad/buscar/")
        self.assertEqual(response.status_code, 403)

    def test_incluye_identidad_del_asesor(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        self.assertTrue(response.data)
        primero = response.data[0]
        self.assertEqual(primero["registro_id"], self.registro.id)
        self.assertEqual(primero["asesor_nombre"], self.asesor_user.nombre_completo)

    def test_filtra_por_asesor(self):
        otro_user = User.objects.create_user(email="asesor2@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_user, numero_trabajador="99999")
        otro_asesor = PerfilAsesorAcademico.objects.create(user=otro_user, area=self.area)
        otro_registro = RegistroAsesor.objects.create(asesor=otro_asesor, semestre="20271")
        otro_registro.agregar_materia(self.materia)
        Disponibilidad.objects.create(
            registro=otro_registro, dia_semana=0, hora_inicio=datetime.time(12, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )

        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}&asesor={self.registro.id}"
        )
        registros = {r["registro_id"] for r in response.data}
        self.assertEqual(registros, {self.registro.id})

    def test_miembro_sae_puede_usar_la_busqueda(self):
        from accounts.models import PerfilSAE

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        self.client.force_authenticate(user=sae_user)
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)

    def test_miembro_sae_no_puede_agendar(self):
        from accounts.models import PerfilSAE

        sae_user = User.objects.create_user(email="sae2@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        self.client.force_authenticate(user=sae_user)
        response = self.client.post(
            "/api/asesorias/asesorias/",
            {
                "disponibilidad": self.disponibilidad.id,
                "materia": self.materia.id,
                "fecha": str(self.proximo_lunes),
            },
        )
        self.assertEqual(response.status_code, 403)
