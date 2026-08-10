# API de administración SAE de Asesorías — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introducir la identidad `PerfilSAE` (rol `'sae'`) y una superficie de API de **solo lectura** bajo `/api/asesorias/admin/` para que un miembro de la SAE supervise asesorías, semestres, asesores y alumnos.

**Architecture:** Un modelo nuevo (`accounts.PerfilSAE`, única migración del feature), dos permisos nuevos en `asesorias/permissions.py`, cinco `APIView` de solo lectura nuevas en `asesorias/views.py` + sus `path()` en `asesorias/urls.py`, un helper `semestre_vigente()` en `asesorias/servicios.py`, y dos gates ampliados (permiso de oferta/búsqueda, y `notas` en `AsesoriaSerializer.to_representation`). El `AsesoriaViewSet` acotado al usuario NO se toca.

**Tech Stack:** Django + Django REST Framework. Tests con `rest_framework.test.APITestCase` + `force_authenticate`.

**Spec:** [`2026-08-09-asesorias-sae-admin-api-design.md`](../specs/2026-08-09-asesorias-sae-admin-api-design.md) · **ADR:** [0023](../../decisions/0023-asesorias-sae-admin-api.md)

## Global Constraints

- **Solo lectura.** Todos los endpoints admin son `GET`. Ningún `POST`/`PATCH`/`DELETE` para el SAE.
- **Sin paginación** en los listados admin → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md). No añadir `pagination_class`.
- **Filtrado lenient por query param**, patrón de `BuscarDisponibilidadView` (`asesorias/views.py:111-120`): un id no numérico se ignora (`.isdigit()`), no rompe ni da 400. Un `?semestre=` desconocido devuelve `[]`, no 400 ([deuda 0001](../../technical-debt/0001-sin-modelo-calendario-academico.md)).
- **Reuso de `AsesoriaSerializer`** para `/admin/asesorias/`: no se crea un serializer paralelo del recurso; solo se amplía su gate de `notas`.
- **Una sola migración**: `accounts.PerfilSAE`. Ningún modelo de `asesorias` cambia de esquema.
- **No se reabren ADR 0017 ni ADR 0021.** El alumno sigue sin ver `notas`; `POST /asesorias/` sigue siendo `EsAlumno`; `AsesoriaViewSet.get_queryset` no cambia.
- **Deuda referenciada, no nueva:** alta manual de `PerfilSAE` → [0014](../../technical-debt/0014-alta-perfil-sae-solo-admin.md) (ya escrita); paginación → [0006](../../technical-debt/0006-sin-paginacion-listados.md); scope de semestre en oferta → [0012](../../technical-debt/0012-oferta-asesorias-sin-scope-de-semestre.md); disponibilidad histórica → [0005](../../technical-debt/0005-editar-disponibilidad-no-propaga.md). **No crear archivos nuevos de deuda.**
- **Formato de semestre real: `"20262"`** (`CharField(max_length=5)`, `YYYYN`), NO `"2026-2"` como en los ejemplos de la spec. Usar siempre el formato real.
- **`nombre_completo`** es la propiedad de `accounts.User` para el nombre a mostrar (no es campo de BD: no se puede `order_by`/`filter` sobre ella).
- **Comando de tests:** desde `backend/`, `python manage.py test <ruta> -v 2`. Requiere Postgres. Si no hay Postgres local: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test <ruta> -v 2`.
- **Commits:** formato `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>`.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `backend/accounts/models.py` | Modelo `PerfilSAE` | Modificar |
| `backend/accounts/migrations/0004_perfilsae.py` | Migración del perfil | Crear (generada) |
| `backend/accounts/admin.py` | Alta manual de `PerfilSAE` | Modificar |
| `backend/accounts/serializers.py` | Rol `'sae'` en `get_roles` | Modificar |
| `backend/asesorias/permissions.py` | `EsMiembroSAE`, `EsAlumnoOMiembroSAE` | Modificar |
| `backend/asesorias/servicios.py` | `semestre_vigente()` | Modificar |
| `backend/asesorias/serializers.py` | Gate de `notas`; serializers del detalle de asesor | Modificar |
| `backend/asesorias/views.py` | Permisos ampliados + 5 views admin | Modificar |
| `backend/asesorias/urls.py` | 5 `path()` bajo `admin/` | Modificar |
| `backend/accounts/tests/test_perfiles.py` | Tests del modelo `PerfilSAE` | Modificar |
| `backend/accounts/tests/test_admin.py` | Registro en Django admin | Modificar |
| `backend/accounts/tests/test_user_details.py` | Rol `'sae'` | Modificar |
| `backend/asesorias/tests/test_permissions.py` | Permisos SAE | Modificar |
| `backend/asesorias/tests/test_api_oferta.py` | SAE en oferta/asesores-por-materia | Modificar |
| `backend/asesorias/tests/test_api_busqueda.py` | SAE en búsqueda de disponibilidad | Modificar |
| `backend/asesorias/tests/test_api_asesoria.py` | `notas` visibles al SAE + regresión alumno | Modificar |
| `backend/asesorias/tests/test_api_admin.py` | Tests de los 5 endpoints admin | Crear |
| `backend/asesorias/tests/test_servicios.py` | `semestre_vigente()` | Modificar |

---

## Task 1: Modelo `PerfilSAE` + migración + Django admin

**Files:**
- Modify: `backend/accounts/models.py`
- Create: `backend/accounts/migrations/0004_perfilsae.py` (generada por `makemigrations`)
- Modify: `backend/accounts/admin.py`
- Test: `backend/accounts/tests/test_perfiles.py`, `backend/accounts/tests/test_admin.py`

**Interfaces:**
- Produces: `accounts.models.PerfilSAE` con `user = OneToOneField(User, on_delete=CASCADE, related_name="perfil_sae")` y `activo = BooleanField(default=True)`. El `related_name` `perfil_sae` es lo que consumen `get_roles` (Task 2) y `EsMiembroSAE` (Task 3).

- [ ] **Step 1: Escribir los tests que fallan**

Añadir al final de `backend/accounts/tests/test_perfiles.py`:

```python
class PerfilSAETests(TestCase):
    def test_un_user_no_puede_tener_dos_perfiles_sae(self):
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilSAE.objects.create(user=user)

    def test_nace_activo_y_es_accesible_por_related_name(self):
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae2@ciencias.unam.mx", password="x")
        perfil = PerfilSAE.objects.create(user=user)
        user.refresh_from_db()
        self.assertTrue(perfil.activo)
        self.assertTrue(hasattr(user, "perfil_sae"))
        self.assertEqual(user.perfil_sae.id, perfil.id)

    def test_usuario_sin_perfil_sae_no_tiene_el_atributo(self):
        user = User.objects.create_user(email="nadie@ciencias.unam.mx", password="x")
        self.assertFalse(hasattr(user, "perfil_sae"))
```

Añadir al final de `backend/accounts/tests/test_admin.py`:

```python
    def test_perfil_sae_registrado(self):
        from accounts.models import PerfilSAE

        self.assertIn(PerfilSAE, admin.site._registry)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test accounts.tests.test_perfiles accounts.tests.test_admin -v 2`
Expected: FAIL — `ImportError: cannot import name 'PerfilSAE' from 'accounts.models'`.

- [ ] **Step 3: Añadir el modelo**

Al final de `backend/accounts/models.py`:

```python
class PerfilSAE(models.Model):
    """Miembro de la Secretaría de Asuntos Estudiantiles.

    Patrón PerfilX de ADR 0012: el rol se deriva de que el perfil exista
    (`hasattr(user, "perfil_sae")`). Vive en `accounts` y no en `asesorias`
    porque otros servicios de la SAE reutilizarán la misma identidad.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_sae")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"SAE — {self.user.email}"
```

- [ ] **Step 4: Generar la migración**

Run: `python manage.py makemigrations accounts`
Expected: crea `backend/accounts/migrations/0004_perfilsae.py`. Verificar que el archivo existe y que NO contiene cambios de otros modelos.

- [ ] **Step 5: Registrar en Django admin**

En `backend/accounts/admin.py`, cambiar el import y añadir la clase al final:

```python
from .models import User, PerfilAcademico, PerfilAlumno, PerfilSAE
```

```python
@admin.register(PerfilSAE)
class PerfilSAEAdmin(admin.ModelAdmin):
    list_display = ("user", "activo")
    list_filter = ("activo",)
    search_fields = ("user__email",)
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `python manage.py test accounts -v 2`
Expected: PASS — 4 tests nuevos y todos los previos de `accounts`.

- [ ] **Step 7: Commit**

```bash
git add backend/accounts/models.py backend/accounts/migrations/0004_perfilsae.py backend/accounts/admin.py backend/accounts/tests/test_perfiles.py backend/accounts/tests/test_admin.py
git commit -m "[feat][accounts] perfil de miembro SAE

- PerfilSAE OneToOne a User (related_name perfil_sae) con activo
- migracion 0004 y registro en Django admin (alta manual, deuda 0014)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Rol `'sae'` en `/api/auth/user/`

**Files:**
- Modify: `backend/accounts/serializers.py` (`UserDetailsSerializer.get_roles`)
- Test: `backend/accounts/tests/test_user_details.py`

**Interfaces:**
- Consumes: `PerfilSAE` (Task 1).
- Produces: `GET /api/auth/user/` y el body de login devuelven `roles` con `"sae"` cuando existe `user.perfil_sae`. No se añade ningún objeto anidado `perfil_sae` (fuera de spec).

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a la clase `UserDetailsApiTests` en `backend/accounts/tests/test_user_details.py`:

```python
    def test_miembro_sae_reporta_el_rol_sae(self):
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=user)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], ["sae"])

    def test_usuario_sin_perfil_sae_no_reporta_el_rol(self):
        user = User.objects.create_user(email="no-sae@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=user, numero_cuenta="312999999", carrera=self.carrera, generacion=2023,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertNotIn("sae", response.data["roles"])

    def test_sae_inactivo_conserva_el_rol(self):
        """El rol depende de que el perfil exista, no de `activo` — mismo
        criterio que EsAsesorAcademico y que la permission EsMiembroSAE."""
        from accounts.models import PerfilSAE

        user = User.objects.create_user(email="sae-inactivo@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=user, activo=False)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertIn("sae", response.data["roles"])
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test accounts.tests.test_user_details -v 2`
Expected: FAIL — `AssertionError: [] != ['sae']`.

- [ ] **Step 3: Añadir el rol**

En `backend/accounts/serializers.py`, dentro de `UserDetailsSerializer.get_roles`, añadir el bloque justo antes de `return roles`:

```python
        # Mismo criterio que los demás roles: existe el perfil -> existe el
        # rol. `activo` no participa (lo mismo que comprueba EsMiembroSAE).
        if hasattr(obj, "perfil_sae"):
            roles.append("sae")
        return roles
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `python manage.py test accounts -v 2`
Expected: PASS — incluye los tests previos de `roles` (`test_usuario_sin_perfiles_reporta_roles_vacios`, `test_alumno_reporta_su_rol_y_su_perfil`).

- [ ] **Step 5: Commit**

```bash
git add backend/accounts/serializers.py backend/accounts/tests/test_user_details.py
git commit -m "[feat][accounts] exponer el rol sae en el detalle de usuario

- UserDetailsSerializer.get_roles anade 'sae' si existe perfil_sae
- criterio por existencia de perfil, no por activo

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Permisos `EsMiembroSAE` y `EsAlumnoOMiembroSAE`

**Files:**
- Modify: `backend/asesorias/permissions.py`
- Test: `backend/asesorias/tests/test_permissions.py`

**Interfaces:**
- Consumes: `related_name` `perfil_sae` (Task 1).
- Produces: `asesorias.permissions.EsMiembroSAE` (`has_permission` → `hasattr(request.user, "perfil_sae")`) y `asesorias.permissions.EsAlumnoOMiembroSAE` (`perfil_alumno` **o** `perfil_sae`). Los consumen las Tasks 4, 6, 7, 8, 9, 10.

- [ ] **Step 1: Escribir el test que falla**

Añadir al final de `backend/asesorias/tests/test_permissions.py`:

```python
class PermisosSAETests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Área SAE test")
        self.carrera = Carrera.objects.create(clave=903, nombre="Carrera SAE Test", area=self.area)

        self.sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        from accounts.models import PerfilSAE
        PerfilSAE.objects.create(user=self.sae_user)

        self.alumno_user = User.objects.create_user(email="alumno-sae@ciencias.unam.mx", password="x")
        PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="313000001", carrera=self.carrera, generacion=2023)

        self.asesor_user = User.objects.create_user(email="asesor-sae@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="80001")
        PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)

    def test_es_miembro_sae_true_para_usuario_con_perfil_sae(self):
        from asesorias.permissions import EsMiembroSAE
        request = SimpleNamespace(user=self.sae_user)
        self.assertTrue(EsMiembroSAE().has_permission(request, None))

    def test_es_miembro_sae_false_para_alumno(self):
        from asesorias.permissions import EsMiembroSAE
        request = SimpleNamespace(user=self.alumno_user)
        self.assertFalse(EsMiembroSAE().has_permission(request, None))

    def test_es_miembro_sae_false_para_asesor(self):
        from asesorias.permissions import EsMiembroSAE
        request = SimpleNamespace(user=self.asesor_user)
        self.assertFalse(EsMiembroSAE().has_permission(request, None))

    def test_es_alumno_o_miembro_sae_true_para_alumno(self):
        from asesorias.permissions import EsAlumnoOMiembroSAE
        request = SimpleNamespace(user=self.alumno_user)
        self.assertTrue(EsAlumnoOMiembroSAE().has_permission(request, None))

    def test_es_alumno_o_miembro_sae_true_para_sae(self):
        from asesorias.permissions import EsAlumnoOMiembroSAE
        request = SimpleNamespace(user=self.sae_user)
        self.assertTrue(EsAlumnoOMiembroSAE().has_permission(request, None))

    def test_es_alumno_o_miembro_sae_false_para_asesor(self):
        from asesorias.permissions import EsAlumnoOMiembroSAE
        request = SimpleNamespace(user=self.asesor_user)
        self.assertFalse(EsAlumnoOMiembroSAE().has_permission(request, None))
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_permissions.PermisosSAETests -v 2`
Expected: FAIL — `ImportError: cannot import name 'EsMiembroSAE' from 'asesorias.permissions'`.

- [ ] **Step 3: Implementar los permisos**

Añadir al final de `backend/asesorias/permissions.py`:

```python
class EsMiembroSAE(BasePermission):
    message = "Se requiere un perfil de miembro de la SAE."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_sae")


class EsAlumnoOMiembroSAE(BasePermission):
    message = "Se requiere un perfil de alumno o de miembro de la SAE."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_alumno") or hasattr(request.user, "perfil_sae")
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_permissions -v 2`
Expected: PASS — 6 tests nuevos + los previos.

- [ ] **Step 5: Commit**

```bash
git add backend/asesorias/permissions.py backend/asesorias/tests/test_permissions.py
git commit -m "[feat][asesorias] permisos EsMiembroSAE y EsAlumnoOMiembroSAE

- hasattr(user, perfil_sae), mismo patron que los permisos existentes
- EsAlumnoOMiembroSAE para los endpoints de consulta compartidos

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: Ampliar oferta / asesores-por-materia / búsqueda a `EsAlumnoOMiembroSAE`

**Files:**
- Modify: `backend/asesorias/views.py` (`OfertaView`, `AsesoresDeMateriaView`, `BuscarDisponibilidadView`)
- Test: `backend/asesorias/tests/test_api_oferta.py`, `backend/asesorias/tests/test_api_busqueda.py`

**Interfaces:**
- Consumes: `EsAlumnoOMiembroSAE` (Task 3).
- Produces: `GET /api/asesorias/oferta/`, `GET /api/asesorias/oferta/{materia_id}/asesores/` y `GET /api/asesorias/disponibilidad/buscar/` devuelven `200` a un miembro SAE sin `PerfilAlumno`. `POST /api/asesorias/asesorias/` sigue `EsAlumno` → `403` para el SAE. Un usuario que no es alumno ni SAE sigue recibiendo `403`.

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a la clase `OfertaApiTests` en `backend/asesorias/tests/test_api_oferta.py`:

```python
    def test_miembro_sae_puede_consultar_la_oferta(self):
        from accounts.models import PerfilSAE

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        self.client.force_authenticate(user=sae_user)
        response = self.client.get("/api/asesorias/oferta/")
        self.assertEqual(response.status_code, 200)
        ids = {m["materia_id"] for m in response.data}
        self.assertIn(self.materia_con_asesor.id, ids)
```

Añadir a la clase `AsesoresDeMateriaApiTests` en el mismo archivo:

```python
    def test_miembro_sae_puede_consultar_los_asesores_de_la_materia(self):
        from accounts.models import PerfilSAE

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        self.client.force_authenticate(user=sae_user)
        response = self.client.get(f"/api/asesorias/oferta/{self.materia.id}/asesores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
```

Añadir a la clase `BuscarDisponibilidadApiTests` en `backend/asesorias/tests/test_api_busqueda.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test asesorias.tests.test_api_oferta asesorias.tests.test_api_busqueda -v 2`
Expected: FAIL — los tres tests de SAE dan `403` en vez de `200` (`test_miembro_sae_no_puede_agendar` ya pasa).

- [ ] **Step 3: Ampliar los permisos de las tres views**

En `backend/asesorias/views.py`:

1. Añadir `EsAlumnoOMiembroSAE` al import de `.permissions`:

```python
from .permissions import (
    EsAlumno, EsAlumnoOAsesorAcademico, EsAlumnoOMiembroSAE, EsAsesorAcademico,
    EsDuenoDelRegistro, EsDuenoDeLaAsesoria,
)
```

2. Cambiar la línea `permission_classes = [EsAlumno]` en **las tres** clases `BuscarDisponibilidadView`, `OfertaView` y `AsesoresDeMateriaView` por:

```python
    permission_classes = [EsAlumnoOMiembroSAE]
```

**No** tocar `AsesoriaViewSet.get_permissions` — `create` sigue con `EsAlumno()`.

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `python manage.py test asesorias.tests.test_api_oferta asesorias.tests.test_api_busqueda -v 2`
Expected: PASS — incluidas las regresiones `test_no_alumno_recibe_403` y `test_asesor_no_puede_usar_la_busqueda` (el asesor no es alumno ni SAE → sigue `403`).

- [ ] **Step 5: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/tests/test_api_oferta.py backend/asesorias/tests/test_api_busqueda.py
git commit -m "[feat][asesorias] oferta y busqueda accesibles al miembro SAE

- OfertaView, AsesoresDeMateriaView y BuscarDisponibilidadView usan EsAlumnoOMiembroSAE
- agendar sigue EsAlumno: el SAE recibe 403 en POST /asesorias/

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: `notas` visibles para el miembro SAE

**Files:**
- Modify: `backend/asesorias/serializers.py` (`AsesoriaSerializer.to_representation`)
- Test: `backend/asesorias/tests/test_api_asesoria.py` (clase `NotasOcultasApiTests`)

**Interfaces:**
- Consumes: `hasattr(user, "perfil_sae")` (Task 1).
- Produces: `AsesoriaSerializer` incluye `notas` si el solicitante es el asesor dueño **o** miembro SAE; las omite para todos los demás (alumno incluido). Lo consume `/admin/asesorias/` (Task 6).

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a la clase `NotasOcultasApiTests` en `backend/asesorias/tests/test_api_asesoria.py`:

```python
    def test_miembro_sae_si_recibe_notas(self):
        from accounts.models import PerfilSAE
        from asesorias.serializers import AsesoriaSerializer
        from rest_framework.test import APIRequestFactory

        sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=sae_user)
        request = APIRequestFactory().get("/")
        request.user = sae_user

        data = AsesoriaSerializer(self.asesoria, context={"request": request}).data

        self.assertIn("notas", data)
        self.assertEqual(data["notas"], "El alumno debe repasar límites.")

    def test_usuario_sin_rol_no_recibe_notas(self):
        from asesorias.serializers import AsesoriaSerializer
        from rest_framework.test import APIRequestFactory

        externo = User.objects.create_user(email="externo@ciencias.unam.mx", password="x")
        request = APIRequestFactory().get("/")
        request.user = externo

        data = AsesoriaSerializer(self.asesoria, context={"request": request}).data

        self.assertNotIn("notas", data)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test asesorias.tests.test_api_asesoria.NotasOcultasApiTests -v 2`
Expected: FAIL — `test_miembro_sae_si_recibe_notas` falla con `AssertionError: 'notas' not found in ...`.

- [ ] **Step 3: Ampliar el gate**

En `backend/asesorias/serializers.py`, reemplazar el cuerpo de `AsesoriaSerializer.to_representation` por:

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
        # ADR 0023: el miembro SAE es casi-administrador del servicio y ve la
        # sesión completa. El alumno sigue excluido (no se reabre ADR 0021).
        es_miembro_sae = hasattr(user, "perfil_sae")
        if not (es_asesor_dueno or es_miembro_sae):
            data.pop("notas", None)
        return data
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `python manage.py test asesorias.tests.test_api_asesoria -v 2`
Expected: PASS — incluidas las regresiones `test_alumno_no_recibe_notas_en_list`, `test_alumno_no_recibe_notas_en_retrieve` y `test_asesor_dueno_si_recibe_notas`.

- [ ] **Step 5: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/tests/test_api_asesoria.py
git commit -m "[feat][asesorias] el miembro SAE ve las notas de la sesion

- AsesoriaSerializer.to_representation: asesor dueno O miembro SAE
- el alumno sigue sin ver notas (regresion cubierta)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 6: `GET /api/asesorias/admin/asesorias/`

**Files:**
- Modify: `backend/asesorias/views.py` (clase `AdminAsesoriasView`)
- Modify: `backend/asesorias/urls.py`
- Test: `backend/asesorias/tests/test_api_admin.py` (crear)

**Interfaces:**
- Consumes: `EsMiembroSAE` (Task 3), `AsesoriaSerializer` con gate de `notas` ampliado (Task 5).
- Produces: `GET /api/asesorias/admin/asesorias/?asesor=&alumno=&semestre=&estado=` → `200` con la lista de `AsesoriaSerializer` (incluye `alumno_nombre`, `asesor_nombre`, `notas`), admin-wide, orden ascendente por `fecha`,`hora_inicio`. `asesor` = `PerfilAsesorAcademico.id`; `alumno` = `PerfilAlumno.id`; ambos lenient (`.isdigit()`). Sin `?semestre`: `fecha >= hoy` y, si tampoco hay `?estado`, `estado="agendada"`. `403` a quien no es SAE, `401` sin autenticar.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/asesorias/tests/test_api_admin.py`:

```python
import datetime

from accounts.models import PerfilAcademico, PerfilAlumno, PerfilSAE, User
from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
from carreras.models import Area, Carrera
from django.utils import timezone
from materias.models import Materia
from rest_framework.test import APITestCase


class AdminAsesoriasApiTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        # Asesor A — registro en el semestre "20262".
        self.asesor_a_user = User.objects.create_user(
            email="asesor-a@ciencias.unam.mx", password="x", first_name="Ana",
        )
        self.asesor_a_user.apellido1 = "López"
        self.asesor_a_user.save()
        PerfilAcademico.objects.create(user=self.asesor_a_user, numero_trabajador="10001")
        self.asesor_a = PerfilAsesorAcademico.objects.create(user=self.asesor_a_user, area=self.area)
        self.registro_a = RegistroAsesor.objects.create(asesor=self.asesor_a, semestre="20262")
        self.registro_a.materias.add(self.materia)
        self.disp_a = Disponibilidad.objects.create(
            registro=self.registro_a, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 4",
        )

        # Asesor B — registro en el semestre "20261".
        self.asesor_b_user = User.objects.create_user(
            email="asesor-b@ciencias.unam.mx", password="x", first_name="Beto",
        )
        PerfilAcademico.objects.create(user=self.asesor_b_user, numero_trabajador="10002")
        self.asesor_b = PerfilAsesorAcademico.objects.create(user=self.asesor_b_user, area=self.area)
        self.registro_b = RegistroAsesor.objects.create(asesor=self.asesor_b, semestre="20261")
        self.registro_b.materias.add(self.materia)
        self.disp_b = Disponibilidad.objects.create(
            registro=self.registro_b, dia_semana=1, hora_inicio=datetime.time(11, 0),
            formato="virtual", liga_virtual="https://meet.example.com/b",
        )

        self.alumno1_user = User.objects.create_user(
            email="alumno1@ciencias.unam.mx", password="x", first_name="Juan",
        )
        self.alumno1 = PerfilAlumno.objects.create(
            user=self.alumno1_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.alumno2_user = User.objects.create_user(
            email="alumno2@ciencias.unam.mx", password="x", first_name="Rosa",
        )
        self.alumno2 = PerfilAlumno.objects.create(
            user=self.alumno2_user, numero_cuenta="312345679", carrera=self.carrera, generacion=2024,
        )

        # Futura agendada: asesor A / alumno 1.
        self.futura_a = Asesoria.objects.create(
            alumno=self.alumno1, disponibilidad=self.disp_a, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy + datetime.timedelta(days=3),
            hora_inicio=datetime.time(10, 0), formato="presencial", ubicacion="Salón 4",
            estado="agendada",
        )
        # Futura agendada: asesor B / alumno 2.
        self.futura_b = Asesoria.objects.create(
            alumno=self.alumno2, disponibilidad=self.disp_b, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy + datetime.timedelta(days=5),
            hora_inicio=datetime.time(11, 0), formato="virtual",
            liga_virtual="https://meet.example.com/b", estado="agendada",
        )
        # Pasada realizada con notas: asesor B / alumno 2 (semestre "20261").
        self.pasada_b = Asesoria.objects.create(
            alumno=self.alumno2, disponibilidad=self.disp_b, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy - datetime.timedelta(days=30),
            hora_inicio=datetime.time(11, 0), formato="virtual",
            liga_virtual="https://meet.example.com/b",
            estado="realizada", asistio=True, notas="Repasar límites.",
        )
        # Futura cancelada: asesor A / alumno 2.
        self.cancelada_a = Asesoria.objects.create(
            alumno=self.alumno2, disponibilidad=self.disp_a, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy + datetime.timedelta(days=10),
            hora_inicio=datetime.time(10, 0), formato="presencial", ubicacion="Salón 4",
            estado="cancelada",
        )

        self.sae_user = User.objects.create_user(email="sae@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_por_defecto_lista_proximas_agendadas_de_todos(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 200)
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_a.id, self.futura_b.id})

    def test_orden_ascendente_por_fecha(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        fechas = [a["fecha"] for a in response.data]
        self.assertEqual(fechas, sorted(fechas))

    def test_incluye_ambos_nombres(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        fila = next(a for a in response.data if a["id"] == self.futura_a.id)
        self.assertEqual(fila["alumno_nombre"], self.alumno1_user.nombre_completo)
        self.assertEqual(fila["asesor_nombre"], self.asesor_a_user.nombre_completo)

    def test_incluye_notas(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?semestre=20261")
        fila = next(a for a in response.data if a["id"] == self.pasada_b.id)
        self.assertEqual(fila["notas"], "Repasar límites.")

    def test_filtra_por_asesor(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesorias/?asesor={self.asesor_a.id}")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_a.id})

    def test_filtra_por_alumno(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesorias/?alumno={self.alumno2.id}")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_b.id})

    def test_filtra_por_semestre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?semestre=20261")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_b.id, self.pasada_b.id})

    def test_filtra_por_estado(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?estado=cancelada")
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.cancelada_a.id})

    def test_semestre_inexistente_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?semestre=19991")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_filtro_no_numerico_se_ignora(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesorias/?asesor=abc&alumno=xyz")
        self.assertEqual(response.status_code, 200)
        ids = {a["id"] for a in response.data}
        self.assertEqual(ids, {self.futura_a.id, self.futura_b.id})

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.alumno1_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 403)

    def test_asesor_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_a_user)
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 403)

    def test_sin_autenticar_recibe_401(self):
        response = self.client.get("/api/asesorias/admin/asesorias/")
        self.assertEqual(response.status_code, 401)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_admin -v 2`
Expected: FAIL — `404` en todos los casos: la ruta `admin/asesorias/` no existe.

- [ ] **Step 3: Implementar `AdminAsesoriasView`**

En `backend/asesorias/views.py`:

1. Añadir `EsMiembroSAE` al import de `.permissions`:

```python
from .permissions import (
    EsAlumno, EsAlumnoOAsesorAcademico, EsAlumnoOMiembroSAE, EsAsesorAcademico, EsMiembroSAE,
    EsDuenoDelRegistro, EsDuenoDeLaAsesoria,
)
```

2. Añadir el import de `timezone` junto a los demás imports de Django:

```python
from django.utils import timezone
```

3. Añadir la clase al final del archivo:

```python
class AdminAsesoriasView(APIView):
    """Todas las sesiones del sistema para el miembro SAE (ADR 0023).

    Deliberadamente separada de AsesoriaViewSet, cuyo queryset está acotado
    al usuario autenticado: mezclar ambas lógicas en una sola clase haría
    que un error de rama expusiera datos de más.
    """

    permission_classes = [EsMiembroSAE]

    def get(self, request):
        asesor_id = request.query_params.get("asesor")
        alumno_id = request.query_params.get("alumno")
        semestre = request.query_params.get("semestre")
        estado = request.query_params.get("estado")

        queryset = Asesoria.objects.select_related(
            "alumno__user", "disponibilidad__registro__asesor__user", "materia"
        )
        # Filtros lenient: un id no numérico se ignora, igual que en
        # BuscarDisponibilidadView. `asesor` es PerfilAsesorAcademico.id.
        if asesor_id and asesor_id.isdigit():
            queryset = queryset.filter(disponibilidad__registro__asesor_id=asesor_id)
        if alumno_id and alumno_id.isdigit():
            queryset = queryset.filter(alumno_id=alumno_id)
        if semestre:
            # Un semestre desconocido devuelve [], no 400 (deuda 0001).
            queryset = queryset.filter(disponibilidad__registro__semestre=semestre)
        if estado:
            queryset = queryset.filter(estado=estado)

        if not semestre:
            # Sin ?semestre el listado es el de "próximas": de hoy en
            # adelante, y agendadas salvo que se pida otro estado.
            queryset = queryset.filter(fecha__gte=timezone.localdate())
            if not estado:
                queryset = queryset.filter(estado="agendada")

        queryset = queryset.order_by("fecha", "hora_inicio")
        return Response(
            AsesoriaSerializer(queryset, many=True, context={"request": request}).data
        )
```

- [ ] **Step 4: Registrar la ruta**

En `backend/asesorias/urls.py`, cambiar el import y añadir el `path` antes de `router.urls`:

```python
from .views import (
    AdminAsesoriasView, AsesoresDeMateriaView, AsesoriaViewSet, BuscarDisponibilidadView,
    DisponibilidadViewSet, OfertaView, RegistroAsesorViewSet,
)

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
    path("oferta/", OfertaView.as_view(), name="oferta"),
    path("oferta/<int:materia_id>/asesores/", AsesoresDeMateriaView.as_view(), name="oferta-asesores"),
    path("admin/asesorias/", AdminAsesoriasView.as_view(), name="admin-asesorias"),
] + router.urls
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_admin -v 2`
Expected: PASS (13 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_admin.py
git commit -m "[feat][asesorias] listado admin de asesorias para el miembro SAE

- GET /api/asesorias/admin/asesorias/?asesor=&alumno=&semestre=&estado= (EsMiembroSAE)
- admin-wide, reusa AsesoriaSerializer (incluye notas), filtros lenient
- sin ?semestre: proximas agendadas desde hoy, orden ascendente

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 7: `GET /api/asesorias/admin/semestres/`

**Files:**
- Modify: `backend/asesorias/views.py` (clase `AdminSemestresView`)
- Modify: `backend/asesorias/urls.py`
- Test: `backend/asesorias/tests/test_api_admin.py` (añadir clase)

**Interfaces:**
- Consumes: `EsMiembroSAE` (Task 3).
- Produces: `GET /api/asesorias/admin/semestres/` → `200` con `["20262", "20261", ...]`: todas las claves de semestre del sistema con al menos una `Asesoria`, sin duplicados, ordenadas descendente. Distinto de `/asesorias/semestres/`, que es por-usuario.

- [ ] **Step 1: Escribir el test que falla**

Añadir al final de `backend/asesorias/tests/test_api_admin.py`:

```python
class AdminSemestresApiTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia = Materia.objects.create(
            clave="1811", nombre="Geometría", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        self.alumno_user = User.objects.create_user(email="alumno-sem@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="313111111", carrera=self.carrera, generacion=2023,
        )

        # Dos asesores distintos, cada uno con su registro en un semestre
        # distinto: ninguno es el usuario que consulta.
        self.disponibilidades = {}
        for indice, (correo, trabajador, semestre, dia) in enumerate(
            [
                ("asesor-sem-a@ciencias.unam.mx", "20001", "20261", 0),
                ("asesor-sem-b@ciencias.unam.mx", "20002", "20262", 1),
            ]
        ):
            user = User.objects.create_user(email=correo, password="x")
            PerfilAcademico.objects.create(user=user, numero_trabajador=trabajador)
            asesor = PerfilAsesorAcademico.objects.create(user=user, area=self.area)
            registro = RegistroAsesor.objects.create(asesor=asesor, semestre=semestre)
            registro.materias.add(self.materia)
            disponibilidad = Disponibilidad.objects.create(
                registro=registro, dia_semana=dia, hora_inicio=datetime.time(9 + indice, 0),
                formato="virtual", liga_virtual=f"https://meet.example.com/{indice}",
            )
            self.disponibilidades[semestre] = disponibilidad
            Asesoria.objects.create(
                alumno=self.alumno, disponibilidad=disponibilidad, materia=self.materia,
                carrera=self.carrera, fecha=self.hoy - datetime.timedelta(days=10 + indice),
                hora_inicio=disponibilidad.hora_inicio, formato="virtual",
                liga_virtual=disponibilidad.liga_virtual, estado="realizada", asistio=True,
            )

        self.sae_user = User.objects.create_user(email="sae-sem@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_lista_todos_los_semestres_del_sistema_descendente(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/semestres/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ["20262", "20261"])

    def test_no_duplica_semestres(self):
        segunda = self.disponibilidades["20261"]
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=segunda, materia=self.materia,
            carrera=self.carrera, fecha=self.hoy - datetime.timedelta(days=17),
            hora_inicio=segunda.hora_inicio, formato="virtual",
            liga_virtual=segunda.liga_virtual, estado="realizada", asistio=True,
        )
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/semestres/")
        self.assertEqual(response.data, ["20262", "20261"])

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/admin/semestres/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_admin.AdminSemestresApiTests -v 2`
Expected: FAIL — `404`: la ruta `admin/semestres/` no existe.

- [ ] **Step 3: Implementar `AdminSemestresView`**

Añadir al final de `backend/asesorias/views.py`:

```python
class AdminSemestresView(APIView):
    """Todos los semestres del sistema con sesiones, de más reciente a más
    antiguo. Alimenta los subtabs de histórico del área SAE; el endpoint
    `asesorias/semestres/` existente sólo cubre los del usuario."""

    permission_classes = [EsMiembroSAE]

    def get(self, request):
        claves = Asesoria.objects.values_list(
            "disponibilidad__registro__semestre", flat=True
        )
        return Response(sorted(set(claves), reverse=True))
```

- [ ] **Step 4: Registrar la ruta**

En `backend/asesorias/urls.py`, añadir `AdminSemestresView` al import y el `path` tras `admin/asesorias/`:

```python
    path("admin/semestres/", AdminSemestresView.as_view(), name="admin-semestres"),
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_admin -v 2`
Expected: PASS (16 tests: 13 de Task 6 + 3 nuevos).

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_admin.py
git commit -m "[feat][asesorias] semestres del sistema para el miembro SAE

- GET /api/asesorias/admin/semestres/ (EsMiembroSAE)
- claves distintas ordenadas descendente, admin-wide

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 8: `semestre_vigente()` + `GET /api/asesorias/admin/asesores/`

**Files:**
- Modify: `backend/asesorias/servicios.py` (`semestre_vigente`)
- Modify: `backend/asesorias/views.py` (clase `AdminAsesoresView`)
- Modify: `backend/asesorias/urls.py`
- Test: `backend/asesorias/tests/test_servicios.py`, `backend/asesorias/tests/test_api_admin.py`

**Interfaces:**
- Produces: `asesorias.servicios.semestre_vigente(hoy: datetime.date | None = None) -> str` → `"YYYY1"` para enero–junio, `"YYYY2"` para julio–diciembre (espejo exacto de `semestreActual` del frontend, `frontend/src/features/asesorias/logica.ts`). Lo consume Task 9.
- Produces: `GET /api/asesorias/admin/asesores/` → `200` con `[{"perfil_id": int, "nombre": str, "area_nombre": str, "activo": bool, "num_materias_semestre_vigente": int}]`, **todos** los asesores (activos e inactivos), ordenados por `nombre`.

- [ ] **Step 1: Escribir los tests que fallan**

Añadir al final de `backend/asesorias/tests/test_servicios.py`:

```python
class SemestreVigenteTests(TestCase):
    def test_enero_a_junio_es_semestre_1(self):
        from asesorias.servicios import semestre_vigente

        self.assertEqual(semestre_vigente(datetime.date(2026, 1, 1)), "20261")
        self.assertEqual(semestre_vigente(datetime.date(2026, 6, 30)), "20261")

    def test_julio_a_diciembre_es_semestre_2(self):
        from asesorias.servicios import semestre_vigente

        self.assertEqual(semestre_vigente(datetime.date(2026, 7, 1)), "20262")
        self.assertEqual(semestre_vigente(datetime.date(2026, 12, 31)), "20262")

    def test_sin_argumento_usa_la_fecha_local(self):
        from django.utils import timezone

        from asesorias.servicios import semestre_vigente

        hoy = timezone.localdate()
        esperado = f"{hoy.year}{'1' if hoy.month <= 6 else '2'}"
        self.assertEqual(semestre_vigente(), esperado)
```

Verificar que `backend/asesorias/tests/test_servicios.py` ya importa `datetime` y `TestCase`; si no, añadir al principio del archivo:

```python
import datetime

from django.test import TestCase
```

Añadir al final de `backend/asesorias/tests/test_api_admin.py`:

```python
class AdminAsesoresApiTests(APITestCase):
    def setUp(self):
        from asesorias.servicios import semestre_vigente

        self.semestre = semestre_vigente()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia1 = Materia.objects.create(
            clave="1821", nombre="Topología", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia2 = Materia.objects.create(
            clave="1822", nombre="Variable Compleja", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        # Asesor activo con 2 materias en el semestre vigente y 1 en otro.
        self.activo_user = User.objects.create_user(
            email="zeta@ciencias.unam.mx", password="x", first_name="Zoe",
        )
        PerfilAcademico.objects.create(user=self.activo_user, numero_trabajador="30001")
        self.asesor_activo = PerfilAsesorAcademico.objects.create(
            user=self.activo_user, area=self.area, activo=True,
        )
        registro_vigente = RegistroAsesor.objects.create(
            asesor=self.asesor_activo, semestre=self.semestre,
        )
        registro_vigente.materias.add(self.materia1, self.materia2)
        registro_viejo = RegistroAsesor.objects.create(asesor=self.asesor_activo, semestre="20191")
        registro_viejo.materias.add(self.materia1)

        # Asesor inactivo sin registro en el semestre vigente.
        self.inactivo_user = User.objects.create_user(
            email="alfa@ciencias.unam.mx", password="x", first_name="Aldo",
        )
        PerfilAcademico.objects.create(user=self.inactivo_user, numero_trabajador="30002")
        self.asesor_inactivo = PerfilAsesorAcademico.objects.create(
            user=self.inactivo_user, area=self.area, activo=False,
        )

        self.sae_user = User.objects.create_user(email="sae-dir@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_lista_todos_los_asesores_ordenados_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        self.assertEqual(response.status_code, 200)
        nombres = [a["nombre"] for a in response.data]
        self.assertEqual(nombres, sorted(nombres))
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_activo.id, self.asesor_inactivo.id})

    def test_incluye_area_y_activo(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_inactivo.id)
        self.assertEqual(fila["area_nombre"], "Matemáticas")
        self.assertFalse(fila["activo"])
        self.assertEqual(fila["nombre"], self.inactivo_user.nombre_completo)

    def test_cuenta_materias_solo_del_semestre_vigente(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_activo.id)
        self.assertEqual(fila["num_materias_semestre_vigente"], 2)

    def test_asesor_sin_registro_vigente_cuenta_cero(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_inactivo.id)
        self.assertEqual(fila["num_materias_semestre_vigente"], 0)

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.activo_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python manage.py test asesorias.tests.test_servicios asesorias.tests.test_api_admin -v 2`
Expected: FAIL — `ImportError: cannot import name 'semestre_vigente' from 'asesorias.servicios'`.

- [ ] **Step 3: Implementar `semestre_vigente()`**

Añadir al final de `backend/asesorias/servicios.py`:

```python
def semestre_vigente(hoy: datetime.date | None = None) -> str:
    """Clave del semestre en curso, formato `YYYYN` (el de RegistroAsesor).

    Espejo de `semestreActual` del frontend: enero–junio -> 1, julio–diciembre
    -> 2. Es una convención de calendario, no un modelo (deuda 0001).
    """
    if hoy is None:
        hoy = timezone.localdate()
    numero = "1" if hoy.month <= 6 else "2"
    return f"{hoy.year}{numero}"
```

- [ ] **Step 4: Implementar `AdminAsesoresView`**

En `backend/asesorias/views.py`:

1. Añadir `PerfilAsesorAcademico` al import de `.models`:

```python
from .models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
```

2. Añadir `semestre_vigente` al import de `.servicios`:

```python
from .servicios import semestre_vigente, ventana_agendable
```

3. Añadir la clase al final del archivo:

```python
class AdminAsesoresView(APIView):
    """Directorio de asesores para el área SAE."""

    permission_classes = [EsMiembroSAE]

    def get(self, request):
        semestre = semestre_vigente()
        asesores = PerfilAsesorAcademico.objects.select_related("user", "area").annotate(
            num_materias_semestre_vigente=Count(
                "registros__materias",
                filter=Q(registros__semestre=semestre),
                distinct=True,
            )
        )
        data = [
            {
                "perfil_id": asesor.id,
                "nombre": asesor.user.nombre_completo,
                "area_nombre": asesor.area.nombre,
                "activo": asesor.activo,
                "num_materias_semestre_vigente": asesor.num_materias_semestre_vigente,
            }
            for asesor in asesores
        ]
        # `nombre_completo` es una propiedad de Python, no una columna: el
        # orden se resuelve aquí y no con order_by.
        data.sort(key=lambda fila: fila["nombre"])
        return Response(data)
```

- [ ] **Step 5: Registrar la ruta**

En `backend/asesorias/urls.py`, añadir `AdminAsesoresView` al import y el `path`:

```python
    path("admin/asesores/", AdminAsesoresView.as_view(), name="admin-asesores"),
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `python manage.py test asesorias.tests.test_servicios asesorias.tests.test_api_admin -v 2`
Expected: PASS (3 tests de servicios + 21 de admin: 13 + 3 + 5).

- [ ] **Step 7: Commit**

```bash
git add backend/asesorias/servicios.py backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_servicios.py backend/asesorias/tests/test_api_admin.py
git commit -m "[feat][asesorias] directorio de asesores para el miembro SAE

- semestre_vigente() en servicios, espejo de semestreActual del frontend
- GET /api/asesorias/admin/asesores/ (EsMiembroSAE) con conteo de materias vigentes

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 9: `GET /api/asesorias/admin/asesores/{perfil_id}/`

**Files:**
- Modify: `backend/asesorias/serializers.py` (`MateriaAdminSerializer`, `DisponibilidadAdminSerializer`, `AsesorDetalleAdminSerializer`)
- Modify: `backend/asesorias/views.py` (clase `AdminAsesorDetalleView`)
- Modify: `backend/asesorias/urls.py`
- Test: `backend/asesorias/tests/test_api_admin.py` (añadir clase)

**Interfaces:**
- Consumes: `EsMiembroSAE` (Task 3), `semestre_vigente()` (Task 8).
- Produces: `GET /api/asesorias/admin/asesores/{perfil_id}/?semestre=` → `200` con `{"perfil_id", "nombre", "area_nombre", "activo", "semestre", "materias": [{"id","clave","nombre"}], "disponibilidades": [{"id","dia_semana","hora_inicio","hora_fin","formato","ubicacion","liga_virtual","activa"}]}`. Sin `?semestre` usa `semestre_vigente()`. Sin registro en ese semestre: ambas listas vacías. `perfil_id` inexistente → `404`.

- [ ] **Step 1: Escribir el test que falla**

Añadir al final de `backend/asesorias/tests/test_api_admin.py`:

```python
class AdminAsesorDetalleApiTests(APITestCase):
    def setUp(self):
        from asesorias.servicios import semestre_vigente

        self.semestre = semestre_vigente()
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")
        self.materia_vigente = Materia.objects.create(
            clave="1831", nombre="Cálculo III", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_vieja = Materia.objects.create(
            clave="1832", nombre="Ecuaciones Diferenciales", carrera=self.carrera, nivel=1,
            plan=2006, habilitada_asesorias=True,
        )

        self.asesor_user = User.objects.create_user(
            email="detalle@ciencias.unam.mx", password="x", first_name="Ana",
        )
        self.asesor_user.apellido1 = "López"
        self.asesor_user.save()
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="40001")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)

        self.registro_vigente = RegistroAsesor.objects.create(
            asesor=self.asesor, semestre=self.semestre,
        )
        self.registro_vigente.materias.add(self.materia_vigente)
        self.disp_vigente = Disponibilidad.objects.create(
            registro=self.registro_vigente, dia_semana=1, hora_inicio=datetime.time(10, 0),
            formato="presencial", ubicacion="Salón 4",
        )

        self.registro_viejo = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20191")
        self.registro_viejo.materias.add(self.materia_vieja)
        self.disp_vieja = Disponibilidad.objects.create(
            registro=self.registro_viejo, dia_semana=3, hora_inicio=datetime.time(16, 30),
            formato="virtual", liga_virtual="https://meet.example.com/viejo",
        )

        self.sae_user = User.objects.create_user(email="sae-det@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_detalle_por_defecto_usa_el_semestre_vigente(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["perfil_id"], self.asesor.id)
        self.assertEqual(response.data["nombre"], "Ana López")
        self.assertEqual(response.data["area_nombre"], "Matemáticas")
        self.assertTrue(response.data["activo"])
        self.assertEqual(response.data["semestre"], self.semestre)
        self.assertEqual(
            [m["clave"] for m in response.data["materias"]], ["1831"]
        )

    def test_materias_incluyen_id_clave_y_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(
            response.data["materias"][0],
            {"id": self.materia_vigente.id, "clave": "1831", "nombre": "Cálculo III"},
        )

    def test_disponibilidades_incluyen_hora_fin_y_formato(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(
            response.data["disponibilidades"][0],
            {
                "id": self.disp_vigente.id,
                "dia_semana": 1,
                "hora_inicio": "10:00:00",
                "hora_fin": "10:30:00",
                "formato": "presencial",
                "ubicacion": "Salón 4",
                "liga_virtual": "",
                "activa": True,
            },
        )

    def test_semestre_explicito_devuelve_ese_registro(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(
            f"/api/asesorias/admin/asesores/{self.asesor.id}/?semestre=20191"
        )
        self.assertEqual(response.data["semestre"], "20191")
        self.assertEqual([m["clave"] for m in response.data["materias"]], ["1832"])
        self.assertEqual(
            [d["id"] for d in response.data["disponibilidades"]], [self.disp_vieja.id]
        )

    def test_semestre_sin_registro_devuelve_listas_vacias(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get(
            f"/api/asesorias/admin/asesores/{self.asesor.id}/?semestre=19991"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["semestre"], "19991")
        self.assertEqual(response.data["materias"], [])
        self.assertEqual(response.data["disponibilidades"], [])

    def test_perfil_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/999999/")
        self.assertEqual(response.status_code, 404)

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/admin/asesores/{self.asesor.id}/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_admin.AdminAsesorDetalleApiTests -v 2`
Expected: FAIL — `404` en todos los casos salvo `test_perfil_inexistente_devuelve_404`: la ruta `admin/asesores/{id}/` no existe.

- [ ] **Step 3: Añadir los serializers del detalle**

Añadir al final de `backend/asesorias/serializers.py`:

```python
class MateriaAdminSerializer(serializers.Serializer):
    """Materia del registro de un asesor, vista SAE de solo lectura."""

    id = serializers.IntegerField()
    clave = serializers.CharField()
    nombre = serializers.CharField()


class DisponibilidadAdminSerializer(serializers.Serializer):
    """Bloque de disponibilidad con `hora_fin` calculada, vista SAE.

    No reusa DisponibilidadSerializer: ese expone `registro` y valida
    escritura; aquí sólo se lee y se necesita `hora_fin` (propiedad del
    modelo, no columna).
    """

    id = serializers.IntegerField()
    dia_semana = serializers.IntegerField()
    hora_inicio = serializers.TimeField()
    hora_fin = serializers.TimeField()
    formato = serializers.CharField()
    ubicacion = serializers.CharField(allow_blank=True)
    liga_virtual = serializers.CharField(allow_blank=True)
    activa = serializers.BooleanField()


class AsesorDetalleAdminSerializer(serializers.Serializer):
    perfil_id = serializers.IntegerField()
    nombre = serializers.CharField()
    area_nombre = serializers.CharField()
    activo = serializers.BooleanField()
    semestre = serializers.CharField()
    materias = MateriaAdminSerializer(many=True)
    disponibilidades = DisponibilidadAdminSerializer(many=True)
```

- [ ] **Step 4: Implementar `AdminAsesorDetalleView`**

En `backend/asesorias/views.py`:

1. Añadir los serializers al import de `.serializers`:

```python
from .serializers import (
    AsesorDetalleAdminSerializer, MateriaDelRegistroSerializer, AsesoriaSerializer, CancelarSerializer,
    DesactivarDisponibilidadSerializer, DisponibilidadSerializer, MarcarAsistenciaSerializer,
    NotasSerializer, RegistroAsesorSerializer, ResultadoBusquedaSerializer, SesionFuturaSerializer,
)
```

2. Añadir la clase al final del archivo:

```python
class AdminAsesorDetalleView(APIView):
    """Materias y disponibilidad de un asesor en un semestre, solo lectura.

    La disponibilidad es la ACTUAL del registro pedido: el modelo no versiona
    el estado activa/inactiva en el tiempo (fuera de alcance, deuda 0005).
    """

    permission_classes = [EsMiembroSAE]

    def get(self, request, perfil_id):
        asesor = get_object_or_404(
            PerfilAsesorAcademico.objects.select_related("user", "area"), pk=perfil_id
        )
        semestre = request.query_params.get("semestre") or semestre_vigente()
        registro = (
            RegistroAsesor.objects.filter(asesor=asesor, semestre=semestre)
            .prefetch_related("materias", "disponibilidades")
            .first()
        )
        materias = registro.materias.all().order_by("clave") if registro else []
        disponibilidades = (
            registro.disponibilidades.all().order_by("dia_semana", "hora_inicio")
            if registro
            else []
        )
        payload = {
            "perfil_id": asesor.id,
            "nombre": asesor.user.nombre_completo,
            "area_nombre": asesor.area.nombre,
            "activo": asesor.activo,
            "semestre": semestre,
            "materias": materias,
            "disponibilidades": disponibilidades,
        }
        return Response(AsesorDetalleAdminSerializer(payload).data)
```

- [ ] **Step 5: Registrar la ruta**

En `backend/asesorias/urls.py`, añadir `AdminAsesorDetalleView` al import y el `path` **después** de `admin/asesores/`:

```python
    path(
        "admin/asesores/<int:perfil_id>/",
        AdminAsesorDetalleView.as_view(),
        name="admin-asesor-detalle",
    ),
```

- [ ] **Step 6: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_admin -v 2`
Expected: PASS (28 tests: 21 previos + 7 nuevos).

- [ ] **Step 7: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_admin.py
git commit -m "[feat][asesorias] detalle read-only de asesor para el miembro SAE

- GET /api/asesorias/admin/asesores/{perfil_id}/?semestre= (EsMiembroSAE)
- materias y disponibilidad del registro del semestre pedido (default vigente)
- 404 si el perfil no existe; listas vacias si no hay registro

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 10: `GET /api/asesorias/admin/alumnos/`

**Files:**
- Modify: `backend/asesorias/views.py` (clase `AdminAlumnosView` + constante `LIMITE_AUTOCOMPLETAR_ALUMNOS`)
- Modify: `backend/asesorias/urls.py`
- Test: `backend/asesorias/tests/test_api_admin.py` (añadir clase)

**Interfaces:**
- Consumes: `EsMiembroSAE` (Task 3), `accounts.models.PerfilAlumno`.
- Produces: `GET /api/asesorias/admin/alumnos/?buscar=` → `200` con `[{"perfil_id": int, "nombre": str, "numero_cuenta": str}]`, máximo `LIMITE_AUTOCOMPLETAR_ALUMNOS = 20` filas. `?buscar=` hace `icontains` sobre `numero_cuenta`, `user__first_name`, `user__apellido1` y `user__apellido2` (unidos por `OR`); `nombre_completo` es una propiedad y no se puede filtrar directamente. Sin `?buscar` devuelve las primeras 20 filas.

- [ ] **Step 1: Escribir el test que falla**

Añadir al final de `backend/asesorias/tests/test_api_admin.py`:

```python
class AdminAlumnosApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.get(nombre="Matemáticas")
        self.carrera = Carrera.objects.get(nombre="Actuaría")

        self.juan_user = User.objects.create_user(
            email="juan@ciencias.unam.mx", password="x", first_name="Juan",
        )
        self.juan_user.apellido1 = "Pérez"
        self.juan_user.save()
        self.juan = PerfilAlumno.objects.create(
            user=self.juan_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

        self.rosa_user = User.objects.create_user(
            email="rosa@ciencias.unam.mx", password="x", first_name="Rosa",
        )
        self.rosa_user.apellido1 = "Gómez"
        self.rosa_user.save()
        self.rosa = PerfilAlumno.objects.create(
            user=self.rosa_user, numero_cuenta="420000001", carrera=self.carrera, generacion=2024,
        )

        self.sae_user = User.objects.create_user(email="sae-alu@ciencias.unam.mx", password="x")
        PerfilSAE.objects.create(user=self.sae_user)

    def test_busca_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=jua")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [{"perfil_id": self.juan.id, "nombre": "Juan Pérez", "numero_cuenta": "312345678"}],
        )

    def test_busca_por_apellido(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=góm")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.rosa.id})

    def test_busca_por_numero_de_cuenta(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=4200")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.rosa.id})

    def test_busqueda_sin_coincidencias_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=zzzzz")
        self.assertEqual(response.data, [])

    def test_respeta_el_limite_de_resultados(self):
        from asesorias.views import LIMITE_AUTOCOMPLETAR_ALUMNOS

        for indice in range(LIMITE_AUTOCOMPLETAR_ALUMNOS + 5):
            user = User.objects.create_user(
                email=f"masivo{indice}@ciencias.unam.mx", password="x", first_name="Masivo",
            )
            PerfilAlumno.objects.create(
                user=user, numero_cuenta=f"5000000{indice:02d}", carrera=self.carrera,
                generacion=2025,
            )
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=masivo")
        self.assertEqual(len(response.data), LIMITE_AUTOCOMPLETAR_ALUMNOS)

    def test_no_sae_recibe_403(self):
        self.client.force_authenticate(user=self.juan_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=jua")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python manage.py test asesorias.tests.test_api_admin.AdminAlumnosApiTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'LIMITE_AUTOCOMPLETAR_ALUMNOS' from 'asesorias.views'` y `404` en el resto.

- [ ] **Step 3: Implementar `AdminAlumnosView`**

En `backend/asesorias/views.py`:

1. Añadir el import de `PerfilAlumno` junto a los demás imports de apps:

```python
from accounts.models import PerfilAlumno
```

2. Añadir la constante y la clase al final del archivo:

```python
# Autocompletar, no listado: el frontend usa esto para resolver un alumno por
# nombre o cuenta. Sin paginación en esta fase (deuda 0006), el corte fijo
# evita devolver el padrón completo.
LIMITE_AUTOCOMPLETAR_ALUMNOS = 20


class AdminAlumnosView(APIView):
    """Autocompletar de alumnos para el filtro `?alumno=` del área SAE."""

    permission_classes = [EsMiembroSAE]

    def get(self, request):
        buscar = request.query_params.get("buscar")
        alumnos = PerfilAlumno.objects.select_related("user")
        if buscar:
            # `nombre_completo` es una propiedad de Python: se busca sobre las
            # columnas que la componen.
            alumnos = alumnos.filter(
                Q(numero_cuenta__icontains=buscar)
                | Q(user__first_name__icontains=buscar)
                | Q(user__apellido1__icontains=buscar)
                | Q(user__apellido2__icontains=buscar)
            )
        alumnos = alumnos.order_by("user__first_name", "user__apellido1", "user__apellido2")
        data = [
            {
                "perfil_id": alumno.id,
                "nombre": alumno.user.nombre_completo,
                "numero_cuenta": alumno.numero_cuenta,
            }
            for alumno in alumnos[:LIMITE_AUTOCOMPLETAR_ALUMNOS]
        ]
        return Response(data)
```

- [ ] **Step 4: Registrar la ruta**

En `backend/asesorias/urls.py`, añadir `AdminAlumnosView` al import y el `path`. El bloque completo de `urlpatterns` queda:

```python
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminAlumnosView, AdminAsesorDetalleView, AdminAsesoresView, AdminAsesoriasView,
    AdminSemestresView, AsesoresDeMateriaView, AsesoriaViewSet, BuscarDisponibilidadView,
    DisponibilidadViewSet, OfertaView, RegistroAsesorViewSet,
)

router = DefaultRouter()
router.register("registros", RegistroAsesorViewSet, basename="registro-asesor")
router.register("disponibilidades", DisponibilidadViewSet, basename="disponibilidad")
router.register("asesorias", AsesoriaViewSet, basename="asesoria")

urlpatterns = [
    path("disponibilidad/buscar/", BuscarDisponibilidadView.as_view(), name="disponibilidad-buscar"),
    path("oferta/", OfertaView.as_view(), name="oferta"),
    path("oferta/<int:materia_id>/asesores/", AsesoresDeMateriaView.as_view(), name="oferta-asesores"),
    path("admin/asesorias/", AdminAsesoriasView.as_view(), name="admin-asesorias"),
    path("admin/semestres/", AdminSemestresView.as_view(), name="admin-semestres"),
    path("admin/asesores/", AdminAsesoresView.as_view(), name="admin-asesores"),
    path(
        "admin/asesores/<int:perfil_id>/",
        AdminAsesorDetalleView.as_view(),
        name="admin-asesor-detalle",
    ),
    path("admin/alumnos/", AdminAlumnosView.as_view(), name="admin-alumnos"),
] + router.urls
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `python manage.py test asesorias.tests.test_api_admin -v 2`
Expected: PASS (34 tests: 28 previos + 6 nuevos).

- [ ] **Step 6: Correr toda la suite**

Run: `python manage.py test -v 2`
Expected: PASS — sin regresiones en `accounts`, `asesorias`, `carreras`, `materias`.

- [ ] **Step 7: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/urls.py backend/asesorias/tests/test_api_admin.py
git commit -m "[feat][asesorias] autocompletar de alumnos para el miembro SAE

- GET /api/asesorias/admin/alumnos/?buscar= (EsMiembroSAE)
- icontains sobre numero_cuenta y nombre/apellidos, limite fijo de 20 filas

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Self-Review

**Spec coverage** (contra `2026-08-09-asesorias-sae-admin-api-design.md`):

| Requisito de la spec | Task |
|---|---|
| Dec. 1 — `PerfilSAE` en `accounts`, `user` + `activo`, Django admin, deuda 0014 | 1 |
| Dec. 2 — rol `'sae'` en `get_roles` | 2 |
| Dec. 3 — `EsMiembroSAE` y `EsAlumnoOMiembroSAE` | 3 |
| Dec. 4 — oferta / asesores-por-materia / búsqueda a `EsAlumnoOMiembroSAE`; `POST` sigue `EsAlumno` | 4 |
| Dec. 5 — `/admin/asesorias/` | 6 |
| Dec. 5 — `/admin/semestres/` | 7 |
| Dec. 5 — `/admin/asesores/` | 8 |
| Dec. 5 — `/admin/asesores/{perfil_id}/` | 9 |
| Dec. 5 — `/admin/alumnos/` | 10 |
| Dec. 6 — `notas` visibles al SAE, alumno excluido | 5 |
| Dec. 7 — solo lectura, sin paginación | Global Constraints (ningún task define método de escritura ni paginación) |
| Dec. 8 — filtro `asesor` por `PerfilAsesorAcademico.id`, lenient | 6 (`test_filtra_por_asesor`, `test_filtro_no_numerico_se_ignora`) |

**Error handling** (tabla de la spec): `401` sin autenticación → Task 6 `test_sin_autenticar_recibe_401`. `403` no-SAE en `/admin/*` → Tasks 6,7,8,9,10 (`test_no_sae_recibe_403`, `test_asesor_recibe_403`). `403` no-alumno-no-SAE en oferta/búsqueda → Task 4 (regresiones `test_no_alumno_recibe_403`, `test_asesor_no_puede_usar_la_busqueda`). `403` SAE en `POST /asesorias/` → Task 4 `test_miembro_sae_no_puede_agendar`. `404` `perfil_id` inexistente → Task 9 `test_perfil_inexistente_devuelve_404`. Filtro no numérico ignorado → Task 6 `test_filtro_no_numerico_se_ignora`. `?semestre=` inexistente → `[]` → Task 6 `test_semestre_inexistente_devuelve_lista_vacia` (y Task 9 `test_semestre_sin_registro_devuelve_listas_vacias`).

**Testing** (sección de la spec): permiso SAE → Tasks 3,6-10; roles → Task 2; endpoints compartidos ampliados → Task 4; listado admin de distintos asesores/alumnos y sus 4 filtros → Task 6; notas al SAE + regresión del alumno → Task 5; semestres admin-wide → Task 7; directorio + detalle + 404 → Tasks 8,9; autocompletar alumno por nombre y cuenta con límite → Task 10.

**Placeholder scan:** sin "TBD", "similar a", "…", ni pasos sin código. Todos los tests y las implementaciones van completos.

**Consistencia de nombres:** `PerfilSAE` / `perfil_sae` (Tasks 1,2,3,5); `EsMiembroSAE` / `EsAlumnoOMiembroSAE` (Tasks 3,4,6-10); `semestre_vigente()` (Tasks 8,9); `AdminAsesoriasView`, `AdminSemestresView`, `AdminAsesoresView`, `AdminAsesorDetalleView`, `AdminAlumnosView` idénticos entre `views.py`, `urls.py` y los imports; claves de respuesta `perfil_id`, `nombre`, `area_nombre`, `activo`, `num_materias_semestre_vigente`, `semestre`, `materias`, `disponibilidades`, `numero_cuenta` idénticas a la spec y a la spec de frontend gemela.

**Resoluciones spec ↔ código** (aplicadas en el plan):
1. **Formato de semestre.** La spec ejemplifica `"2026-2"`; el modelo real es `CharField(max_length=5)` con claves `"20262"` (ver `RegistroAsesor.semestre` y `semestreActual` del frontend). El plan usa el formato real.
2. **`?estado=` vs. el default de próximas.** La spec dice "sin `?semestre` → próximas agendadas (por defecto `estado=agendada`, `fecha >= hoy`)". Se implementa literalmente: sin `?semestre` siempre aplica `fecha >= hoy`, y `estado="agendada"` sólo si no se pasó `?estado`.
3. **`semestre vigente` no existía en backend.** Se añade `semestre_vigente()` en `asesorias/servicios.py` (Task 8), espejo del `semestreActual` del frontend, en vez de duplicar la convención en dos views.
4. **Búsqueda por "nombre" en `/admin/alumnos/`.** `nombre_completo` es una propiedad de `User`, no una columna: el `icontains` se aplica sobre `first_name`, `apellido1` y `apellido2` unidos por `OR`.
5. **Límite del autocompletar.** La spec pide "límite fijo" sin número: se fija `LIMITE_AUTOCOMPLETAR_ALUMNOS = 20`, exportado desde `asesorias/views.py` para que el test lo consuma.
6. **`hora_fin` del detalle de asesor.** Es una `@property` de `Disponibilidad`, no columna; se expone con `DisponibilidadAdminSerializer` (serializer plano nuevo) en vez de reusar `DisponibilidadSerializer`, que expone `registro` y valida escritura.
