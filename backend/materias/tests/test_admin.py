from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from carreras.models import Area, Carrera
from materias.models import Materia


class MateriaAdminAccionesHabilitarAsesoriasTests(TestCase):
    def setUp(self):
        area = Area.objects.create(nombre="Área de Prueba Admin")
        self.carrera = Carrera.objects.create(clave=992, nombre="Carrera de Prueba Admin", area=area)
        self.materia_a = Materia.objects.create(
            clave="9001", nombre="Materia A", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=False,
        )
        self.materia_b = Materia.objects.create(
            clave="9002", nombre="Materia B", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=False,
        )
        self.materia_c = Materia.objects.create(
            clave="9003", nombre="Materia C", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        self.superuser = User.objects.create_superuser(
            email="admin-materias@ciencias.unam.mx", password="x",
        )
        self.client.force_login(self.superuser)
        self.changelist_url = reverse("admin:materias_materia_changelist")

    def test_accion_habilitar_asesorias_actualiza_seleccionadas(self):
        self.client.post(self.changelist_url, {
            "action": "habilitar_asesorias",
            "_selected_action": [self.materia_a.pk, self.materia_b.pk],
        })
        self.materia_a.refresh_from_db()
        self.materia_b.refresh_from_db()
        self.assertTrue(self.materia_a.habilitada_asesorias)
        self.assertTrue(self.materia_b.habilitada_asesorias)

    def test_accion_habilitar_asesorias_no_toca_no_seleccionadas(self):
        self.client.post(self.changelist_url, {
            "action": "habilitar_asesorias",
            "_selected_action": [self.materia_a.pk],
        })
        self.materia_b.refresh_from_db()
        self.assertFalse(self.materia_b.habilitada_asesorias)

    def test_accion_deshabilitar_asesorias_actualiza_seleccionadas(self):
        self.client.post(self.changelist_url, {
            "action": "deshabilitar_asesorias",
            "_selected_action": [self.materia_c.pk],
        })
        self.materia_c.refresh_from_db()
        self.assertFalse(self.materia_c.habilitada_asesorias)
