import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from accounts.tests.factories import crear_alumno
from asesorias.models import Asesoria
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class FlujoCompletoAsesoriaApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        crear_alumno(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        from asesorias.models import PerfilAsesorAcademico
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)

        self.proximo_lunes = self._proximo_dia_semana(0)
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        delta = delta or 7
        return hoy + datetime.timedelta(days=delta)

    def test_flujo_completo_asesor_publica_alumno_agenda_asesor_cierra(self):
        # 1. Asesor busca su catálogo de materias disponibles vía carrera.
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/materias/materias/?carrera={self.carrera.id}")
        self.assertEqual(response.status_code, 200)
        materia_id = response.data[0]["id"]

        # 2. Asesor crea su registro del semestre.
        response = self.client.post("/api/asesorias/registros/", {"semestre": "20271"})
        self.assertEqual(response.status_code, 201)
        registro_id = response.data["id"]

        # 3. Asesor agrega la materia a su pool.
        response = self.client.post(
            f"/api/asesorias/registros/{registro_id}/materias/", {"materia_id": materia_id}
        )
        self.assertEqual(response.status_code, 200)

        # 4. Asesor publica un bloque de disponibilidad.
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": registro_id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 201)
        disponibilidad_id = response.data["id"]

        # 5. Alumno busca disponibilidad para esa materia.
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/disponibilidad/buscar/?materia={materia_id}")
        self.assertEqual(response.status_code, 200)
        resultado = next(r for r in response.data if r["disponibilidad_id"] == disponibilidad_id)

        # 6. Alumno agenda sobre ese resultado.
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": disponibilidad_id, "materia": materia_id, "fecha": resultado["fecha"],
        })
        self.assertEqual(response.status_code, 201)
        asesoria_id = response.data["id"]

        # 7. Un asesor no-dueño no puede marcar asistencia.
        otro_asesor_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_asesor_user, numero_trabajador="99999")
        from asesorias.models import PerfilAsesorAcademico
        PerfilAsesorAcademico.objects.create(user=otro_asesor_user, area=self.area)
        self.client.force_authenticate(user=otro_asesor_user)
        response = self.client.post(f"/api/asesorias/asesorias/{asesoria_id}/marcar_asistencia/", {"asistio": True})
        self.assertEqual(response.status_code, 403)

        # 8. El alumno no puede marcar asistencia.
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(f"/api/asesorias/asesorias/{asesoria_id}/marcar_asistencia/", {"asistio": True})
        self.assertEqual(response.status_code, 403)

        # 9. La sesión ocurre en el pasado (ajuste directo en BD para el test) y el asesor dueño marca asistencia.
        asesoria = Asesoria.objects.get(id=asesoria_id)
        asesoria.fecha = self.lunes_pasado
        asesoria.save()
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(f"/api/asesorias/asesorias/{asesoria_id}/marcar_asistencia/", {"asistio": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "realizada")

        # 10. El asesor guarda notas.
        response = self.client.post(
            f"/api/asesorias/asesorias/{asesoria_id}/notas/", {"texto": "Repasamos series de Taylor."}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["notas"], "Repasamos series de Taylor.")

    def test_alumno_cancela_y_slot_vuelve_a_aparecer_en_busqueda(self):
        from asesorias.models import Disponibilidad, RegistroAsesor
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        registro.agregar_materia(self.materia)
        disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 201)
        asesoria_id = response.data["id"]

        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        ocupado_antes = [
            r for r in response.data
            if r["fecha"] == str(self.proximo_lunes) and r["disponibilidad_id"] == disponibilidad.id
        ]
        self.assertEqual(ocupado_antes, [])

        response = self.client.post(f"/api/asesorias/asesorias/{asesoria_id}/cancelar/", {})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia.id}"
        )
        libre_despues = [
            r for r in response.data
            if r["fecha"] == str(self.proximo_lunes) and r["disponibilidad_id"] == disponibilidad.id
        ]
        self.assertEqual(len(libre_despues), 1)
