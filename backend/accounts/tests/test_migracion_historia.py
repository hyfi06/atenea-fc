from django.test import TestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection


class MigrarCarreraAHistoriaTests(TestCase):
    """La migración 0006 copia la carrera denormalizada al historial.

    Se prueba con el estado histórico de los modelos (`apps.get_model` de la
    migración), no con los modelos actuales: para cuando esto corra en CI,
    `PerfilAlumno.carrera` ya no existirá en `models.py`.
    """

    migrate_from = ("accounts", "0005_historiaacademica")
    migrate_to = ("accounts", "0006_migrar_carrera_a_historia")

    def test_copia_la_carrera_denormalizada_al_historial(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        executor.loader.build_graph()
        estado_viejo = executor.loader.project_state([self.migrate_from]).apps

        Area = estado_viejo.get_model("carreras", "Area")
        Carrera = estado_viejo.get_model("carreras", "Carrera")
        User = estado_viejo.get_model("accounts", "User")
        PerfilAlumno = estado_viejo.get_model("accounts", "PerfilAlumno")

        area = Area.objects.create(nombre="Area migracion")
        carrera = Carrera.objects.create(clave=981, nombre="Carrera Migracion", area=area)
        user = User.objects.create(email="migrado@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=user, numero_cuenta="312000099", carrera=carrera, generacion=2022
        )

        executor.loader.build_graph()
        executor.migrate([self.migrate_to])
        estado_nuevo = executor.loader.project_state([self.migrate_to]).apps

        HistoriaAcademica = estado_nuevo.get_model("accounts", "HistoriaAcademica")
        historia = HistoriaAcademica.objects.get(perfil_alumno__numero_cuenta="312000099")
        self.assertEqual(historia.generacion, 2022)
        self.assertEqual(historia.carrera.nombre, "Carrera Migracion")
