# Plan — Resolver la deuda 0011: doble rol (alumno + asesor) en Asesorías

**Deuda que cierra:** [0011 — Un usuario con doble rol solo ve el lado de alumno](../../technical-debt/0011-doble-rol-alumno-asesor-solo-ve-alumno.md)
**ADR relacionada:** [0017 — Asesorías académicas (API)](../../decisions/0017-asesorias-academicas-api.md)
**Rama sugerida:** `dev-backend` (o una rama propia que forkee de ahí)

## Contexto

`PerfilAlumno` y `PerfilAsesorAcademico` son ambos `OneToOneField` a `User`; nada
impide que un `User` tenga los dos. Hoy el backend de Asesorías asume mono-rol en
dos puntos, ambos con precedencia **alumno primero**:

1. `AsesoriaViewSet.get_queryset` (`backend/asesorias/views.py:169-174`) —
   `if perfil_alumno: filter(alumno=…) elif perfil_asesor_academico: filter(asesor=…) else none()`.
   Un usuario con doble rol nunca entra al `elif`: sus sesiones como asesor no
   aparecen en `GET /api/asesorias/asesorias/` ni en `.../semestres/`.
2. `EsDuenoDeLaAsesoria.has_object_permission` (`backend/asesorias/permissions.py:36-41`) —
   `if perfil_alumno: return obj.alumno_id == …` (return inmediato). Si el usuario
   es el asesor de la sesión pero no su alumno, devuelve `False` → `403` en
   `cancelar`/`marcar_asistencia`/`notas`, sin evaluar la rama de asesor.

La Task 3 del plan de backend 2026-08-04 ya expone `roles` como **lista**, así que
el contrato de la API promete multi-rol pero el filtrado no lo cumple.

## Decisión de diseño

- **Permiso:** el usuario es dueño de la asesoría si es su alumno **o** su asesor.
  Se cambia el `if … return` en cadena por una comprobación con `or` que evalúa
  ambas ramas (una `and` por rama para no romper cuando falta un perfil).
- **Listado:** para un usuario con doble rol se devuelve la **unión** de sus
  sesiones (donde es alumno **o** donde es asesor), con `Q(alumno=…) | Q(disponibilidad__registro__asesor__user=…)`.
  No se introduce un `?rol=` selector: el frontend ya distingue cada lado con
  `alumno_nombre`/`asesor_nombre` del serializer, y un switch de perspectiva es
  una decisión de UI que no corresponde a este arreglo de backend.
- **Se preservan intactos:** la rama temprana de acciones que devuelve `base` sin
  filtrar por dueño (para que el 403 del ADR 0017 lo dé `EsDuenoDeLaAsesoria`, no
  un 404), los `select_related`, y el filtro `?semestre=` (que se aplica sobre la
  unión).

## Global Constraints

- Sin migraciones: no hay cambios de esquema.
- Sin dependencias ni variables de entorno nuevas.
- El proyecto no usa `django-filter`; el filtrado es manual con el ORM, igual que
  el código actual.
- Los errores de validación siguen el patrón vigente (no aplica aquí: no se agregan
  validaciones nuevas).
- Commits `[type][scope] resumen` + cuerpo + `Signed-off-by`, atómicos.
- No se toca `frontend/`.
- Toda regresión se descubre corriendo la suite completa de `asesorias`.

---

## Task 1: `EsDuenoDeLaAsesoria` reconoce ambos roles

**Files:**
- Modify: `backend/asesorias/permissions.py`
- Modify: `backend/asesorias/tests/test_permissions.py`

- [ ] **Step 1 (RED):** En `test_permissions.py`, dentro de `PermissionsTests` (o
  una clase nueva `EsDuenoDeLaAsesoriaDobleRolTests(TestCase)` si el setUp lo pide),
  agregar tests que construyan un `User` con **ambos** perfiles (`PerfilAlumno` y
  `PerfilAsesorAcademico`) y una `Asesoria` donde ese usuario es el **asesor** (no
  el alumno). Casos:
  - `has_object_permission` es `True` cuando el usuario es el asesor dueño aunque
    también tenga `perfil_alumno` y no sea el alumno de la sesión. **(hoy falla:
    devuelve `False`)**
  - `has_object_permission` sigue siendo `True` cuando el usuario es el alumno de
    la sesión (no regresión).
  - `has_object_permission` es `False` cuando el usuario con doble rol no es ni el
    alumno ni el asesor de esa sesión.
  Correr solo estos tests y confirmar que el primero falla como se espera.

- [ ] **Step 2 (GREEN):** Reescribir `EsDuenoDeLaAsesoria.has_object_permission`
  para evaluar ambas ramas con `or` en vez de `if … return` en cadena:

  ```python
  def has_object_permission(self, request, view, obj):
      user = request.user
      es_alumno_dueno = (
          hasattr(user, "perfil_alumno")
          and obj.alumno_id == user.perfil_alumno.id
      )
      es_asesor_dueno = (
          hasattr(user, "perfil_asesor_academico")
          and obj.disponibilidad.registro.asesor.user_id == user.id
      )
      return es_alumno_dueno or es_asesor_dueno
  ```

- [ ] **Step 3 (GREEN):** Correr `test_permissions.py` completo — todos verdes,
  incluidos los tests pre-existentes de las otras permission classes.

- [ ] **Step 4:** Commit.
  `[fix][backend] EsDuenoDeLaAsesoria reconoce dueño alumno o asesor (doble rol)`

---

## Task 2: `get_queryset` devuelve la unión para el usuario con doble rol

**Files:**
- Modify: `backend/asesorias/views.py`
- Modify: `backend/asesorias/tests/test_api_asesoria.py`

- [ ] **Step 1 (RED):** En `test_api_asesoria.py`, agregar
  `DobleRolListadoApiTests(AsesoriaApiTestsBase)`. En su `setUp` (llamando a
  `super().setUp()`), promover a `self.asesor_user` a también-alumno creando un
  `PerfilAlumno` para él, y crear dos asesorías: una donde es **alumno** y otra
  donde es **asesor** (esta última ya la sostiene `self.disponibilidad`). Tests:
  - `GET /api/asesorias/asesorias/` autenticado como el usuario de doble rol
    devuelve **ambas** sesiones. **(hoy falla: solo devuelve la de alumno)**
  - `GET /api/asesorias/asesorias/semestres/` incluye los semestres de ambos lados.
  - No regresión: un usuario solo-alumno sigue viendo solo lo suyo, y un usuario
    solo-asesor sigue viendo solo lo suyo (pueden reusarse las clases existentes;
    si ya están cubiertos, no duplicar).
  Confirmar el fallo del primer test.

- [ ] **Step 2 (GREEN):** Reescribir la resolución de rol en `get_queryset`
  preservando todo lo demás (rama de acciones, `select_related`, filtro
  `?semestre=`). Sustituir el bloque `if/elif/else` por una construcción con `Q`:

  ```python
  from django.db.models import Q  # al inicio del archivo, si no está ya

  condiciones = Q()
  if hasattr(user, "perfil_alumno"):
      condiciones |= Q(alumno=user.perfil_alumno)
  if hasattr(user, "perfil_asesor_academico"):
      condiciones |= Q(disponibilidad__registro__asesor__user=user)
  if not condiciones:
      return Asesoria.objects.none()
  queryset = base.filter(condiciones)
  ```

  El resto del método (bloque `if self.action == "list": … semestre …` y el
  `return queryset`) queda igual.

- [ ] **Step 3 (GREEN):** Correr `test_api_asesoria.py` completo. Verificar que el
  `assertNumQueries` de `NombresEnAsesoriaApiTests`/`ListarAsesoriaApiTests` sigue
  en verde — la unión no debe reintroducir N+1 (los `select_related` se conservan).
  Si un `assertNumQueries` cambia de valor legítimamente por el `OR`, ajustarlo con
  un comentario que explique el nuevo conteo; si sube de forma inesperada, es señal
  de un `select_related` perdido.

- [ ] **Step 4:** Commit.
  `[fix][backend] listar asesorias como union para usuarios con doble rol`

---

## Task 3: Cerrar la deuda 0011 y anotar la ADR 0017

**Files:**
- Modify: `docs/technical-debt/0011-doble-rol-alumno-asesor-solo-ve-alumno.md`
- Modify: `docs/technical-debt/README.md`
- Modify: `docs/decisions/0017-asesorias-academicas-api.md`
- Modify: `docs/development/api-frontend.md`

- [ ] **Step 1:** En `0011-…md`, cambiar `**Estado:** Activa` por
  `**Estado:** Resuelta — <fecha> (commits de este plan)` y agregar una sección
  `## Cómo se resolvió` describiendo el `or` en el permiso y la unión con `Q` en
  `get_queryset`.

- [ ] **Step 2:** En `docs/technical-debt/README.md`, mover la 0011 de `### Activa`
  a `### Resuelta`.

- [ ] **Step 3:** En el `## Changelog` de la ADR 0017, agregar una entrada fechada:
  el filtrado de `AsesoriaViewSet` y `EsDuenoDeLaAsesoria` dejan de asumir un solo
  rol por usuario; un `User` con perfil de alumno y de asesor ve y gestiona ambos
  lados (unión en el listado, `or` en el permiso de dueño). Sin cambios de esquema.

- [ ] **Step 4:** En `docs/development/api-frontend.md`, agregar una nota breve en
  la sección de listado de asesorías: para un usuario con doble rol, el listado
  devuelve la unión de sus sesiones como alumno y como asesor; cada fila se
  distingue por `alumno_nombre`/`asesor_nombre`.

- [ ] **Step 5:** Correr la suite completa de `backend` (`uv run manage.py test`).
  PASS obligatorio antes de commitear.

- [ ] **Step 6:** Commit.
  `[docs] cerrar deuda 0011 (doble rol en asesorias) y anotar ADR 0017`

---

## Self-Review

**Cobertura de requisitos**

| Requisito | Task |
|---|---|
| Usuario con doble rol ve sus sesiones de asesor en el listado | 2 |
| Usuario con doble rol puede cancelar/marcar/notas sus sesiones de asesor | 1 |
| No regresión para usuarios mono-rol (alumno o asesor) | 1, 2 |
| Se preserva el 403 del ADR 0017 (rama de acciones sin filtro de dueño) | 2 (intacta) |
| Se preservan los `select_related` (sin N+1) | 2 (Step 3) |
| Se preserva el filtro `?semestre=` sobre la unión | 2 (intacta) |
| Deuda 0011 cerrada y ADR 0017 anotada | 3 |

**Fuera de alcance a propósito:** el switch de perspectiva "actuar como alumno /
como asesor" en la UI (decisión de frontend); un `?rol=` en la API; el resto de las
permission classes (`EsAlumno`, `EsAsesorAcademico`, `EsAlumnoOAsesorAcademico`)
que son chequeos de existencia de perfil y no de doble rol.

**Riesgo principal:** que la unión con `OR` cambie el plan de consulta y algún
`assertNumQueries` existente. Mitigado en la Task 2, Step 3, que lo verifica
explícitamente y da el criterio para distinguir un ajuste legítimo de una regresión
de N+1.
