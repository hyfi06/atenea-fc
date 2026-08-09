# API del lado alumno de Asesorías — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar los huecos de la API DRF para que el frontend del alumno pueda elegir materia → asesor → día → bloque → carrera → agendar, y dejar de filtrar las notas del asesor al alumno.

**Architecture:** Todo se resuelve en `asesorias/views.py`, `asesorias/serializers.py` y `asesorias/urls.py` — sin migraciones ni modelos nuevos. Dos `APIView` de sólo lectura nuevas (`oferta/`, `oferta/{materia_id}/asesores/`), una extensión de `BuscarDisponibilidadView` (`?asesor=` + identidad), `carrera` escribible en `AsesoriaSerializer` y ocultamiento de `notas` vía `to_representation`.

**Tech Stack:** Django + Django REST Framework. Tests con `rest_framework.test.APITestCase` + `force_authenticate`.

**Spec:** [`2026-08-08-asesorias-alumno-api-design.md`](../specs/2026-08-08-asesorias-alumno-api-design.md) · **ADR:** [0021](../../decisions/0021-asesorias-alumno-api.md)

## Global Constraints

- **Sin migraciones ni cambios de modelo.** Ningún `models.py` se toca; ninguna task genera una migración.
- **Reusar, no duplicar:** `EsAlumno` (`asesorias/permissions.py:4`), `ventana_agendable()` (`asesorias/servicios.py:6`), el patrón `APIView` de `BuscarDisponibilidadView` (`asesorias/views.py:96`), el `AsesoriaViewSet` compartido y su `409` por doble-booking (`views.py:193-201`).
- **Filtrado manual por query param**, comparación en Python — el proyecto no usa `django-filter` (igual que el filtro `?semestre=` en `views.py:187-190`).
- **`nombre_completo`** es la propiedad de `accounts.User` usada en todo el módulo para el nombre a mostrar (ver `SesionFuturaSerializer`, `serializers.py:79`).
- **Deuda referenciada, no nueva:** carrera múltiple → [0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md); paginación → [0006](../../technical-debt/0006-sin-paginacion-listados.md); calendario → [0001](../../technical-debt/0001-sin-modelo-calendario-academico.md). Esta entrega no crea deuda; el leak de `notas` se corrige aquí.
- **Comando de tests:** desde `backend/`, `python manage.py test asesorias.tests.<módulo> -v 2` (o el equivalente en docker: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test asesorias.tests.<módulo> -v 2`).
- **Commits:** formato `[type][scope] resumen`, atómicos, con `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>` (ver `docs/development/commit-conventions.md`).

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `backend/asesorias/views.py` | Endpoints de oferta y búsqueda | Modificar: `BuscarDisponibilidadView`; añadir `OfertaView`, `AsesoresDeMateriaView` |
| `backend/asesorias/serializers.py` | Formas de respuesta y validación | Modificar: `ResultadoBusquedaSerializer`, `AsesoriaSerializer` |
| `backend/asesorias/urls.py` | Ruteo | Añadir dos `path()` antes de `router.urls` |
| `backend/asesorias/tests/test_api_oferta.py` | Tests de oferta y asesores-por-materia | Crear |
| `backend/asesorias/tests/test_api_busqueda.py` | Tests de `?asesor=` + identidad | Modificar (añadir casos) |
| `backend/asesorias/tests/test_api_asesoria.py` | Tests de carrera escribible y notas ocultas | Modificar (añadir casos) |

---

## Task 1: Oferta de materias — `GET /api/asesorias/oferta/`

**Files:**
- Modify: `backend/asesorias/views.py` (nueva clase `OfertaView`)
- Modify: `backend/asesorias/urls.py` (nuevo `path`)
- Test: `backend/asesorias/tests/test_api_oferta.py` (crear)

**Interfaces:**
- Consumes: `EsAlumno`, `Materia` (`materias.models`), M2M related names `Materia.registros_asesor` (de `RegistroAsesor.materias`) y `RegistroAsesor.disponibilidades` (de `Disponibilidad.registro`).
- Produces: `GET /api/asesorias/oferta/?carrera=&buscar=` → `200` con `[{"materia_id": int, "nombre": str, "carrera_id": int, "num_asesores": int}]`. Sólo materias con ≥1 asesor con `Disponibilidad.activa`. `403` si el solicitante no es alumno.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/asesorias/tests/test_api_oferta.py`:

```python
import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class OfertaApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.otra_carrera = Carrera.objects.create(clave=200, nombre="Física", area=self.area)

        self.materia_con_asesor = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_sin_asesor = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.get_or_create(
            materia=self.materia_con_asesor, semestre="20271", defaults={"se_imparte": True}
        )

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.registro.materias.add(self.materia_con_asesor)
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

    def test_oferta_solo_materias_con_asesor_disponible(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.status_code, 200)
        ids = {m["materia_id"] for m in response.data}
        self.assertIn(self.materia_con_asesor.id, ids)
        self.assertNotIn(self.materia_sin_asesor.id, ids)

    def test_oferta_incluye_num_asesores_y_carrera(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/")
        fila = next(m for m in response.data if m["materia_id"] == self.materia_con_asesor.id)
        self.assertEqual(fila["num_asesores"], 1)
        self.assertEqual(fila["carrera_id"], self.carrera.id)
        self.assertEqual(fila["nombre"], "Álgebra")

    def test_materia_con_disponibilidad_inactiva_no_aparece(self):
        Disponibilidad.objects.filter(registro=self.registro).update(activa=False)
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.data, [])

    def test_filtra_por_carrera(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/oferta/?carrera={self.otra_carrera.id}")
        self.assertEqual(response.data, [])

    def test_filtra_por_busqueda_de_nombre(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/?buscar=álge")
        ids = {m["materia_id"] for m in response.data}
        self.assertEqual(ids, {self.materia_con_asesor.id})

    def test_no_alumno_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_oferta -v 2`
Expected: FAIL — `404`/`Resolver404` porque la ruta `oferta/` aún no existe.

- [ ] **Step 3: Implementar `OfertaView`**

En `backend/asesorias/views.py`, añadir el import de `Count` y de `Materia`, y la clase (colócala junto a `BuscarDisponibilidadView`):

```python
from django.db.models import Count, Q  # Q ya está importado; añade Count
from materias.models import Materia


class OfertaView(APIView):
    permission_classes = [EsAlumno]

    def get(self, request):
        carrera_id = request.query_params.get("carrera")
        buscar = request.query_params.get("buscar")

        materias = (
            Materia.objects.filter(registros_asesor__disponibilidades__activa=True)
            .annotate(num_asesores=Count("registros_asesor__asesor", distinct=True))
            .distinct()
        )
        if carrera_id:
            materias = materias.filter(carrera_id=carrera_id)
        if buscar:
            materias = materias.filter(nombre__icontains=buscar)

        data = [
            {
                "materia_id": m.id,
                "nombre": m.nombre,
                "carrera_id": m.carrera_id,
                "num_asesores": m.num_asesores,
            }
            for m in materias
        ]
        return Response(data)
```

- [ ] **Step 4: Registrar la ruta**

En `backend/asesorias/urls.py`, importar `OfertaView` y añadir el `path` dentro de `urlpatterns`, antes de `router.urls`:

```python
from .views import (
    AsesoriaViewSet, BuscarDisponibilidadView, DisponibilidadViewSet, OfertaView, RegistroAsesorViewSet,
)

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
    path("oferta/", OfertaView.as_view(), name="oferta"),
] + router.urls
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_oferta -v 2`
Expected: PASS (6 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_oferta.py
git commit -m "[feat][asesorias] endpoint de oferta de materias con asesores disponibles

- GET /api/asesorias/oferta/?carrera=&buscar= (EsAlumno)
- deriva de Disponibilidad.activa; num_asesores por materia

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Asesores por materia — `GET /api/asesorias/oferta/{materia_id}/asesores/`

**Files:**
- Modify: `backend/asesorias/views.py` (nueva clase `AsesoresDeMateriaView`)
- Modify: `backend/asesorias/urls.py` (nuevo `path`)
- Test: `backend/asesorias/tests/test_api_oferta.py` (añadir clase de test)

**Interfaces:**
- Consumes: `EsAlumno`, `Materia`, `RegistroAsesor`, related names `RegistroAsesor.disponibilidades` y `PerfilAsesorAcademico.area` (`carreras.Area`, campo `nombre`).
- Produces: `GET /api/asesorias/oferta/{materia_id}/asesores/` → `200` con `[{"registro_id": int, "asesor_nombre": str, "area_nombre": str, "formatos": [str]}]` ordenado por `registro_id`; `[]` si la materia no tiene asesores; `404` si `materia_id` no existe; `403` si no es alumno.

- [ ] **Step 1: Escribir el test que falla**

Añadir al final de `backend/asesorias/tests/test_api_oferta.py`:

```python
from django.shortcuts import get_object_or_404  # no requerido en el test; ver implementación


class AsesoresDeMateriaApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_sin_asesores = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.registro.materias.add(self.materia)
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=1, hora_inicio=datetime.time(11, 0),
            formato="presencial", ubicacion="Salón 4",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

    def test_lista_asesores_con_identidad_y_formatos(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia.id}/asesores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        fila = response.data[0]
        self.assertEqual(fila["registro_id"], self.registro.id)
        self.assertEqual(fila["asesor_nombre"], self.asesor_user.nombre_completo)
        self.assertEqual(fila["area_nombre"], "Matemáticas")
        self.assertEqual(sorted(fila["formatos"]), ["presencial", "virtual"])

    def test_materia_sin_asesores_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia_sin_asesores.id}/asesores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_materia_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/oferta/999999/asesores/")
        self.assertEqual(response.status_code, 404)

    def test_no_alumno_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia.id}/asesores/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_oferta.AsesoresDeMateriaApiTests -v 2`
Expected: FAIL — la ruta `oferta/{id}/asesores/` no existe todavía.

- [ ] **Step 3: Implementar `AsesoresDeMateriaView`**

En `backend/asesorias/views.py`, añadir el import y la clase:

```python
from django.shortcuts import get_object_or_404


class AsesoresDeMateriaView(APIView):
    permission_classes = [EsAlumno]

    def get(self, request, materia_id):
        materia = get_object_or_404(Materia, pk=materia_id)
        registros = (
            RegistroAsesor.objects.filter(materias=materia, disponibilidades__activa=True)
            .select_related("asesor__user", "asesor__area")
            .distinct()
            .order_by("id")
        )
        data = []
        for registro in registros:
            formatos = sorted(
                set(registro.disponibilidades.filter(activa=True).values_list("formato", flat=True))
            )
            data.append({
                "registro_id": registro.id,
                "asesor_nombre": registro.asesor.user.nombre_completo,
                "area_nombre": registro.asesor.area.nombre,
                "formatos": formatos,
            })
        return Response(data)
```

Añadir `RegistroAsesor` al import existente de `.models` en `views.py` si no está (hoy importa `Asesoria, Disponibilidad, RegistroAsesor` — ya está).

- [ ] **Step 4: Registrar la ruta**

En `backend/asesorias/urls.py`, importar `AsesoresDeMateriaView` y añadir el `path`:

```python
from .views import (
    AsesoresDeMateriaView, AsesoriaViewSet, BuscarDisponibilidadView, DisponibilidadViewSet,
    OfertaView, RegistroAsesorViewSet,
)

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
    path("oferta/", OfertaView.as_view(), name="oferta"),
    path("oferta/<int:materia_id>/asesores/", AsesoresDeMateriaView.as_view(), name="oferta-asesores"),
] + router.urls
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_oferta -v 2`
Expected: PASS (10 tests: 6 de Task 1 + 4 nuevos).

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_oferta.py
git commit -m "[feat][asesorias] endpoint de asesores disponibles por materia

- GET /api/asesorias/oferta/{materia_id}/asesores/ (EsAlumno)
- registro_id, asesor_nombre, area_nombre, formatos; 404 si materia no existe

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Disponibilidad por asesor — `GET /disponibilidad/buscar/?asesor=` + identidad

**Files:**
- Modify: `backend/asesorias/views.py` (`BuscarDisponibilidadView.get`)
- Modify: `backend/asesorias/serializers.py` (`ResultadoBusquedaSerializer`)
- Test: `backend/asesorias/tests/test_api_busqueda.py` (añadir casos)

**Interfaces:**
- Consumes: `ventana_agendable()`, la lógica de exclusión de ocupados ya existente.
- Produces: `GET /api/asesorias/disponibilidad/buscar/?materia=&asesor=<registro_id>` filtra por `registro_id` y cada resultado gana `registro_id` y `asesor_nombre`. La ventana y la exclusión de ocupados no cambian (regresión de ADR 0017).

- [ ] **Step 1: Escribir el test que falla**

Añadir estos métodos a la clase `BuscarDisponibilidadApiTests` en `backend/asesorias/tests/test_api_busqueda.py`:

```python
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
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_busqueda -v 2`
Expected: FAIL — `KeyError`/`assertEqual` porque `registro_id`/`asesor_nombre` no vienen y `?asesor=` no filtra.

- [ ] **Step 3: Extender `ResultadoBusquedaSerializer`**

En `backend/asesorias/serializers.py`, añadir los dos campos al principio de `ResultadoBusquedaSerializer`:

```python
class ResultadoBusquedaSerializer(serializers.Serializer):
    registro_id = serializers.IntegerField()
    asesor_nombre = serializers.CharField()
    disponibilidad_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()
    formato = serializers.CharField()
    ubicacion = serializers.CharField(allow_blank=True)
    liga_virtual = serializers.CharField(allow_blank=True)
```

- [ ] **Step 4: Extender `BuscarDisponibilidadView.get`**

En `backend/asesorias/views.py`, dentro de `BuscarDisponibilidadView.get`: leer el nuevo query param, ampliar el `select_related` y filtrar; luego añadir los dos campos al dict de resultados.

```python
        materia_id = request.query_params.get("materia")
        carrera_id = request.query_params.get("carrera")
        formato = request.query_params.get("formato")
        asesor_registro_id = request.query_params.get("asesor")

        disponibilidades = Disponibilidad.objects.filter(activa=True).select_related(
            "registro__asesor__user"
        )
        if materia_id:
            disponibilidades = disponibilidades.filter(registro__materias__id=materia_id)
        if carrera_id:
            disponibilidades = disponibilidades.filter(registro__materias__carrera_id=carrera_id)
        if formato:
            disponibilidades = disponibilidades.filter(formato=formato)
        if asesor_registro_id:
            disponibilidades = disponibilidades.filter(registro_id=asesor_registro_id)
        disponibilidades = list(disponibilidades.distinct())
```

Y en el `resultados.append({...})`, añadir las dos primeras claves:

```python
                resultados.append({
                    "registro_id": disp.registro_id,
                    "asesor_nombre": disp.registro.asesor.user.nombre_completo,
                    "disponibilidad_id": disp.id,
                    "fecha": fecha_cursor,
                    "hora_inicio": disp.hora_inicio,
                    "hora_fin": disp.hora_fin,
                    "formato": disp.formato,
                    "ubicacion": disp.ubicacion,
                    "liga_virtual": disp.liga_virtual,
                })
```

- [ ] **Step 5: Correr el test y verificar que pasa (incluida la regresión)**

Run: `python manage.py test asesorias.tests.test_api_busqueda -v 2`
Expected: PASS — los casos nuevos y los existentes (`test_excluye_slot_ya_agendado`, `test_no_devuelve_fechas_fuera_de_la_ventana`) siguen verdes.

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/serializers.py backend/asesorias/tests/test_api_busqueda.py
git commit -m "[feat][asesorias] busqueda de disponibilidad filtrable por asesor con identidad

- GET /disponibilidad/buscar/?asesor=<registro_id>
- cada resultado incluye registro_id y asesor_nombre

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: Carrera escribible al agendar

**Files:**
- Modify: `backend/asesorias/serializers.py` (`AsesoriaSerializer`)
- Test: `backend/asesorias/tests/test_api_asesoria.py` (añadir casos)

**Interfaces:**
- Consumes: `carreras.models.Carrera`.
- Produces: `POST /api/asesorias/asesorias/` acepta `carrera` en el body. Se valida contra las carreras del alumno — hoy el conjunto es `{alumno.carrera_id}` ([deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md)). Omitir `carrera` → usa `alumno.carrera`. Enviar una carrera ajena → `400`. El snapshot se conserva.

- [ ] **Step 1: Escribir el test que falla**

Añadir a `backend/asesorias/tests/test_api_asesoria.py` una clase (usa el mismo `setUp` que las demás; si el archivo ya tiene una clase con este `setUp`, añade sólo los métodos de test). Test autocontenido:

```python
import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class CarreraAlAgendarApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.carrera_ajena = Carrera.objects.create(clave=300, nombre="Matemáticas Aplicadas", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
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
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.proximo_lunes = self._proximo_dia_semana(0)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        return hoy + datetime.timedelta(days=delta or 7)

    def _payload(self, **extra):
        payload = {
            "disponibilidad": self.disponibilidad.id,
            "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        }
        payload.update(extra)
        return payload

    def test_agendar_con_carrera_propia_devuelve_201(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera=self.carrera.id)
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["carrera"], self.carrera.id)

    def test_omitir_carrera_usa_la_del_alumno(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["carrera"], self.carrera.id)

    def test_carrera_ajena_devuelve_400(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera=self.carrera_ajena.id)
        )
        self.assertEqual(response.status_code, 400)

    def test_snapshot_conserva_carrera_si_cambia_el_perfil(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 201, response.data)
        self.alumno.carrera = self.carrera_ajena
        self.alumno.save()
        from asesorias.models import Asesoria
        asesoria = Asesoria.objects.get(pk=response.data["id"])
        self.assertEqual(asesoria.carrera_id, self.carrera.id)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_asesoria.CarreraAlAgendarApiTests -v 2`
Expected: FAIL — `test_agendar_con_carrera_propia` y `test_carrera_ajena` fallan: hoy `carrera` es `read_only` (se ignora del payload) y no hay validación de carrera ajena.

- [ ] **Step 3: Hacer `carrera` escribible y validarla**

En `backend/asesorias/serializers.py`:

1. Importar `Carrera`:

```python
from carreras.models import Carrera
```

2. Declarar el campo `carrera` explícito en `AsesoriaSerializer` (junto a `alumno_nombre`/`asesor_nombre`):

```python
    carrera = serializers.PrimaryKeyRelatedField(queryset=Carrera.objects.all(), required=False)
```

3. Quitar `"carrera"` de `read_only_fields` (déjalo en `fields`):

```python
        read_only_fields = [
            "id", "alumno", "hora_inicio", "formato", "ubicacion", "liga_virtual",
            "estado", "asistio", "notas", "motivo_cancelacion", "cancelado_por", "creado_en",
        ]
```

4. Reescribir `validate` para usar la carrera del payload validada contra las del alumno:

```python
    def validate(self, attrs):
        disponibilidad = attrs["disponibilidad"]
        alumno = self.context["request"].user.perfil_alumno
        carrera = attrs.get("carrera") or alumno.carrera
        # Hoy el alumno tiene exactamente una carrera (deuda 0008). Cuando el
        # conjunto crezca, esta comprobación ya acepta cualquier carrera suya.
        carreras_del_alumno = {alumno.carrera_id}
        if carrera.id not in carreras_del_alumno:
            raise serializers.ValidationError({"carrera": "La carrera no pertenece al alumno."})
        instance = Asesoria(
            alumno=alumno,
            disponibilidad=disponibilidad,
            materia=attrs["materia"],
            carrera=carrera,
            fecha=attrs["fecha"],
            hora_inicio=disponibilidad.hora_inicio,
            formato=disponibilidad.formato,
            ubicacion=disponibilidad.ubicacion,
            liga_virtual=disponibilidad.liga_virtual,
        )
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        attrs["carrera"] = carrera
        attrs["hora_inicio"] = disponibilidad.hora_inicio
        attrs["formato"] = disponibilidad.formato
        attrs["ubicacion"] = disponibilidad.ubicacion
        attrs["liga_virtual"] = disponibilidad.liga_virtual
        return attrs
```

- [ ] **Step 4: Correr el test y verificar que pasa (con regresión de agendado)**

Run: `python manage.py test asesorias.tests.test_api_asesoria -v 2`
Expected: PASS — los casos nuevos y los ya existentes de agendado/`409` de `test_api_asesoria.py` siguen verdes.

- [ ] **Step 5: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/tests/test_api_asesoria.py
git commit -m "[feat][asesorias] carrera escribible y validada al agendar

- POST /asesorias/ acepta carrera; valida contra las carreras del alumno
- omitir carrera usa alumno.carrera; carrera ajena -> 400; snapshot conservado

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: Ocultar `notas` al alumno (corrección de seguridad)

**Files:**
- Modify: `backend/asesorias/serializers.py` (`AsesoriaSerializer.to_representation`)
- Test: `backend/asesorias/tests/test_api_asesoria.py` (añadir casos de seguridad)

**Interfaces:**
- Consumes: `context["request"].user`, `obj.disponibilidad.registro.asesor.user_id`.
- Produces: `AsesoriaSerializer` **omite** `notas` cuando el solicitante no es el asesor dueño de la sesión (aplica a `list` y `retrieve`). El asesor dueño y (futuro) admin siguen recibiéndolo. Un usuario doble-rol ve `notas` sólo en las sesiones donde es el asesor.

- [ ] **Step 1: Escribir el test que falla**

Añadir a `backend/asesorias/tests/test_api_asesoria.py` una clase autocontenida:

```python
class NotasOcultasApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

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
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        from asesorias.models import Asesoria
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=datetime.date.today(), hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
            estado="realizada", asistio=True, notas="El alumno debe repasar límites.",
        )

    def test_alumno_no_recibe_notas_en_list(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/asesorias/")
        self.assertTrue(response.data)
        self.assertNotIn("notas", response.data[0])

    def test_alumno_no_recibe_notas_en_retrieve(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")
        self.assertNotIn("notas", response.data)

    def test_asesor_dueno_si_recibe_notas(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")
        self.assertIn("notas", response.data)
        self.assertEqual(response.data["notas"], "El alumno debe repasar límites.")
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_asesoria.NotasOcultasApiTests -v 2`
Expected: FAIL — hoy `notas` viaja en la respuesta también para el alumno.

- [ ] **Step 3: Ocultar `notas` en `to_representation`**

En `backend/asesorias/serializers.py`, añadir a `AsesoriaSerializer`:

```python
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        user_id = getattr(user, "id", None)
        es_asesor_dueno = (
            user_id is not None
            and instance.disponibilidad.registro.asesor.user_id == user_id
        )
        if not es_asesor_dueno:
            data.pop("notas", None)
        return data
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_asesoria -v 2`
Expected: PASS — incluye la clase de carrera de Task 4 y todos los casos previos.

- [ ] **Step 5: Correr toda la suite de asesorías**

Run: `python manage.py test asesorias -v 2`
Expected: PASS — sin regresiones en `test_api_busqueda`, `test_api_flujo_completo`, `test_permissions`, etc.

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/tests/test_api_asesoria.py
git commit -m "[fix][asesorias] no exponer notas del asesor al alumno

- AsesoriaSerializer.to_representation omite notas salvo para el asesor dueno
- corrige leak de list/retrieve; asesor y futuro admin conservan el dato

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Self-Review

**Spec coverage** (contra `2026-08-08-asesorias-alumno-api-design.md`):
- Decision 1 (oferta) → Task 1. Decision 2 (asesores por materia) → Task 2. Decision 3 (`?asesor=` + identidad) → Task 3. Decision 4 (carrera escribible) → Task 4. Decision 5 (ocultar notas) → Task 5. Decision 6 (sin modelos/permisos nuevos) → Global Constraints. Todos los casos de la sección *Testing* del spec están cubiertos por los tests de las tasks.
- Error handling del spec: `403` (Tasks 1,2,3 tests), `404` (Task 2), `400` carrera ajena (Task 4), `400` de `clean()` y `409` doble-booking → regresión conservada (Task 4 Step 4).

**Placeholder scan:** ningún paso usa "TBD/implementar después/manejo apropiado"; todo el código y los tests están completos.

**Type/nombre consistency:** `registro_id`, `asesor_nombre`, `area_nombre`, `formatos`, `num_asesores`, `materia_id`, `carrera_id` son idénticos entre views, serializer, tests y el spec de frontend gemela. `OfertaView`/`AsesoresDeMateriaView` se importan con el mismo nombre en `views.py` y `urls.py`. `nombre_completo` coincide con el uso existente en `SesionFuturaSerializer`.
