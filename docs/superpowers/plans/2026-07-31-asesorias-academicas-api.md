# Asesorías Académicas — Fase 2 (capa DRF) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exponer vía DRF los flujos de alumno (buscar disponibilidad, agendar, cancelar) y asesor (registrar materias, publicar disponibilidad, marcar asistencia, guardar notas) de Asesorías Académicas, más catálogo de solo lectura (`carreras`, `materias`) que el frontend necesita para poblar filtros.

**Architecture:** Serializers/viewsets delgados sobre el dominio ya escrito en la Fase 0+1 (`asesorias/models.py`): las vistas invocan métodos de modelo ya validados (`agregar_materia`, `marcar_asistencia`, `guardar_notas`, `cancelar`, `clean()`) y traducen `ValidationError`/`IntegrityError` a códigos HTTP, sin reimplementar reglas de negocio. `ModelViewSet` + `@action` para recursos CRUD; `APIView` dedicada solo para la búsqueda de disponibilidad, cuyo resultado no es un shape CRUD estándar.

**Tech Stack:** Django REST Framework (`ModelViewSet`, `APIView`, `DefaultRouter`), `APITestCase` + `force_authenticate` para tests, JWT ya configurado (`rest_framework_simplejwt`), sin `django-filter` instalado (filtros de query params se implementan a mano en `get_queryset`).

## Global Constraints

- Prerrequisito: Fase 0+1 completa (`asesorias/models.py` con `PerfilAsesorAcademico`, `RegistroAsesor`, `Disponibilidad`, `Asesoria` y sus métodos de negocio) — ya mergeada en `dev-backend`.
- `REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]` ya es `["IsAuthenticated"]` (`config/settings/base.py:130`) — no hace falta declararlo por vista.
- Sin paginación en ningún listado de esta fase (deuda técnica ya documentada en `docs/technical-debt.md`).
- Ventana agendable = semana en curso + la siguiente, fija en código vía `asesorias.servicios.ventana_agendable()` — se aplica en `Asesoria.clean()` y en la búsqueda de disponibilidad, nunca hardcodeada dos veces.
- Alta de `PerfilAsesorAcademico` sigue siendo solo por Django admin — ningún endpoint de esta fase la expone.
- Todas las URLs nuevas cuelgan de `/api/<app>/` vía `include()` en `config/urls.py:6-10`, siguiendo el patrón ya usado por `accounts.urls`.
- Convención de commits: `[type][scope] resumen` (ver `docs/development/commit-conventions.md`); cada task de este plan es un commit atómico.
- `CELERY_TASK_ALWAYS_EAGER = "test" in sys.argv` (`config/settings/base.py:164`) ya hace que las notificaciones Celery corran síncronas en tests — no requiere configuración adicional en esta fase.

---

## Task 1: `ventana_agendable()` + extensión de `Asesoria.clean()`

**Files:**

- Create: `backend/asesorias/servicios.py`
- Create: `backend/asesorias/tests/test_servicios.py`
- Modify: `backend/asesorias/models.py:117-119` (método `Asesoria.clean()`)
- Modify: `backend/asesorias/tests/test_asesoria.py` (agregar un test a `AsesoriaConstraintTests`)

**Interfaces:**

- Produces: `ventana_agendable(hoy: datetime.date | None = None) -> tuple[datetime.date, datetime.date]` en `asesorias/servicios.py` — devuelve `(hoy_efectivo, domingo_que_cierra_la_semana_siguiente)`. Usado por Task 7 (búsqueda) y por `Asesoria.clean()`.

- [x] **Step 1: Escribir el test que falla para `ventana_agendable`**

```python
# backend/asesorias/tests/test_servicios.py
import datetime

from django.test import SimpleTestCase

from asesorias.servicios import ventana_agendable


class VentanaAgendableTests(SimpleTestCase):
    def test_lunes_devuelve_hoy_y_domingo_de_la_semana_siguiente(self):
        lunes = datetime.date(2026, 8, 3)  # lunes
        inicio, fin = ventana_agendable(lunes)
        self.assertEqual(inicio, lunes)
        self.assertEqual(fin, datetime.date(2026, 8, 16))  # domingo, 13 días después

    def test_miercoles_devuelve_hoy_y_domingo_de_la_semana_siguiente(self):
        miercoles = datetime.date(2026, 8, 5)
        inicio, fin = ventana_agendable(miercoles)
        self.assertEqual(inicio, miercoles)
        self.assertEqual(fin, datetime.date(2026, 8, 16))  # mismo domingo que si fuera lunes

    def test_domingo_devuelve_hoy_y_domingo_de_la_semana_siguiente(self):
        domingo = datetime.date(2026, 8, 9)  # domingo, cierra la semana en curso
        inicio, fin = ventana_agendable(domingo)
        self.assertEqual(inicio, domingo)
        self.assertEqual(fin, datetime.date(2026, 8, 16))

    def test_sin_argumento_usa_hoy(self):
        inicio, _fin = ventana_agendable()
        from django.utils import timezone
        self.assertEqual(inicio, timezone.localdate())
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_servicios -v 2`
Expected: FAIL con `ModuleNotFoundError: No module named 'asesorias.servicios'`

- [x] **Step 3: Implementar `ventana_agendable`**

```python
# backend/asesorias/servicios.py
import datetime

from django.utils import timezone


def ventana_agendable(hoy: datetime.date | None = None) -> tuple[datetime.date, datetime.date]:
    if hoy is None:
        hoy = timezone.localdate()
    lunes_de_esta_semana = hoy - datetime.timedelta(days=hoy.weekday())
    domingo_que_cierra_semana_siguiente = lunes_de_esta_semana + datetime.timedelta(days=13)
    return hoy, domingo_que_cierra_semana_siguiente
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_servicios -v 2`
Expected: PASS (4 tests)

- [x] **Step 5: Escribir el test que falla para la extensión de `Asesoria.clean()`**

Agregar este método a la clase `AsesoriaConstraintTests` en `backend/asesorias/tests/test_asesoria.py` (después de `test_fecha_no_coincide_con_dia_semana_falla_en_clean`):

```python
    def test_fecha_fuera_de_la_ventana_agendable_falla_en_clean(self):
        fecha_lejana = self.proximo_lunes + datetime.timedelta(days=30)
        asesoria = Asesoria(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=fecha_lejana, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        with self.assertRaises(ValidationError):
            asesoria.clean()
```

- [x] **Step 6: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_asesoria.AsesoriaConstraintTests.test_fecha_fuera_de_la_ventana_agendable_falla_en_clean -v 2`
Expected: FAIL (no se lanza `ValidationError` — la fecha lejana pasa `clean()` sin la nueva validación)

- [x] **Step 7: Extender `Asesoria.clean()`**

En `backend/asesorias/models.py`, agregar el import y modificar `clean()`:

```python
# Al inicio del archivo, junto a los demás imports:
from asesorias.servicios import ventana_agendable
```

```python
    def clean(self):
        if self.fecha.weekday() != self.disponibilidad.dia_semana:
            raise ValidationError("La fecha no coincide con el día de la disponibilidad.")
        inicio, fin = ventana_agendable()
        if not (inicio <= self.fecha <= fin):
            raise ValidationError("La fecha está fuera de la ventana agendable (semana en curso y la siguiente).")
```

- [x] **Step 8: Correr todos los tests de `asesorias` y verificar que pasan**

Run: `cd backend && .venv/bin/python manage.py test asesorias -v 2`
Expected: PASS — incluye el test nuevo y no rompe ninguno existente (`test_asesoria.py` ya usa `self.proximo_lunes`, que siempre cae dentro de la ventana agendable por construcción, así que ningún test viejo se ve afectado).

- [x] **Step 9: Commit**

```bash
git add backend/asesorias/servicios.py backend/asesorias/tests/test_servicios.py backend/asesorias/models.py backend/asesorias/tests/test_asesoria.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar ventana agendable a Asesoria.clean()

- asesorias/servicios.py: ventana_agendable(hoy=None) -> (hoy, domingo que
  cierra la semana siguiente), fija en código (ADR 0017, decision 3)
- Asesoria.clean() ahora rechaza fechas fuera de esa ventana, sin importar
  el punto de entrada (API, admin, shell)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 2: Catálogo de solo lectura — `carreras`

**Files:**

- Create: `backend/carreras/serializers.py`
- Create: `backend/carreras/views.py`
- Create: `backend/carreras/urls.py`
- Create: `backend/carreras/tests/test_api.py`
- Modify: `backend/config/urls.py`

**Interfaces:**

- Produces: `AreaSerializer`, `CarreraSerializer` en `carreras/serializers.py`; `AreaViewSet`, `CarreraViewSet` (ambos `ReadOnlyModelViewSet`) en `carreras/views.py`. Endpoints: `GET /api/carreras/areas/`, `GET /api/carreras/areas/{id}/`, `GET /api/carreras/carreras/`, `GET /api/carreras/carreras/{id}/`.

- [x] **Step 1: Escribir el test que falla**

```python
# backend/carreras/tests/test_api.py
from accounts.models import User
from carreras.models import Area, Carrera
from rest_framework.test import APITestCase


class CatalogoCarrerasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Matemáticas")
        self.carrera = Carrera.objects.create(clave=801, nombre="Actuaría", area=self.area)

    def test_sin_autenticacion_devuelve_401(self):
        response = self.client.get("/api/carreras/areas/")
        self.assertEqual(response.status_code, 401)

    def test_listar_areas(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/carreras/areas/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nombre"], "Matemáticas")

    def test_listar_carreras_incluye_area_anidada(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/carreras/carreras/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["nombre"], "Actuaría")
        self.assertEqual(response.data[0]["area"]["nombre"], "Matemáticas")

    def test_obtener_una_carrera(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/carreras/carreras/{self.carrera.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["clave"], 801)
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test carreras.tests.test_api -v 2`
Expected: FAIL con 404 (la URL `/api/carreras/` todavía no existe)

- [x] **Step 3: Implementar serializers, views, urls y wiring**

```python
# backend/carreras/serializers.py
from rest_framework import serializers

from .models import Area, Carrera


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "nombre"]


class CarreraSerializer(serializers.ModelSerializer):
    area = AreaSerializer(read_only=True)

    class Meta:
        model = Carrera
        fields = ["id", "clave", "nombre", "area", "acepta_nuevo_ingreso"]
```

```python
# backend/carreras/views.py
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Area, Carrera
from .serializers import AreaSerializer, CarreraSerializer


class AreaViewSet(ReadOnlyModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class CarreraViewSet(ReadOnlyModelViewSet):
    queryset = Carrera.objects.select_related("area").all()
    serializer_class = CarreraSerializer
```

```python
# backend/carreras/urls.py
from rest_framework.routers import DefaultRouter

from .views import AreaViewSet, CarreraViewSet

router = DefaultRouter()
router.register("areas", AreaViewSet, basename="area")
router.register("carreras", CarreraViewSet, basename="carrera")

urlpatterns = router.urls
```

```python
# backend/config/urls.py — reemplazar el archivo completo
from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/", include("accounts.urls")),
    path("api/carreras/", include("carreras.urls")),
]
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test carreras.tests.test_api -v 2`
Expected: PASS (4 tests)

- [x] **Step 5: Correr toda la suite para verificar que no se rompió nada**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/carreras/serializers.py backend/carreras/views.py backend/carreras/urls.py backend/carreras/tests/test_api.py backend/config/urls.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar API de solo lectura para catálogo de carreras

- ReadOnlyModelViewSet para Area y Carrera, sin filtros ni paginación
- Área anidada en la representación de Carrera

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 3: Catálogo de solo lectura — `materias` (filtrable)

**Files:**

- Create: `backend/materias/serializers.py`
- Create: `backend/materias/views.py`
- Create: `backend/materias/urls.py`
- Create: `backend/materias/tests/test_api.py`
- Modify: `backend/config/urls.py`

**Interfaces:**

- Consumes: patrón `ReadOnlyModelViewSet` de Task 2.
- Produces: `MateriaSerializer` en `materias/serializers.py`; `MateriaViewSet` en `materias/views.py`, filtrable por `?carrera=<id>` y `?habilitada_asesorias=true|false`. Endpoint: `GET /api/materias/materias/`. Usado por Task 7 (búsqueda) para resolver `materia_id`/`carrera_id`.

- [x] **Step 1: Escribir el test que falla**

```python
# backend/materias/tests/test_api.py
from accounts.models import User
from carreras.models import Area, Carrera
from materias.models import Materia
from rest_framework.test import APITestCase


class CatalogoMateriasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Matemáticas")
        self.carrera1 = Carrera.objects.create(clave=801, nombre="Actuaría", area=self.area)
        self.carrera2 = Carrera.objects.create(clave=802, nombre="Matemáticas", area=self.area)
        self.materia_habilitada = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera1, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_no_habilitada = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera1, nivel=1, plan=2006,
            habilitada_asesorias=False,
        )
        self.materia_otra_carrera = Materia.objects.create(
            clave="1901", nombre="Topología", carrera=self.carrera2, nivel=3, plan=2006,
            habilitada_asesorias=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_listar_todas(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_filtrar_por_carrera(self):
        response = self.client.get(f"/api/materias/materias/?carrera={self.carrera1.id}")
        claves = {m["clave"] for m in response.data}
        self.assertEqual(claves, {"1801", "1802"})

    def test_filtrar_por_habilitada_asesorias(self):
        response = self.client.get("/api/materias/materias/?habilitada_asesorias=true")
        claves = {m["clave"] for m in response.data}
        self.assertEqual(claves, {"1801", "1901"})

    def test_filtrar_por_carrera_y_habilitada(self):
        response = self.client.get(
            f"/api/materias/materias/?carrera={self.carrera1.id}&habilitada_asesorias=true"
        )
        claves = {m["clave"] for m in response.data}
        self.assertEqual(claves, {"1801"})
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test materias.tests.test_api -v 2`
Expected: FAIL con 404

- [x] **Step 3: Implementar serializer, view, urls y wiring**

```python
# backend/materias/serializers.py
from rest_framework import serializers

from .models import Materia


class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ["id", "clave", "nombre", "carrera", "nivel", "plan", "habilitada_asesorias"]
```

```python
# backend/materias/views.py
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Materia
from .serializers import MateriaSerializer


class MateriaViewSet(ReadOnlyModelViewSet):
    serializer_class = MateriaSerializer

    def get_queryset(self):
        queryset = Materia.objects.select_related("carrera").all()
        carrera_id = self.request.query_params.get("carrera")
        if carrera_id is not None:
            queryset = queryset.filter(carrera_id=carrera_id)
        habilitada_asesorias = self.request.query_params.get("habilitada_asesorias")
        if habilitada_asesorias is not None:
            queryset = queryset.filter(
                habilitada_asesorias=habilitada_asesorias.lower() in ("1", "true")
            )
        return queryset
```

```python
# backend/materias/urls.py
from rest_framework.routers import DefaultRouter

from .views import MateriaViewSet

router = DefaultRouter()
router.register("materias", MateriaViewSet, basename="materia")

urlpatterns = router.urls
```

```python
# backend/config/urls.py — agregar la línea marcada
from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/", include("accounts.urls")),
    path("api/carreras/", include("carreras.urls")),
    path("api/materias/", include("materias.urls")),  # <-- nueva
]
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test materias.tests.test_api -v 2`
Expected: PASS (4 tests)

- [x] **Step 5: Correr toda la suite**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/materias/serializers.py backend/materias/views.py backend/materias/urls.py backend/materias/tests/test_api.py backend/config/urls.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar API de solo lectura para catálogo de materias

- ReadOnlyModelViewSet filtrable por ?carrera= y ?habilitada_asesorias=
- Filtros implementados a mano en get_queryset (sin django-filter en el proyecto)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 4: Permisos de rol y de dueño

**Files:**

- Create: `backend/asesorias/permissions.py`
- Create: `backend/asesorias/tests/test_permissions.py`

**Interfaces:**

- Produces: `EsAlumno`, `EsAsesorAcademico`, `EsDueñoDelRegistro`, `EsDueñoDeLaAsesoria` (todas `rest_framework.permissions.BasePermission`) en `asesorias/permissions.py`. Consumidas por Tasks 5, 6, 7, 8.
  - `EsDueñoDelRegistro.has_object_permission(request, view, obj)`: acepta un `RegistroAsesor` (usa `obj.asesor`) o un `Disponibilidad` (usa `obj.registro.asesor`) — distingue con `hasattr(obj, "asesor")`.
  - `EsDueñoDeLaAsesoria.has_object_permission(request, view, obj)`: acepta un `Asesoria`; rama según `hasattr(request.user, "perfil_alumno")` vs `"perfil_asesor_academico"`.

- [x] **Step 1: Escribir el test que falla**

```python
# backend/asesorias/tests/test_permissions.py
from types import SimpleNamespace

from django.test import TestCase

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.permissions import EsAlumno, EsAsesorAcademico, EsDueñoDelRegistro
from carreras.models import Area

import datetime


class PermissionsTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Área test")

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.otro_asesor_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_asesor_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_asesor_user, area=self.area)

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(user=self.alumno_user, numero_cuenta="312345678")

    def test_es_alumno_true_para_usuario_con_perfil_alumno(self):
        request = SimpleNamespace(user=self.alumno_user)
        self.assertTrue(EsAlumno().has_permission(request, None))

    def test_es_alumno_false_para_asesor(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertFalse(EsAlumno().has_permission(request, None))

    def test_es_asesor_academico_true_para_asesor(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertTrue(EsAsesorAcademico().has_permission(request, None))

    def test_es_asesor_academico_false_para_alumno(self):
        request = SimpleNamespace(user=self.alumno_user)
        self.assertFalse(EsAsesorAcademico().has_permission(request, None))

    def test_dueño_del_registro_true_para_su_propio_registro(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertTrue(EsDueñoDelRegistro().has_object_permission(request, None, self.registro))

    def test_dueño_del_registro_false_para_otro_asesor(self):
        request = SimpleNamespace(user=self.otro_asesor_user)
        self.assertFalse(EsDueñoDelRegistro().has_object_permission(request, None, self.registro))

    def test_dueño_del_registro_true_para_su_propia_disponibilidad(self):
        request = SimpleNamespace(user=self.asesor_user)
        self.assertTrue(EsDueñoDelRegistro().has_object_permission(request, None, self.disponibilidad))

    def test_dueño_del_registro_false_para_disponibilidad_de_otro_asesor(self):
        request = SimpleNamespace(user=self.otro_asesor_user)
        self.assertFalse(EsDueñoDelRegistro().has_object_permission(request, None, self.disponibilidad))
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_permissions -v 2`
Expected: FAIL con `ModuleNotFoundError: No module named 'asesorias.permissions'`

- [x] **Step 3: Implementar `asesorias/permissions.py`**

```python
# backend/asesorias/permissions.py
from rest_framework.permissions import BasePermission


class EsAlumno(BasePermission):
    message = "Se requiere un perfil de alumno."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_alumno")


class EsAsesorAcademico(BasePermission):
    message = "Se requiere un perfil de asesor académico."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_asesor_academico")


class EsDueñoDelRegistro(BasePermission):
    message = "No puedes operar sobre el registro de otro asesor."

    def has_object_permission(self, request, view, obj):
        registro = obj if hasattr(obj, "asesor") else obj.registro
        return registro.asesor.user_id == request.user.id


class EsDueñoDeLaAsesoria(BasePermission):
    message = "No puedes operar sobre una sesión ajena."

    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, "perfil_alumno"):
            return obj.alumno_id == request.user.perfil_alumno.id
        if hasattr(request.user, "perfil_asesor_academico"):
            return obj.disponibilidad.registro.asesor.user_id == request.user.id
        return False
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_permissions -v 2`
Expected: PASS (8 tests)

- [x] **Step 5: Commit**

```bash
git add backend/asesorias/permissions.py backend/asesorias/tests/test_permissions.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar permisos de rol y de dueño para Asesorías

- EsAlumno/EsAsesorAcademico: chequeo de rol vía hasattr(user, "perfil_*")
- EsDueñoDelRegistro: object-level para RegistroAsesor y Disponibilidad
- EsDueñoDeLaAsesoria: object-level para Asesoria, ramifica por rol

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 5: `RegistroAsesorViewSet` + `agregar_materia`

**Files:**

- Create: `backend/asesorias/serializers.py`
- Create: `backend/asesorias/views.py`
- Create: `backend/asesorias/urls.py`
- Create: `backend/asesorias/tests/test_api_registro.py`
- Modify: `backend/config/urls.py`

**Interfaces:**

- Consumes: `EsAsesorAcademico`, `EsDueñoDelRegistro` (Task 4).
- Produces: `RegistroAsesorSerializer`, `AgregarMateriaSerializer` en `asesorias/serializers.py`; `RegistroAsesorViewSet` en `asesorias/views.py`. Endpoints: `GET/POST /api/asesorias/registros/`, `POST /api/asesorias/registros/{id}/materias/` con body `{"materia_id": <int>}`.

- [x] **Step 1: Escribir el test que falla**

```python
# backend/asesorias/tests/test_api_registro.py
from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class RegistroAsesorApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")
        self.carrera = Carrera.objects.create(clave=801, nombre="Actuaría", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)

        self.otro_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_user, area=self.area)
        self.registro_ajeno = RegistroAsesor.objects.create(asesor=self.otro_asesor, semestre="20271")

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        from accounts.models import PerfilAlumno
        PerfilAlumno.objects.create(user=self.alumno_user, numero_cuenta="312345678")

    def test_alumno_no_puede_crear_registro(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": "20271"})
        self.assertEqual(response.status_code, 403)

    def test_asesor_crea_su_registro(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/registros/", {"semestre": "20271"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RegistroAsesor.objects.get(id=response.data["id"]).asesor, self.asesor)

    def test_listar_solo_ve_sus_propios_registros(self):
        RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/registros/")
        self.assertEqual(len(response.data), 1)

    def test_agregar_materia_exitoso(self):
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/", {"materia_id": self.materia.id}
        )
        self.assertEqual(response.status_code, 200)
        registro.refresh_from_db()
        self.assertIn(self.materia, registro.materias.all())

    def test_agregar_materia_no_habilitada_devuelve_400(self):
        materia_no_habilitada = Materia.objects.create(
            clave="1802", nombre="Cálculo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=False,
        )
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/", {"materia_id": materia_no_habilitada.id}
        )
        self.assertEqual(response.status_code, 400)

    def test_agregar_materia_a_registro_ajeno_devuelve_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/registros/{self.registro_ajeno.id}/materias/", {"materia_id": self.materia.id}
        )
        self.assertEqual(response.status_code, 403)
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_registro -v 2`
Expected: FAIL con 404 (URL no existe)

- [x] **Step 3: Implementar serializers, view, urls y wiring**

```python
# backend/asesorias/serializers.py
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from materias.models import Materia

from .models import RegistroAsesor


class RegistroAsesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroAsesor
        fields = ["id", "semestre", "materias"]
        read_only_fields = ["materias"]


class AgregarMateriaSerializer(serializers.Serializer):
    materia_id = serializers.IntegerField()

    def validate_materia_id(self, value):
        try:
            return Materia.objects.get(pk=value)
        except Materia.DoesNotExist:
            raise serializers.ValidationError("La materia no existe.")
```

```python
# backend/asesorias/views.py
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import RegistroAsesor
from .permissions import EsAsesorAcademico, EsDueñoDelRegistro
from .serializers import AgregarMateriaSerializer, RegistroAsesorSerializer


class RegistroAsesorViewSet(ModelViewSet):
    serializer_class = RegistroAsesorSerializer
    permission_classes = [EsAsesorAcademico, EsDueñoDelRegistro]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return RegistroAsesor.objects.filter(asesor__user=self.request.user)
        # Fuera de list, get_object() resuelve sobre todo el queryset y deja
        # que EsDueñoDelRegistro (permission_classes, uniforme para todas
        # las acciones de este viewset) decida 403 vs. acceso — si se
        # filtrara aquí también, un registro ajeno daría 404 en vez de 403
        # en la acción materias/.
        return RegistroAsesor.objects.all()

    def perform_create(self, serializer):
        serializer.save(asesor=self.request.user.perfil_asesor_academico)

    @action(detail=True, methods=["post"], url_path="materias")
    def materias(self, request, pk=None):
        registro = self.get_object()
        serializer = AgregarMateriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        materia = serializer.validated_data["materia_id"]
        try:
            registro.agregar_materia(materia)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RegistroAsesorSerializer(registro).data, status=status.HTTP_200_OK)
```

```python
# backend/asesorias/urls.py
from rest_framework.routers import DefaultRouter

from .views import RegistroAsesorViewSet

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")

urlpatterns = router.urls
```

```python
# backend/config/urls.py — agregar la línea marcada
from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/", include("accounts.urls")),
    path("api/carreras/", include("carreras.urls")),
    path("api/materias/", include("materias.urls")),
    path("api/asesorias/", include("asesorias.urls")),  # <-- nueva
]
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_registro -v 2`
Expected: PASS (6 tests)

- [x] **Step 5: Correr toda la suite**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_registro.py backend/config/urls.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar API de RegistroAsesor con acción agregar materia

- ModelViewSet scoped al asesor autenticado (get_queryset + EsDueñoDelRegistro)
- @action materias/ invoca RegistroAsesor.agregar_materia(), traduce
  ValidationError del modelo a 400 sin reimplementar la regla

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 6: `DisponibilidadViewSet`

**Files:**

- Modify: `backend/asesorias/serializers.py` (agregar `DisponibilidadSerializer`)
- Modify: `backend/asesorias/views.py` (agregar `DisponibilidadViewSet`)
- Modify: `backend/asesorias/urls.py` (registrar `disponibilidades`)
- Create: `backend/asesorias/tests/test_api_disponibilidad.py`

**Interfaces:**

- Consumes: `EsAsesorAcademico`, `EsDueñoDelRegistro` (Task 4).
- Produces: `DisponibilidadSerializer` en `asesorias/serializers.py`; `DisponibilidadViewSet` en `asesorias/views.py`. Endpoints: `GET/POST /api/asesorias/disponibilidades/`, `PATCH/DELETE /api/asesorias/disponibilidades/{id}/`. Usado por Task 7 (búsqueda) y Task 8 (creación de `Asesoria` referencia `disponibilidad_id`).

- [x] **Step 1: Escribir el test que falla**

```python
# backend/asesorias/tests/test_api_disponibilidad.py
import datetime

from accounts.models import PerfilAcademico, User
from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area
from rest_framework.test import APITestCase


class DisponibilidadApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

        self.otro_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_user, area=self.area)
        self.registro_ajeno = RegistroAsesor.objects.create(asesor=self.otro_asesor, semestre="20271")

    def test_asesor_crea_disponibilidad_virtual(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 201)

    def test_crear_en_registro_ajeno_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro_ajeno.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 400)

    def test_hora_fuera_de_rejilla_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:15:00",
            "formato": "virtual", "liga_virtual": "https://meet.example.com/x",
        })
        self.assertEqual(response.status_code, 400)

    def test_presencial_sin_ubicacion_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "presencial",
        })
        self.assertEqual(response.status_code, 400)

    def test_bloque_duplicado_devuelve_400(self):
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/disponibilidades/", {
            "registro": self.registro.id, "dia_semana": 0, "hora_inicio": "10:00:00",
            "formato": "presencial", "ubicacion": "Salón 1",
        })
        self.assertEqual(response.status_code, 400)

    def test_listar_solo_ve_las_propias(self):
        Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        Disponibilidad.objects.create(
            registro=self.registro_ajeno, dia_semana=0, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/disponibilidades/")
        self.assertEqual(len(response.data), 1)

    def test_editar_disponibilidad_ajena_devuelve_403(self):
        disp_ajena = Disponibilidad.objects.create(
            registro=self.registro_ajeno, dia_semana=0, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.patch(f"/api/asesorias/disponibilidades/{disp_ajena.id}/", {"activa": False})
        self.assertEqual(response.status_code, 403)

    def test_eliminar_propia_disponibilidad(self):
        disp = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.delete(f"/api/asesorias/disponibilidades/{disp.id}/")
        self.assertEqual(response.status_code, 204)
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_disponibilidad -v 2`
Expected: FAIL con 404

- [x] **Step 3: Implementar**

Agregar a `backend/asesorias/serializers.py` (al final del archivo):

```python
from .models import Disponibilidad  # agregar a los imports de .models existentes


class DisponibilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilidad
        fields = ["id", "registro", "dia_semana", "hora_inicio", "formato", "ubicacion", "liga_virtual", "activa"]

    def validate_registro(self, value):
        request = self.context["request"]
        if value.asesor.user_id != request.user.id:
            raise serializers.ValidationError("No puedes crear disponibilidad para el registro de otro asesor.")
        return value

    def validate(self, attrs):
        instance = self.instance or Disponibilidad()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return attrs
```

Agregar a `backend/asesorias/views.py`:

```python
from .models import Disponibilidad  # agregar a los imports de .models existentes
from .serializers import DisponibilidadSerializer  # agregar al import existente


class DisponibilidadViewSet(ModelViewSet):
    serializer_class = DisponibilidadSerializer
    permission_classes = [EsAsesorAcademico, EsDueñoDelRegistro]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return Disponibilidad.objects.filter(registro__asesor__user=self.request.user)
        # Mismo razonamiento que en RegistroAsesorViewSet.get_queryset():
        # fuera de list, EsDueñoDelRegistro decide 403 vs. acceso sobre el
        # queryset completo.
        return Disponibilidad.objects.all()
```

`GenericAPIView.get_serializer_context()` ya incluye `"request"` por defecto, así que `validate_registro` (que lee `self.context["request"]`) funciona sin overrides adicionales.

Modificar `backend/asesorias/urls.py`:

```python
# backend/asesorias/urls.py
from rest_framework.routers import DefaultRouter

from .views import DisponibilidadViewSet, RegistroAsesorViewSet

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")

urlpatterns = router.urls
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_disponibilidad -v 2`
Expected: PASS (7 tests)

- [x] **Step 5: Correr toda la suite**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_disponibilidad.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar API CRUD de Disponibilidad scoped al asesor

- validate_registro verifica dueño antes de crear (no hay objeto todavía
  para el permission check de EsDueñoDelRegistro)
- validate() invoca Disponibilidad.clean() para las reglas de rejilla de
  30 min y ubicación/liga según formato, sin duplicar la regla
- UniqueConstraint (registro, dia_semana, hora_inicio) sin condición se
  valida automáticamente por DRF -> 400 en bloque duplicado

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 7: Búsqueda de disponibilidad (alumno)

**Files:**

- Modify: `backend/asesorias/serializers.py` (agregar `ResultadoBusquedaSerializer`)
- Modify: `backend/asesorias/views.py` (agregar `BuscarDisponibilidadView`)
- Modify: `backend/asesorias/urls.py` (agregar path de búsqueda)
- Create: `backend/asesorias/tests/test_api_busqueda.py`

**Interfaces:**

- Consumes: `ventana_agendable()` (Task 1), `EsAlumno` (Task 4).
- Produces: `BuscarDisponibilidadView` (`APIView`) en `asesorias/views.py`. Endpoint: `GET /api/asesorias/disponibilidad/buscar/?carrera=&materia=&formato=`, respuesta = lista de `{disponibilidad_id, fecha, hora_inicio, hora_fin, formato, ubicacion, liga_virtual}` dentro de la ventana agendable, excluyendo slots ya ocupados por una `Asesoria` no cancelada.

- [x] **Step 1: Escribir el test que falla**

```python
# backend/asesorias/tests/test_api_busqueda.py
import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from asesorias.servicios import ventana_agendable
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class BuscarDisponibilidadApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")
        self.carrera = Carrera.objects.create(clave=801, nombre="Actuaría", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

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
        self.alumno = PerfilAlumno.objects.create(user=self.alumno_user, numero_cuenta="312345678")

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
            fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
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
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_busqueda -v 2`
Expected: FAIL con 404

- [x] **Step 3: Implementar**

Agregar a `backend/asesorias/serializers.py`:

```python
class ResultadoBusquedaSerializer(serializers.Serializer):
    disponibilidad_id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()
    formato = serializers.CharField()
    ubicacion = serializers.CharField(allow_blank=True)
    liga_virtual = serializers.CharField(allow_blank=True)
```

Agregar a `backend/asesorias/views.py`:

```python
import datetime

from rest_framework.views import APIView

from .models import Asesoria  # agregar a los imports de .models existentes
from .permissions import EsAlumno  # agregar al import existente
from .serializers import ResultadoBusquedaSerializer  # agregar al import existente
from .servicios import ventana_agendable


class BuscarDisponibilidadView(APIView):
    permission_classes = [EsAlumno]

    def get(self, request):
        materia_id = request.query_params.get("materia")
        carrera_id = request.query_params.get("carrera")
        formato = request.query_params.get("formato")

        disponibilidades = Disponibilidad.objects.filter(activa=True).select_related("registro")
        if materia_id:
            disponibilidades = disponibilidades.filter(registro__materias__id=materia_id)
        if carrera_id:
            disponibilidades = disponibilidades.filter(registro__materias__carrera_id=carrera_id)
        if formato:
            disponibilidades = disponibilidades.filter(formato=formato)
        disponibilidades = list(disponibilidades.distinct())

        inicio, fin = ventana_agendable()
        ocupados = set(
            Asesoria.objects.filter(fecha__range=(inicio, fin))
            .exclude(estado="cancelada")
            .values_list("disponibilidad_id", "fecha")
        )

        resultados = []
        fecha_cursor = inicio
        while fecha_cursor <= fin:
            dia_semana = fecha_cursor.weekday()
            for disp in disponibilidades:
                if disp.dia_semana != dia_semana:
                    continue
                if (disp.id, fecha_cursor) in ocupados:
                    continue
                resultados.append({
                    "disponibilidad_id": disp.id,
                    "fecha": fecha_cursor,
                    "hora_inicio": disp.hora_inicio,
                    "hora_fin": disp.hora_fin,
                    "formato": disp.formato,
                    "ubicacion": disp.ubicacion,
                    "liga_virtual": disp.liga_virtual,
                })
            fecha_cursor += datetime.timedelta(days=1)

        return Response(ResultadoBusquedaSerializer(resultados, many=True).data)
```

Nota: `Disponibilidad` ya debe estar importado en `asesorias/views.py` desde el Task 6 — si no, agregarlo al import de `.models`.

Modificar `backend/asesorias/urls.py`:

```python
# backend/asesorias/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BuscarDisponibilidadView, DisponibilidadViewSet, RegistroAsesorViewSet

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
] + router.urls
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_busqueda -v 2`
Expected: PASS (5 tests)

- [x] **Step 5: Correr toda la suite**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_busqueda.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar búsqueda de disponibilidad para alumnos

- APIView dedicada (no ReadOnlyModelViewSet): el resultado son instancias
  concretas (fecha, disponibilidad) dentro de la ventana agendable, ya sin
  slots ocupados por una Asesoria no cancelada — no es un shape CRUD
- Filtros opcionales por materia/carrera/formato

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 8: `AsesoriaViewSet` — agendar, cancelar, marcar asistencia, notas

**Files:**

- Modify: `backend/asesorias/serializers.py` (agregar `AsesoriaSerializer`, `CancelarSerializer`, `MarcarAsistenciaSerializer`, `NotasSerializer`)
- Modify: `backend/asesorias/views.py` (agregar `AsesoriaViewSet`)
- Modify: `backend/asesorias/urls.py` (registrar `asesorias`)
- Create: `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**

- Consumes: `ventana_agendable()` (Task 1), `EsAlumno`/`EsAsesorAcademico`/`EsDueñoDeLaAsesoria` (Task 4).
- Produces: `AsesoriaSerializer` en `asesorias/serializers.py`; `AsesoriaViewSet` en `asesorias/views.py`. Endpoints: `GET /api/asesorias/asesorias/`, `POST /api/asesorias/asesorias/` (solo alumno), `POST /api/asesorias/asesorias/{id}/cancelar/`, `POST /api/asesorias/asesorias/{id}/marcar_asistencia/`, `POST /api/asesorias/asesorias/{id}/notas/`.

- [x] **Step 1: Escribir el test que falla**

```python
# backend/asesorias/tests/test_api_asesoria.py
import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class AsesoriaApiTestsBase(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")
        self.carrera = Carrera.objects.create(clave=801, nombre="Actuaría", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(user=self.alumno_user, numero_cuenta="312345678")

        self.otro_alumno_user = User.objects.create_user(email="otro_alumno@ciencias.unam.mx", password="x")
        self.otro_alumno = PerfilAlumno.objects.create(user=self.otro_alumno_user, numero_cuenta="312345679")

        self.proximo_lunes = self._proximo_dia_semana(0)

    @staticmethod
    def _proximo_dia_semana(dia_semana):
        hoy = timezone.localdate()
        delta = (dia_semana - hoy.weekday()) % 7
        delta = delta or 7
        return hoy + datetime.timedelta(days=delta)


class AgendarAsesoriaApiTests(AsesoriaApiTestsBase):
    def test_alumno_agenda_exitosamente(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["formato"], "virtual")
        self.assertEqual(response.data["estado"], "agendada")

    def test_asesor_no_puede_agendar(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 403)

    def test_fecha_que_no_coincide_con_dia_semana_devuelve_400(self):
        martes = self.proximo_lunes + datetime.timedelta(days=1)
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(martes),
        })
        self.assertEqual(response.status_code, 400)

    def test_doble_booking_devuelve_409(self):
        Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post("/api/asesorias/asesorias/", {
            "disponibilidad": self.disponibilidad.id, "materia": self.materia.id,
            "fecha": str(self.proximo_lunes),
        })
        self.assertEqual(response.status_code, 409)


class ListarAsesoriaApiTests(AsesoriaApiTestsBase):
    def test_alumno_solo_ve_sus_propias_sesiones(self):
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.proximo_lunes + datetime.timedelta(days=7),
            hora_inicio=self.disponibilidad.hora_inicio, formato=self.disponibilidad.formato,
            liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/asesorias/")
        self.assertEqual(len(response.data), 1)

    def test_asesor_ve_las_sesiones_de_sus_disponibilidades(self):
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.proximo_lunes, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/")
        self.assertEqual(len(response.data), 1)


class CicloDeVidaAsesoriaApiTests(AsesoriaApiTestsBase):
    def setUp(self):
        super().setUp()
        self.lunes_pasado = self.proximo_lunes - datetime.timedelta(days=7 * 5)
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )

    def test_asesor_marca_asistencia_y_guarda_notas(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/marcar_asistencia/", {"asistio": True}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "realizada")

        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/notas/", {"texto": "Repasamos series de Taylor."}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["notas"], "Repasamos series de Taylor.")

    def test_alumno_no_puede_marcar_asistencia(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/marcar_asistencia/", {"asistio": True}
        )
        self.assertEqual(response.status_code, 403)

    def test_asesor_no_dueño_no_puede_marcar_asistencia(self):
        otro_user = User.objects.create_user(email="otro_asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_user, numero_trabajador="99999")
        PerfilAsesorAcademico.objects.create(user=otro_user, area=self.area)
        self.client.force_authenticate(user=otro_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/marcar_asistencia/", {"asistio": True}
        )
        self.assertEqual(response.status_code, 403)

    def test_guardar_notas_sin_asistencia_confirmada_devuelve_400(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/notas/", {"texto": "texto"}
        )
        self.assertEqual(response.status_code, 400)

    def test_alumno_cancela_y_libera_el_slot(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["estado"], "cancelada")

        segunda = Asesoria.objects.create(
            alumno=self.otro_alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            fecha=self.lunes_pasado, hora_inicio=self.disponibilidad.hora_inicio,
            formato=self.disponibilidad.formato, liga_virtual=self.disponibilidad.liga_virtual,
        )
        self.assertIsNotNone(segunda.id)

    def test_alumno_ajeno_no_puede_cancelar(self):
        self.client.force_authenticate(user=self.otro_alumno_user)
        response = self.client.post(f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/", {})
        self.assertEqual(response.status_code, 403)
```

- [x] **Step 2: Correr el test y verificar que falla**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_asesoria -v 2`
Expected: FAIL con 404

- [x] **Step 3: Implementar**

Agregar a `backend/asesorias/serializers.py`:

```python
from .models import Asesoria  # agregar a los imports de .models existentes


class AsesoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asesoria
        fields = [
            "id", "alumno", "disponibilidad", "materia", "fecha", "hora_inicio",
            "formato", "ubicacion", "liga_virtual", "estado", "asistio", "notas", "creado_en",
        ]
        read_only_fields = [
            "id", "alumno", "hora_inicio", "formato", "ubicacion", "liga_virtual",
            "estado", "asistio", "notas", "creado_en",
        ]
        # DRF genera un UniqueTogetherValidator automático a partir del
        # UniqueConstraint condicional de Asesoria, lo que rechazaría el
        # doble-booking con 400 antes de tocar la base de datos. Se
        # desactiva a propósito: ADR 0017 decisión 8 exige que la condición
        # de carrera se resuelva en la base de datos y se traduzca a 409,
        # no que se prevenga con un chequeo optimista en la vista.
        validators = []

    def validate(self, attrs):
        disponibilidad = attrs["disponibilidad"]
        instance = Asesoria(
            alumno=self.context["request"].user.perfil_alumno,
            disponibilidad=disponibilidad,
            materia=attrs["materia"],
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
        attrs["hora_inicio"] = disponibilidad.hora_inicio
        attrs["formato"] = disponibilidad.formato
        attrs["ubicacion"] = disponibilidad.ubicacion
        attrs["liga_virtual"] = disponibilidad.liga_virtual
        return attrs

    def create(self, validated_data):
        validated_data["alumno"] = self.context["request"].user.perfil_alumno
        return Asesoria.objects.create(**validated_data)


class CancelarSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=False, allow_blank=True, default="")


class MarcarAsistenciaSerializer(serializers.Serializer):
    asistio = serializers.BooleanField()


class NotasSerializer(serializers.Serializer):
    texto = serializers.CharField(allow_blank=True)
```

Agregar a `backend/asesorias/views.py`:

```python
from django.db import IntegrityError, transaction
from rest_framework.permissions import IsAuthenticated

from .models import Asesoria  # ya debe estar importado desde Task 7; si no, agregar
from .permissions import EsDueñoDeLaAsesoria  # agregar al import existente
from .serializers import (  # ampliar el import existente
    AsesoriaSerializer, CancelarSerializer, MarcarAsistenciaSerializer, NotasSerializer,
)


class AsesoriaViewSet(ModelViewSet):
    serializer_class = AsesoriaSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [EsAlumno()]
        if self.action == "cancelar":
            return [EsAlumno(), EsDueñoDeLaAsesoria()]
        if self.action in ("marcar_asistencia", "notas"):
            return [EsAsesorAcademico(), EsDueñoDeLaAsesoria()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if self.action in ("cancelar", "marcar_asistencia", "notas"):
            # get_object() resuelve desde este queryset ANTES de aplicar
            # has_object_permission. Si se filtrara aquí por dueño, un
            # objeto ajeno daría 404 y nunca llegaría a EsDueñoDeLaAsesoria
            # -> el 403 explícito que exige el ADR 0017 se perdería.
            return Asesoria.objects.all()
        if hasattr(user, "perfil_alumno"):
            return Asesoria.objects.filter(alumno=user.perfil_alumno)
        if hasattr(user, "perfil_asesor_academico"):
            return Asesoria.objects.filter(disponibilidad__registro__asesor__user=user)
        return Asesoria.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "Este horario ya fue tomado por otro alumno."},
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        asesoria = self.get_object()
        serializer = CancelarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asesoria.cancelar(usuario=request.user, motivo=serializer.validated_data["motivo"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AsesoriaSerializer(asesoria).data)

    @action(detail=True, methods=["post"], url_path="marcar_asistencia")
    def marcar_asistencia(self, request, pk=None):
        asesoria = self.get_object()
        serializer = MarcarAsistenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asesoria.marcar_asistencia(serializer.validated_data["asistio"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AsesoriaSerializer(asesoria).data)

    @action(detail=True, methods=["post"])
    def notas(self, request, pk=None):
        asesoria = self.get_object()
        serializer = NotasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            asesoria.guardar_notas(serializer.validated_data["texto"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AsesoriaSerializer(asesoria).data)
```

Modificar `backend/asesorias/urls.py`:

```python
# backend/asesorias/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AsesoriaViewSet, BuscarDisponibilidadView, DisponibilidadViewSet, RegistroAsesorViewSet,
)

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")
router.register("asesorias", AsesoriaViewSet, basename="asesoria")

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
] + router.urls
```

- [x] **Step 4: Correr el test y verificar que pasa**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_asesoria -v 2`
Expected: PASS (13 tests)

- [x] **Step 5: Correr toda la suite**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_asesoria.py
git commit -m "$(cat <<'EOF'
[feat][backend] agregar AsesoriaViewSet compartido alumno/asesor

- get_queryset/get_permissions ramifican por perfil del usuario en vez de
  dos viewsets separados (ADR 0017)
- create() envuelve en transaction.atomic() y traduce IntegrityError del
  UniqueConstraint condicional a 409, en vez de dejarlo propagar como 500
- validate() en el serializer invoca Asesoria.clean() (día de semana +
  ventana agendable); acciones cancelar/marcar_asistencia/notas invocan
  los métodos de modelo ya escritos en la Fase 1

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Task 9: Test de integración end-to-end + cierre de fase

**Files:**

- Create: `backend/asesorias/tests/test_api_flujo_completo.py`

**Interfaces:**

- Consumes: todos los endpoints de Tasks 2–8.
- Produces: nada nuevo — es la verificación de que todas las piezas encajan en un flujo real, tal como lo pide la sección "Testing" de la spec (`docs/superpowers/specs/2026-07-30-asesorias-academicas-api-design.md`).

- [x] **Step 1: Escribir el test de flujo completo (ya "falla" en el sentido de que es nuevo, pero se espera que pase de inmediato dado que Tasks 1–8 ya están implementados — este paso documenta el comportamiento end-to-end, no introduce código nuevo de producción)**

```python
# backend/asesorias/tests/test_api_flujo_completo.py
import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import Asesoria
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia, OfertaMateria
from rest_framework.test import APITestCase


class FlujoCompletoAsesoriaApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Matemáticas")
        self.carrera = Carrera.objects.create(clave=801, nombre="Actuaría", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)

        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")

        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(user=self.alumno_user, numero_cuenta="312345678")

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
```

- [x] **Step 2: Correr el test de flujo completo**

Run: `cd backend && .venv/bin/python manage.py test asesorias.tests.test_api_flujo_completo -v 2`
Expected: PASS (2 tests). Si falla, el error señala qué pieza de las Tasks 1–8 no encaja con las demás — corregir ahí, no en este archivo de test.

- [x] **Step 3: Correr la suite completa del proyecto**

Run: `cd backend && .venv/bin/python manage.py test`
Expected: PASS — todos los tests de Fase 0+1 (60 tests previos) más todos los de esta fase.

- [x] **Step 4: Commit**

```bash
git add backend/asesorias/tests/test_api_flujo_completo.py
git commit -m "$(cat <<'EOF'
[test][backend] agregar test end-to-end del flujo completo de Asesorías

Cubre: asesor publica catálogo/registro/disponibilidad -> alumno busca y
agenda -> asesor dueño marca asistencia y guarda notas -> verifica que
ni un alumno ni un asesor no-dueño pueden operar sobre la sesión, y que
cancelar libera el slot para otro alumno.

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>
EOF
)"
```

---

## Verification (fin del plan)

1. `cd backend && .venv/bin/python manage.py test` — suite completa en verde (Fase 0+1 + Fase 2).
2. `cd backend && .venv/bin/python manage.py runserver` y probar manualmente con `curl`/Postman el flujo: login JWT (`POST /api/auth/login/`) → `GET /api/carreras/carreras/` → crear registro/disponibilidad como asesor → `GET /api/asesorias/disponibilidad/buscar/` como alumno → `POST /api/asesorias/asesorias/` → confirmar en Django admin que la `Asesoria` quedó creada y que se envió la notificación (revisar log de la consola, `EMAIL_BACKEND` es `console` por default).
3. Revisar que `docs/technical-debt.md` siga describiendo con precisión la deuda de esta fase (sin paginación, alta de asesor solo admin, ventana fija en código) — no debería requerir cambios, ya fue escrito junto con ADR 0017 antes de esta implementación.
4. Confirmar que ningún test de Fase 0+1 (`test_asesoria.py`, `test_disponibilidad.py`, `test_registro_asesor.py`, `test_perfil_asesor_academico.py`, `test_notificaciones.py`) se vio afectado por la extensión de `Asesoria.clean()` del Task 1.
