# Usuarios reales — Home por rol, historia académica y autoservicio de asesor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preparar Atenea para usuarios reales: historia académica multi-carrera del alumno, periodo académico con fechas y ventana de registro, autoservicio de asesor, carga masiva de alumnos y una Home que solo muestra servicios que existen de verdad.

**Architecture:** Una app nueva de Django (`academico`) para el calendario (`PeriodoAcademico` + la heurística `semestre_vigente`), un modelo nuevo en `accounts` (`HistoriaAcademica`) que reemplaza `PerfilAlumno.carrera`/`generacion`, dos endpoints de autoservicio en `asesorias`, un management command de carga masiva, y un frontend que deja de pintar mocks y gatea sus tiles por rol.

**Tech Stack:** Django 6 + DRF (backend, `uv`), React 19 + TypeScript + Vite + TanStack Query (frontend, `vitest`), PostgreSQL 16.

**Spec:** [`docs/superpowers/specs/2026-08-15-usuarios-reales-asesorias-design.md`](../specs/2026-08-15-usuarios-reales-asesorias-design.md)

---

## Global Constraints

- **Formato de semestre: `"20271"`** — `CharField(max_length=5)`, `AAAAN`. Nunca `"2027-1"`.
- **Heurística de semestre (la corregida en `1533d53`)**: enero–junio → `N=2` con el **año en curso**; julio–diciembre → `N=1` con el **año siguiente**. Ejemplos canónicos: `2026-08-01 → "20271"`, `2027-03-15 → "20272"`. La versión que hoy vive en `backend/asesorias/servicios.py::semestre_vigente` es la **vieja** y está mal — esta plan la corrige (Task 8).
- **Patrón PerfilX de [ADR 0012](../../decisions/0012-perfiles-identidad-roles.md):** el rol se deriva de que el perfil exista (`hasattr(user, "perfil_x")`), nunca de un Group de Django ni de `activo`.
- **`User.email` sigue siendo la única llave de autenticación** ([ADR 0003](../../decisions/0003-google-oauth-allauth-jwt.md), [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md)). `correos_alternos` **no** participa en el login ni en la resolución de cuentas.
- **`Asesoria.carrera` es un snapshot independiente** ([ADR 0021](../../decisions/0021-asesorias-alumno-api.md)) y sigue viniendo **explícito** en el payload de agendar. El backend no infiere la carrera cuando el alumno tiene más de una.
- **Sin paginación** en los listados nuevos → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md). No añadir `pagination_class`.
- **Filtrado lenient por query param**, patrón de `BuscarDisponibilidadView`: un id no numérico se ignora con `.isdigit()`, no da 400.
- **No se reabren** [ADR 0016](../../decisions/0016-asesorias-academicas.md) ni [ADR 0017](../../decisions/0017-asesorias-academicas-api.md): `RegistroAsesor.agregar_materia`, `Disponibilidad`, la ventana agendable (semana en curso + siguiente) y los permisos existentes no cambian de semántica.
- **`nombre_completo`** es una propiedad de Python de `accounts.User`, no una columna: no se puede `order_by`/`filter` sobre ella.
- **Comando de tests backend:** desde `backend/`, `uv run manage.py test <ruta> -v 2` (requiere Postgres; `docker compose -f docker-compose.dev.yml up -d postgres redis` lo levanta). Alternativa sin Postgres local: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test <ruta> -v 2`.
- **Comando de tests frontend:** desde `frontend/`, `npx vitest run <ruta>`. Lint: `npm run lint`. Typecheck: `npx tsc -b`.
- **Commits:** formato `[type][scope] resumen` + lista de bullets + `Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>` (usar `git commit -s` con `user.email` configurado, o escribir el trailer a mano). Ver [`docs/development/commit-conventions.md`](../../development/commit-conventions.md).
- **Dos STOP obligatorios** (Task 13 y Task 17): son tareas que **se detienen y preguntan a Héctor**. Está prohibido inventar el contenido que piden y seguir de largo.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `backend/accounts/models.py` | `HistoriaAcademica`; `PerfilAlumno.correos_alternos`; baja de `carrera`/`generacion` | Modificar |
| `backend/accounts/migrations/0005_historiaacademica.py` | Crea el modelo | Crear (generada) |
| `backend/accounts/migrations/0006_migrar_carrera_a_historia.py` | Copia los datos existentes | Crear (a mano) |
| `backend/accounts/migrations/0007_remove_perfilalumno_carrera_generacion.py` | Baja de columnas | Crear (generada) |
| `backend/accounts/migrations/0008_perfilalumno_correos_alternos.py` | ArrayField | Crear (generada) |
| `backend/accounts/admin.py` | Inline de `HistoriaAcademica`; `correos_alternos` | Modificar |
| `backend/accounts/serializers.py` | `perfil_alumno.historial` en `UserDetailsSerializer` | Modificar |
| `backend/accounts/tests/factories.py` | `crear_alumno()` compartido por los tests | Crear |
| `backend/accounts/management/commands/cargar_alumnos.py` | Carga masiva CSV | Crear |
| `backend/academico/` (app nueva) | `PeriodoAcademico`, `semestre_vigente`, endpoint del periodo | Crear |
| `backend/asesorias/models.py` | `PerfilAsesorAcademico.validado_externamente` | Modificar |
| `backend/asesorias/servicios.py` | `semestre_vigente` pasa a delegar en `academico` | Modificar |
| `backend/asesorias/serializers.py` | Carrera del alumno vía `historial`; `SolicitudAsesorSerializer` | Modificar |
| `backend/asesorias/permissions.py` | `EsAcademico` | Modificar |
| `backend/asesorias/views.py` | Scope de semestre; `SolicitudAsesorView`; ventana de registro | Modificar |
| `backend/asesorias/urls.py` | `asesores/solicitud/` | Modificar |
| `frontend/src/api/types.ts` | `historial`, `PeriodoVigente`, `correos_alternos` | Modificar |
| `frontend/src/auth/rol.ts` | `useEsAcademico()` | Modificar |
| `frontend/src/auth/RutaProtegida.tsx` | `RutaDeAcademico`; `RutaDeAsesorias` ampliada | Modificar |
| `frontend/src/App.tsx` | Ruta `/asesorias/soy-asesor` | Modificar |
| `frontend/src/screens/Home.tsx` | Tiles reales por rol | Modificar |
| `frontend/src/data/services.ts` | Mock de 9 servicios | **Borrar** |
| `frontend/src/components/icons/ServiceIcons.tsx` | Solo sobreviven los íconos en uso | Modificar |
| `frontend/src/features/academico/api.ts` | `usePeriodoVigente()` | Crear |
| `frontend/src/features/asesorias/screens/SolicitudAsesor.tsx` | Autoservicio de asesor | Crear |
| `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx` | Selección de carrera con >1 historia | Modificar |
| `docs/decisions/0027-usuarios-reales-academico-autoservicio.md` | ADR de esta iteración | Crear |
| `docs/technical-debt/0018-*.md`, `0019-*.md` | Deuda nueva | Crear |
| `docs/technical-debt/0002, 0008, 0012` | Marcar Resueltas | Modificar |

---

# Fase 0 — Baseline y decisión registrada

## Task 1: Reparar el baseline rojo de `semestreActual`

El hotfix `1533d53` cambió la heurística pero no sus tests: `frontend/src/features/asesorias/logica.test.ts` **falla hoy en `main`** (2 tests). Todo lo demás del plan se apoya en esa heurística, así que se arregla primero.

**Files:**
- Test: `frontend/src/features/asesorias/logica.test.ts:5-13`

**Interfaces:**
- Consumes: nada.
- Produces: `semestreActual(hoy: Date = new Date()): string` queda documentada y verificada — Task 8 la porta a Python.

- [ ] **Step 1: Ver el fallo actual**

Run: `cd frontend && npx vitest run src/features/asesorias/logica.test.ts`
Expected: FAIL, 2 tests — `expected '20262' to be '20261'` y `expected '20271' to be '20262'`.

- [ ] **Step 2: Corregir las expectativas al comportamiento correcto**

Reemplazar el bloque `describe('semestreActual', ...)` completo (líneas 5-13) por:

```ts
describe('semestreActual', () => {
  // Convención UNAM: el semestre AAAA-1 arranca en agosto del año anterior.
  // Agosto 2026 ya es el semestre 2027-1; marzo 2027 es el 2027-2.
  it('julio a diciembre pertenece al semestre 1 del año siguiente', () => {
    expect(semestreActual(new Date('2026-08-01T12:00:00'))).toBe('20271')
    expect(semestreActual(new Date('2026-12-31T12:00:00'))).toBe('20271')
  })

  it('enero a junio pertenece al semestre 2 del año en curso', () => {
    expect(semestreActual(new Date('2027-01-15T12:00:00'))).toBe('20272')
    expect(semestreActual(new Date('2027-06-30T12:00:00'))).toBe('20272')
  })
})
```

Nota: las fechas llevan hora `T12:00:00` a propósito — `new Date('2026-08-01')` se parsea como UTC medianoche y en `America/Mexico_City` cae el 31 de julio, lo que cambiaría el mes evaluado.

- [ ] **Step 3: Verificar verde**

Run: `cd frontend && npx vitest run src/features/asesorias/logica.test.ts`
Expected: PASS, 21 tests.

- [ ] **Step 4: Confirmar que el resto del frontend sigue verde**

Run: `cd frontend && npx vitest run`
Expected: PASS (todos los archivos).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/logica.test.ts
git commit -s -m "$(cat <<'EOF'
[test][frontend] alinear los tests de semestreActual con la heurística corregida

- actualizar las expectativas al comportamiento introducido en 1533d53 (jul–dic → semestre 1 del año siguiente)
- fijar la hora de las fechas de prueba para que el parseo UTC no corra el mes

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 2: ADR 0027 — decisiones de esta iteración

**Files:**
- Create: `docs/decisions/0027-usuarios-reales-academico-autoservicio.md`
- Modify: `docs/superpowers/specs/2026-08-15-usuarios-reales-asesorias-design.md` (una línea de enlace al ADR)

**Interfaces:**
- Consumes: la spec.
- Produces: el ADR al que apuntarán los ítems de deuda 0018 y 0019 (Task 20) en su campo **Origen**.

- [ ] **Step 1: Escribir el ADR**

Crear `docs/decisions/0027-usuarios-reales-academico-autoservicio.md` con exactamente este contenido:

```markdown
# 0027 — Usuarios reales: historia académica, periodo académico y autoservicio de asesor

**Status:** Accepted
**Date:** 2026-08-15

## Context

Atenea abre a usuarios reales para el semestre 20271. Eso rompe tres supuestos del MVP: que un alumno tiene exactamente una carrera y un correo, que "el semestre vigente" se puede derivar de una heurística de fecha sin fechas reales detrás, y que la SAE puede dar de alta a cada asesor a mano en el admin de Django. Además, la Home pinta nueve servicios mock sin backend a cualquier usuario, y ni el alumno ni el académico tienen una entrada a `/asesorias` desde ahí.

## Decision

1. **`HistoriaAcademica(perfil_alumno, carrera, generacion)` reemplaza `PerfilAlumno.carrera`/`generacion`.** Sin `unique_together` sobre `perfil_alumno`: un alumno puede tener varias filas (carrera simultánea o segunda carrera bajo el mismo `numero_cuenta`). Deja de existir una "carrera activa" denormalizada. Vive en `accounts`, junto a `PerfilAlumno`: es identidad del alumno y la lee `UserDetailsSerializer`, así que ponerla en otra app obligaría a `accounts` a importar esa app.
2. **`Asesoria.carrera` no cambia**: sigue siendo un snapshot explícito del payload (ADR 0021). Con una sola fila de historia el backend la infiere por conveniencia; con dos o más, exige el campo y el frontend pregunta.
3. **`PerfilAlumno.correos_alternos`** (`ArrayField(EmailField)`) guarda los correos que la SAE conoce además del de login. Nunca se expone al propio alumno ni participa en la autenticación: solo en el admin de Django y en endpoints con permiso `EsMiembroSAE`.
4. **App nueva `academico`** con `PeriodoAcademico(semestre, fecha_inicio, fecha_fin, registro_asesores_inicio, registro_asesores_fin)`, gestionado a mano desde el admin por la SAE cada semestre (mismo criterio que `PerfilSAE`). La heurística `semestre_vigente()` se porta ahí desde el frontend, y `asesorias.servicios.semestre_vigente` pasa a delegar en ella — la copia que vivía en `asesorias` usaba la convención vieja y estaba mal.
5. **`GET /api/academico/periodo-vigente/`** devuelve el detalle del periodo cuya clave coincide con la heurística, o 404 si la SAE todavía no lo dio de alta. El frontend conserva su propia copia de la heurística para etiquetar sin pegarle a la red, y consulta el endpoint solo para fechas y ventanas.
6. **La oferta se acota al semestre vigente y al asesor activo.** `OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` filtran por `registro__semestre == semestre_vigente()` y `registro__asesor__activo=True`, además de `Disponibilidad.activa`.
7. **Autoservicio de asesor.** Un `PerfilAcademico` sin `PerfilAsesorAcademico` puede solicitarlo eligiendo área. La activación depende de un servicio externo de vigencia de académicos cuyo contrato no está definido: se aísla en `validar_academico_activo(numero_trabajador) -> bool`, con un stub que devuelve `False` (el perfil nace `activo=False` y la SAE lo activa en el admin). El stub es deliberadamente pesimista: nunca concede acceso operativo sin validación humana.
8. **Autoservicio de `RegistroAsesor`** del semestre vigente, permitido solo dentro de `registro_asesores_inicio..registro_asesores_fin` del periodo vigente. La gestión de un registro ya existente (materias, horario) no se restringe por esa ventana.
9. **Home sin mocks.** `services.ts` se borra. Los tiles son reales y gateados por rol; sin ningún tile aplicable se muestra una leyenda en vez de una grilla vacía.

## Consequences

- Un alumno con dos carreras es representable sin duplicar `PerfilAlumno` ni su `numero_cuenta`.
- `PerfilAlumno` deja de responder "¿cuál es su carrera?" en una sola lectura: quien lo necesite recorre `perfil.historial`.
- La SAE gana una tarea recurrente: dar de alta el `PeriodoAcademico` de cada semestre antes de que abra el registro. Sin él, `/api/academico/periodo-vigente/` da 404 y el autoservicio de registro no se ofrece.
- Un `RegistroAsesor` de un semestre pasado deja de aparecer en la oferta aunque sus disponibilidades sigan `activa=True`.
- Mientras el stub de validación externa devuelva `False`, el autoservicio reduce el trabajo de la SAE de "crear el perfil" a "activarlo" — no lo elimina.
- Los nueve servicios mock desaparecen de la vista del usuario sin nada que los reemplace: la Home de un usuario sin rol queda con una leyenda.

## Alternatives considered

- **Conservar `PerfilAlumno.carrera` como "carrera principal" junto al historial**: rechazado — dos fuentes de verdad para el mismo dato, y ninguna regla no arbitraria para elegir la principal cuando hay dos carreras simultáneas.
- **Derivar el semestre vigente solo de `PeriodoAcademico` (buscar el periodo que contiene hoy)**: rechazado como fuente primaria — dejaría al sistema sin semestre en cuanto la SAE olvide dar de alta un periodo, y rompería `RegistroAsesor` y el historial, que solo necesitan la clave. La heurística siempre responde; el modelo aporta las fechas.
- **Un endpoint que devuelva la clave del semestre para que el frontend no la calcule**: rechazado — obligaría a una llamada de red para dibujar una etiqueta, y a un estado de carga en pantallas que hoy son síncronas.
- **Activar el `PerfilAsesorAcademico` en cuanto se solicita, y validar después**: rechazado — un académico no vigente podría publicar disponibilidad y recibir alumnos antes de la validación.
- **Reemplazar los nueve mocks por tiles deshabilitados "próximamente"**: rechazado — anuncia fechas que nadie se comprometió a cumplir.
```

- [ ] **Step 2: Enlazar el ADR desde la spec**

En `docs/superpowers/specs/2026-08-15-usuarios-reales-asesorias-design.md`, justo debajo de la línea `**Date:** 2026-08-15`, agregar:

```markdown
**ADR:** [0027](../../decisions/0027-usuarios-reales-academico-autoservicio.md)
```

- [ ] **Step 3: Commit**

```bash
git add docs/decisions/0027-usuarios-reales-academico-autoservicio.md docs/superpowers/specs/2026-08-15-usuarios-reales-asesorias-design.md
git commit -s -m "$(cat <<'EOF'
[docs] ADR 0027: historia académica, periodo académico y autoservicio de asesor

- registrar las nueve decisiones de la spec de usuarios reales
- enlazar el ADR desde la spec

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 1 — `HistoriaAcademica`

## Task 3: Modelo `HistoriaAcademica` + migración + admin (aditivo)

Paso aditivo: `PerfilAlumno.carrera`/`generacion` **siguen existiendo** al final de esta tarea. Se borran en la Task 5, cuando ya nadie los lee.

**Files:**
- Modify: `backend/accounts/models.py:36-43`
- Create: `backend/accounts/migrations/0005_historiaacademica.py` (generada)
- Modify: `backend/accounts/admin.py:54-58`
- Create: `backend/accounts/tests/factories.py`
- Test: `backend/accounts/tests/test_perfiles.py`, `backend/accounts/tests/test_admin.py`

**Interfaces:**
- Consumes: `accounts.PerfilAlumno`, `carreras.Carrera`.
- Produces:
  - `accounts.models.HistoriaAcademica` con campos `perfil_alumno` (FK, `related_name="historial"`), `carrera` (FK a `carreras.Carrera`, `related_name="historial_alumnos"`), `generacion` (`PositiveSmallIntegerField`).
  - `accounts.tests.factories.crear_alumno(user, numero_cuenta, carrera=None, generacion=2023) -> PerfilAlumno` — usada por todos los tests a partir de la Task 5.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `backend/accounts/tests/test_perfiles.py`:

```python
class HistoriaAcademicaTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area historia")
        self.carrera_a = Carrera.objects.create(clave=971, nombre="Carrera A Test", area=self.area)
        self.carrera_b = Carrera.objects.create(clave=972, nombre="Carrera B Test", area=self.area)
        self.user = User.objects.create_user(email="historia@ciencias.unam.mx", password="x")
        self.perfil = PerfilAlumno.objects.create(user=self.user, numero_cuenta="312000001")

    def test_un_alumno_puede_tener_dos_carreras_simultaneas(self):
        from accounts.models import HistoriaAcademica

        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2023
        )
        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_b, generacion=2025
        )
        self.assertEqual(self.perfil.historial.count(), 2)

    def test_no_se_repite_la_misma_carrera_para_el_mismo_alumno(self):
        from accounts.models import HistoriaAcademica

        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2023
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistoriaAcademica.objects.create(
                perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2024
            )

    def test_borrar_el_perfil_borra_su_historial(self):
        from accounts.models import HistoriaAcademica

        HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_a, generacion=2023
        )
        self.perfil.delete()
        self.assertEqual(HistoriaAcademica.objects.count(), 0)
```

Nota: `PerfilAlumno.objects.create(user=..., numero_cuenta=...)` sin `carrera`/`generacion` todavía no es válido en este punto (los campos son obligatorios). Por eso el `setUp` de arriba se escribe así a propósito: la Step 3 hace `carrera`/`generacion` opcionales en el mismo movimiento.

Agregar a `backend/accounts/tests/test_admin.py`:

```python
    def test_historia_academica_registrada(self):
        from accounts.models import HistoriaAcademica

        self.assertIn(HistoriaAcademica, admin.site._registry)
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `cd backend && uv run manage.py test accounts.tests.test_perfiles accounts.tests.test_admin -v 2`
Expected: FAIL — `ImportError: cannot import name 'HistoriaAcademica' from 'accounts.models'`.

- [ ] **Step 3: Implementar el modelo**

En `backend/accounts/models.py`, reemplazar la clase `PerfilAlumno` (líneas 36-43) por:

```python
class PerfilAlumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_alumno")
    numero_cuenta = models.CharField(max_length=10, unique=True)
    # Transitorios: los reemplaza HistoriaAcademica y se borran en la migración
    # 0007, una vez que ningún lector los usa (ADR 0027 decisión 1).
    carrera = models.ForeignKey(
        "carreras.Carrera", on_delete=models.PROTECT, related_name="alumnos",
        null=True, blank=True,
    )
    generacion = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero_cuenta}, {self.user.email}"


class HistoriaAcademica(models.Model):
    """Una inscripción del alumno a una carrera.

    Sin `unique_together` sobre `perfil_alumno` solo: un mismo número de
    cuenta puede cursar dos carreras a la vez o iniciar una segunda
    (ADR 0027 decisión 1). Lo que sí es único es el par: la misma carrera
    no se registra dos veces para el mismo alumno.
    """

    perfil_alumno = models.ForeignKey(
        PerfilAlumno, on_delete=models.CASCADE, related_name="historial"
    )
    carrera = models.ForeignKey(
        "carreras.Carrera", on_delete=models.PROTECT, related_name="historial_alumnos"
    )
    generacion = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["generacion", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["perfil_alumno", "carrera"], name="unique_historia_alumno_carrera"
            ),
        ]

    def __str__(self):
        return f"{self.perfil_alumno.numero_cuenta} — {self.carrera} ({self.generacion})"
```

- [ ] **Step 4: Generar la migración**

Run: `cd backend && uv run manage.py makemigrations accounts --name historiaacademica`
Expected: crea `backend/accounts/migrations/0005_historiaacademica.py` con `CreateModel` + `AlterField` de `carrera` y `generacion` a nullable.

- [ ] **Step 5: Registrar en el admin**

En `backend/accounts/admin.py`, reemplazar el bloque de `PerfilAlumnoAdmin` (líneas 54-58) por:

```python
class HistoriaAcademicaInline(admin.TabularInline):
    model = HistoriaAcademica
    extra = 0


@admin.register(PerfilAlumno)
class PerfilAlumnoAdmin(admin.ModelAdmin):
    list_display = ("numero_cuenta", "user")
    search_fields = ("numero_cuenta", "user__email")
    inlines = [HistoriaAcademicaInline]


@admin.register(HistoriaAcademica)
class HistoriaAcademicaAdmin(admin.ModelAdmin):
    list_display = ("perfil_alumno", "carrera", "generacion")
    list_filter = ("carrera", "generacion")
    search_fields = ("perfil_alumno__numero_cuenta", "perfil_alumno__user__email")
```

y cambiar el import de la línea 5 por:

```python
from .models import User, HistoriaAcademica, PerfilAcademico, PerfilAlumno, PerfilSAE
```

- [ ] **Step 6: Crear la factory de tests**

Crear `backend/accounts/tests/factories.py`:

```python
"""Helpers de construcción para tests.

`crear_alumno` existe para que los tests no tengan que saber que la carrera
del alumno dejó de vivir en `PerfilAlumno` y pasó a `HistoriaAcademica`
(ADR 0027 decisión 1): la firma es la misma que tenía
`PerfilAlumno.objects.create` antes del cambio.
"""

from accounts.models import HistoriaAcademica, PerfilAlumno


def crear_alumno(user, numero_cuenta, carrera=None, generacion=2023):
    perfil = PerfilAlumno.objects.create(user=user, numero_cuenta=numero_cuenta)
    if carrera is not None:
        HistoriaAcademica.objects.create(
            perfil_alumno=perfil, carrera=carrera, generacion=generacion
        )
    return perfil
```

- [ ] **Step 7: Verificar verde**

Run: `cd backend && uv run manage.py test accounts -v 2`
Expected: PASS.

- [ ] **Step 8: Verificar que nada más se rompió**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS (todo el backend).

- [ ] **Step 9: Commit**

```bash
git add backend/accounts/models.py backend/accounts/migrations/0005_historiaacademica.py backend/accounts/admin.py backend/accounts/tests/
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar HistoriaAcademica para el historial multi-carrera del alumno

- agregar modelo HistoriaAcademica (perfil_alumno, carrera, generacion) con unicidad por par alumno-carrera
- volver nullable PerfilAlumno.carrera/generacion como paso transitorio
- registrar el modelo en el admin, con inline en PerfilAlumno
- agregar accounts.tests.factories.crear_alumno para los tests

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 4: Migrar los lectores a `historial`

**Files:**
- Create: `backend/accounts/migrations/0006_migrar_carrera_a_historia.py`
- Modify: `backend/accounts/serializers.py:126-136`
- Modify: `backend/asesorias/serializers.py:136-165`
- Test: `backend/accounts/tests/test_user_details.py`, `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**
- Consumes: `HistoriaAcademica` (Task 3).
- Produces:
  - `UserDetailsSerializer.get_perfil_alumno` devuelve `{"id", "numero_cuenta", "historial": [{"carrera", "carrera_nombre", "generacion"}]}` — lo consume `frontend/src/api/types.ts` en la Task 6.
  - `AsesoriaSerializer.validate` exige `carrera` explícita cuando el alumno tiene ≠1 historia.

- [ ] **Step 1: Escribir el test de migración de datos**

Crear `backend/accounts/tests/test_migracion_historia.py`:

```python
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
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test accounts.tests.test_migracion_historia -v 2`
Expected: FAIL — `NodeNotFoundError` / `KeyError` sobre `accounts.0006_migrar_carrera_a_historia` (la migración no existe).

- [ ] **Step 3: Escribir la migración de datos**

Crear `backend/accounts/migrations/0006_migrar_carrera_a_historia.py`:

```python
from django.db import migrations


def copiar_carrera_al_historial(apps, schema_editor):
    PerfilAlumno = apps.get_model("accounts", "PerfilAlumno")
    HistoriaAcademica = apps.get_model("accounts", "HistoriaAcademica")
    for perfil in PerfilAlumno.objects.exclude(carrera__isnull=True).iterator():
        HistoriaAcademica.objects.get_or_create(
            perfil_alumno=perfil,
            carrera_id=perfil.carrera_id,
            defaults={"generacion": perfil.generacion or 0},
        )


def vaciar_historial(apps, schema_editor):
    # Reversa deliberadamente destructiva y acotada: la migración solo crea
    # filas a partir de la columna denormalizada, así que deshacerla es
    # borrar exactamente lo que creó. No intenta reconstruir
    # PerfilAlumno.carrera porque en 0007 esa columna ya no existe.
    HistoriaAcademica = apps.get_model("accounts", "HistoriaAcademica")
    HistoriaAcademica.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_historiaacademica")]

    operations = [
        migrations.RunPython(copiar_carrera_al_historial, vaciar_historial),
    ]
```

- [ ] **Step 4: Verificar que el test de migración pasa**

Run: `cd backend && uv run manage.py test accounts.tests.test_migracion_historia -v 2`
Expected: PASS.

- [ ] **Step 5: Escribir el test del serializer de usuario**

En `backend/accounts/tests/test_user_details.py`, cambiar la aserción del perfil de alumno (líneas 45-50 aprox., el dict con `"carrera"`, `"carrera_nombre"`, `"generacion"`) por:

```python
                "historial": [
                    {
                        "carrera": self.carrera.id,
                        "carrera_nombre": "Carrera Test",
                        "generacion": 2023,
                    }
                ],
```

y agregar al final del archivo:

```python
class PerfilAlumnoDosCarrerasTests(TestCase):
    def test_el_historial_lista_las_dos_carreras(self):
        from accounts.models import HistoriaAcademica
        from accounts.tests.factories import crear_alumno

        area = Area.objects.create(nombre="Area dos carreras")
        carrera_a = Carrera.objects.create(clave=961, nombre="Carrera Uno Test", area=area)
        carrera_b = Carrera.objects.create(clave=962, nombre="Carrera Dos Test", area=area)
        user = User.objects.create_user(email="doble@ciencias.unam.mx", password="x")
        perfil = crear_alumno(user, "312000077", carrera=carrera_a, generacion=2022)
        HistoriaAcademica.objects.create(
            perfil_alumno=perfil, carrera=carrera_b, generacion=2025
        )

        self.client.force_login(user)
        response = self.client.get("/api/auth/user/")

        historial = response.json()["perfil_alumno"]["historial"]
        self.assertEqual(
            [fila["carrera_nombre"] for fila in historial],
            ["Carrera Uno Test", "Carrera Dos Test"],
        )
```

(Si el archivo no importa ya `User`, `Area` o `Carrera`, agregarlos al bloque de imports de arriba: `from accounts.models import User` y `from carreras.models import Area, Carrera`.)

- [ ] **Step 6: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test accounts.tests.test_user_details -v 2`
Expected: FAIL — la respuesta trae `carrera`/`generacion`, no `historial`.

- [ ] **Step 7: Implementar el serializer de usuario**

En `backend/accounts/serializers.py`, reemplazar `get_perfil_alumno` (líneas 126-136) por:

```python
    def get_perfil_alumno(self, obj):
        perfil = getattr(obj, "perfil_alumno", None)
        if perfil is None:
            return None
        # `correos_alternos` NO viaja aquí: es visible solo para la SAE
        # (ADR 0027 decisión 3). El alumno nunca ve su propia lista.
        return {
            "id": perfil.id,
            "numero_cuenta": perfil.numero_cuenta,
            "historial": [
                {
                    "carrera": historia.carrera_id,
                    "carrera_nombre": historia.carrera.nombre,
                    "generacion": historia.generacion,
                }
                for historia in perfil.historial.select_related("carrera")
            ],
        }
```

- [ ] **Step 8: Verificar verde**

Run: `cd backend && uv run manage.py test accounts.tests.test_user_details -v 2`
Expected: PASS.

- [ ] **Step 9: Escribir los tests de agendar con historial**

En `backend/asesorias/tests/test_api_asesoria.py`, agregar al final del archivo:

```python
class AgendarConHistorialTests(APITestCase):
    """La carrera del payload se valida contra HistoriaAcademica, no contra
    un campo denormalizado del perfil (ADR 0027 decisión 2)."""

    def setUp(self):
        from accounts.models import HistoriaAcademica, PerfilAcademico, User
        from accounts.tests.factories import crear_alumno
        from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
        from carreras.models import Area, Carrera
        from materias.models import Materia, OfertaMateria
        from asesorias.servicios import semestre_vigente
        import datetime

        self.area = Area.objects.create(nombre="Area historial agendar")
        self.carrera_a = Carrera.objects.create(clave=951, nombre="Carrera HA Test", area=self.area)
        self.carrera_b = Carrera.objects.create(clave=952, nombre="Carrera HB Test", area=self.area)
        self.carrera_ajena = Carrera.objects.create(
            clave=953, nombre="Carrera HC Ajena Test", area=self.area
        )
        self.materia = Materia.objects.create(
            clave="1951", nombre="Álgebra HA", carrera=self.carrera_a, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(
            materia=self.materia, semestre=semestre_vigente(), se_imparte=True
        )

        asesor_user = User.objects.create_user(email="asesor.ha@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=asesor_user, numero_trabajador="91234")
        asesor = PerfilAsesorAcademico.objects.create(user=asesor_user, area=self.area)
        registro = RegistroAsesor.objects.create(asesor=asesor, semestre=semestre_vigente())
        registro.materias.add(self.materia)
        hoy = datetime.date.today()
        self.disponibilidad = Disponibilidad.objects.create(
            registro=registro, dia_semana=hoy.weekday(), hora_inicio=datetime.time(9, 0),
            formato="virtual", liga_virtual="https://zoom.us/j/1",
        )
        self.fecha = hoy

        self.user = User.objects.create_user(email="alumno.ha@ciencias.unam.mx", password="x")
        self.perfil = crear_alumno(self.user, "312000055", carrera=self.carrera_a, generacion=2023)
        self.HistoriaAcademica = HistoriaAcademica
        self.client.force_authenticate(user=self.user)

    def _payload(self, carrera_id=None):
        cuerpo = {
            "disponibilidad": self.disponibilidad.id,
            "fecha": self.fecha.isoformat(),
            "materia": self.materia.id,
        }
        if carrera_id is not None:
            cuerpo["carrera"] = carrera_id
        return cuerpo

    def test_con_una_sola_carrera_el_payload_puede_omitirla(self):
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["carrera"], self.carrera_a.id)

    def test_con_dos_carreras_la_carrera_es_obligatoria(self):
        self.HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_b, generacion=2025
        )
        response = self.client.post("/api/asesorias/asesorias/", self._payload())
        self.assertEqual(response.status_code, 400)
        self.assertIn("carrera", response.data)

    def test_con_dos_carreras_acepta_cualquiera_de_las_suyas(self):
        self.HistoriaAcademica.objects.create(
            perfil_alumno=self.perfil, carrera=self.carrera_b, generacion=2025
        )
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera_id=self.carrera_b.id)
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["carrera"], self.carrera_b.id)

    def test_rechaza_una_carrera_que_no_es_del_alumno(self):
        response = self.client.post(
            "/api/asesorias/asesorias/", self._payload(carrera_id=self.carrera_ajena.id)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("carrera", response.data)
```

- [ ] **Step 10: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test asesorias.tests.test_api_asesoria.AgendarConHistorialTests -v 2`
Expected: FAIL — `test_con_dos_carreras_la_carrera_es_obligatoria` devuelve 201 en vez de 400 (hoy el serializer cae a `alumno.carrera`).

- [ ] **Step 11: Implementar la validación en `AsesoriaSerializer`**

En `backend/asesorias/serializers.py`, reemplazar las líneas 136-144 (desde `def validate(self, attrs):` hasta el `raise` de carrera) por:

```python
    def validate(self, attrs):
        disponibilidad = attrs["disponibilidad"]
        alumno = self.context["request"].user.perfil_alumno
        # ADR 0027 decisión 2: el backend no elige por el alumno. Con una sola
        # inscripción la infiere por conveniencia (contrato previo intacto);
        # con dos o más exige que el payload lo diga.
        carreras_del_alumno = set(alumno.historial.values_list("carrera_id", flat=True))
        carrera = attrs.get("carrera")
        if carrera is None:
            if len(carreras_del_alumno) != 1:
                raise serializers.ValidationError(
                    {"carrera": "Indica con qué carrera agendas esta asesoría."}
                )
            carrera = Carrera.objects.get(pk=next(iter(carreras_del_alumno)))
        if carrera.id not in carreras_del_alumno:
            raise serializers.ValidationError({"carrera": "La carrera no pertenece al alumno."})
```

El resto del método (desde `instance = Asesoria(` hasta `return attrs`) queda igual.

- [ ] **Step 12: Verificar verde**

Run: `cd backend && uv run manage.py test asesorias.tests.test_api_asesoria -v 2`
Expected: PASS. Si `test_api_asesoria.py:566` (`self.alumno.carrera = self.carrera_ajena`) falla, reemplazar esas líneas por:

```python
        self.alumno.historial.update(carrera=self.carrera_ajena)
```

- [ ] **Step 13: Suite completa**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 14: Commit**

```bash
git add backend/accounts backend/asesorias/serializers.py backend/asesorias/tests
git commit -s -m "$(cat <<'EOF'
[feat][backend] leer la carrera del alumno desde HistoriaAcademica

- migrar los datos de PerfilAlumno.carrera/generacion a HistoriaAcademica
- exponer perfil_alumno.historial en UserDetailsSerializer
- exigir carrera explícita al agendar cuando el alumno tiene más de una inscripción

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 5: Borrar `PerfilAlumno.carrera` y `PerfilAlumno.generacion`

**Files:**
- Modify: `backend/accounts/models.py` (clase `PerfilAlumno`)
- Create: `backend/accounts/migrations/0007_remove_perfilalumno_carrera_generacion.py` (generada)
- Test (fixtures a actualizar): `backend/accounts/tests/test_perfiles.py`, `backend/asesorias/tests/test_asesoria.py`, `test_api_disponibilidad.py`, `test_api_busqueda.py`, `test_permissions.py`, `test_api_oferta.py`, `test_notificaciones.py`, `test_api_registro.py`, `test_disponibilidad.py`, `test_api_admin.py`, `test_api_flujo_completo.py`, `test_registro_asesor.py`, `test_api_asesoria.py`

**Interfaces:**
- Consumes: `crear_alumno` (Task 3), `historial` (Task 4).
- Produces: `PerfilAlumno` con exactamente tres campos propios: `user`, `numero_cuenta`, y (Task 7) `correos_alternos`.

- [ ] **Step 1: Localizar todos los call sites**

Run: `cd backend && grep -rn "PerfilAlumno.objects.create" --include=*.py .`
Expected: 33 ocurrencias en 14 archivos de test (más las de `accounts/tests/factories.py`, que se dejan como están).

- [ ] **Step 2: Reemplazar cada call site por `crear_alumno`**

En cada archivo de test listado arriba, sustituir cada llamada de la forma

```python
PerfilAlumno.objects.create(
    user=X, numero_cuenta="NNN", carrera=Y, generacion=ZZZZ,
)
```

por

```python
crear_alumno(user=X, numero_cuenta="NNN", carrera=Y, generacion=ZZZZ)
```

agregando en cada archivo el import `from accounts.tests.factories import crear_alumno`. Las llamadas que ya no pasan `carrera`/`generacion` (las de `accounts/tests/test_perfiles.py` sobre unicidad y las de la Task 3) se dejan como `PerfilAlumno.objects.create(...)`.

Los `tearDown` que hacen `self.carrera.delete()` (`test_asesoria.py:49`, `test_api_registro.py:44`) siguen funcionando: `HistoriaAcademica.carrera` es `PROTECT`, pero el `tearDown` borra primero al alumno, lo que cascadea su historial.

- [ ] **Step 3: Verificar que la suite sigue verde antes de tocar el modelo**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS. (Si aquí falla algo, es un call site sin migrar — arreglarlo antes de seguir.)

- [ ] **Step 4: Borrar los campos del modelo**

En `backend/accounts/models.py`, dejar `PerfilAlumno` así:

```python
class PerfilAlumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_alumno")
    numero_cuenta = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.numero_cuenta}, {self.user.email}"
```

- [ ] **Step 5: Generar la migración**

Run: `cd backend && uv run manage.py makemigrations accounts --name remove_perfilalumno_carrera_generacion`
Expected: `0007_remove_perfilalumno_carrera_generacion.py` con dos `RemoveField`.

- [ ] **Step 6: Verificar verde**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 7: Confirmar que no faltan migraciones**

Run: `cd backend && uv run manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

- [ ] **Step 8: Commit**

```bash
git add backend/accounts backend/asesorias/tests
git commit -s -m "$(cat <<'EOF'
[refactor][backend] eliminar PerfilAlumno.carrera y PerfilAlumno.generacion

- borrar las columnas denormalizadas ahora que HistoriaAcademica es la única fuente
- migrar los fixtures de test a accounts.tests.factories.crear_alumno

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 6: Frontend — historial y selección de carrera al agendar

**Files:**
- Modify: `frontend/src/api/types.ts:6-12`
- Modify: `frontend/src/test/factories.ts`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx:35-36,90-97,193-207`
- Test: `frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx`, `frontend/src/auth/rol.test.tsx:44-50`

**Interfaces:**
- Consumes: `GET /api/auth/user/` → `perfil_alumno.historial` (Task 4).
- Produces: `interface InscripcionAlumno { carrera: number; carrera_nombre: string; generacion: number }` y `PerfilAlumno.historial: InscripcionAlumno[]`.

- [ ] **Step 1: Escribir el test de la pantalla**

En `frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx`, el helper `mockComun` (línea 22) mockea `useAuth` con el perfil viejo. Cambiar ese `vi.spyOn(auth, 'useAuth')` por una versión parametrizable:

```tsx
const HISTORIAL_UNA: InscripcionAlumno[] = [
  { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
]

function mockComun(
  mutateImpl: ReturnType<typeof vi.fn>,
  historial: InscripcionAlumno[] = HISTORIAL_UNA,
) {
```

y dentro de ella:

```tsx
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: { perfil_alumno: { id: 1, numero_cuenta: '312345678', historial } },
    status: 'authenticated',
  } as unknown as ReturnType<typeof auth.useAuth>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(
    new Map([
      [3, { id: 3, nombre: 'Actuaría' } as never],
      [6, { id: 6, nombre: 'Matemáticas' } as never],
    ]),
  )
```

agregando `InscripcionAlumno` al import de tipos de la línea 10. Los tests existentes siguen pasando: el default reproduce el perfil de una sola carrera con `carrera: 3`.

Agregar al final del archivo:

```tsx
describe('AgendarAsesoria — selección de carrera', () => {
  afterEach(() => vi.restoreAllMocks())

  function avanzarHastaCarrera() {
    fireEvent.click(screen.getByText('Ana López'))
    fireEvent.click(screen.getByText(/10 de agosto/i))
    fireEvent.click(screen.getByText('10:00–10:30'))
  }

  it('con una sola inscripción deja la carrera preseleccionada', () => {
    mockComun(vi.fn())
    montar()
    avanzarHastaCarrera()
    expect((screen.getByLabelText('Carrera') as HTMLSelectElement).value).toBe('3')
  })

  it('con dos inscripciones ofrece ambas y no preselecciona ninguna', () => {
    mockComun(vi.fn(), [
      { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
      { carrera: 6, carrera_nombre: 'Matemáticas', generacion: 2025 },
    ])
    montar()
    avanzarHastaCarrera()
    const select = screen.getByLabelText('Carrera') as HTMLSelectElement
    expect(select.value).toBe('')
    expect([...select.options].map((o) => o.textContent)).toEqual([
      'Elige una carrera', 'Actuaría', 'Matemáticas',
    ])
  })

  it('con dos inscripciones el POST manda la que se eligió', () => {
    const mutate = vi.fn()
    mockComun(mutate, [
      { carrera: 3, carrera_nombre: 'Actuaría', generacion: 2023 },
      { carrera: 6, carrera_nombre: 'Matemáticas', generacion: 2025 },
    ])
    montar()
    avanzarHastaCarrera()
    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '6' } })
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ carrera: 6 }),
      expect.anything(),
    )
  })
})
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `cd frontend && npx vitest run src/features/asesorias/screens/AgendarAsesoria.test.tsx`
Expected: FAIL — error de tipos/propiedad: `perfil_alumno.carrera` es `undefined`.

- [ ] **Step 3: Actualizar los tipos**

En `frontend/src/api/types.ts`, reemplazar la interfaz `PerfilAlumno` (líneas 6-12) por:

```ts
/** Una inscripción del alumno a una carrera. Espejo de `accounts.HistoriaAcademica`. */
export interface InscripcionAlumno {
  carrera: number
  carrera_nombre: string
  generacion: number
}

export interface PerfilAlumno {
  id: number
  numero_cuenta: string
  // Puede traer más de una fila: carrera simultánea o segunda carrera bajo el
  // mismo número de cuenta (ADR 0027 decisión 1). `correos_alternos` no viaja
  // aquí a propósito: es visible solo para la SAE.
  historial: InscripcionAlumno[]
}
```

- [ ] **Step 4: Actualizar la factory de tests**

En `frontend/src/test/factories.ts`, agregar debajo de `usuarioSAE`:

```ts
/** Usuario alumno con una sola inscripción, el caso más común. */
export function usuarioAlumno(overrides: Partial<AuthUser> = {}): AuthUser {
  return usuarioDePrueba({
    roles: ['alumno'],
    perfil_alumno: {
      id: 4,
      numero_cuenta: '312345678',
      historial: [{ carrera: 5, carrera_nombre: 'Actuaría', generacion: 2023 }],
    },
    ...overrides,
  })
}
```

y en `frontend/src/auth/rol.test.tsx` reemplazar el objeto `perfil_alumno` del test "reconoce al alumno" (líneas 44-50) por:

```tsx
        perfil_alumno: {
          id: 4,
          numero_cuenta: '312345678',
          historial: [{ carrera: 5, carrera_nombre: 'Actuaría', generacion: 2023 }],
        },
```

- [ ] **Step 5: Implementar la pantalla**

En `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx`:

Reemplazar las líneas 35-36 por:

```tsx
  const historial = user?.perfil_alumno?.historial ?? []
  // Con una sola inscripción no hay nada que preguntar: se preselecciona.
  // Con dos o más, `carrera` arranca en null y el backend exige el campo.
  const [carrera, setCarrera] = useState<number | null>(
    historial.length === 1 ? historial[0].carrera : null,
  )
```

Reemplazar el bloque `if (carreraAlumno === null) { ... }` (líneas 90-97) por:

```tsx
  if (historial.length === 0) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate('/asesorias')} className="foco-visible w-fit min-h-11 text-sm text-primary">← Volver a Asesorías</button>
        <p className="text-sm text-on-surface-variant">Sólo los alumnos pueden agendar asesorías.</p>
      </main>
    )
  }
```

Reemplazar el contenido del `<select>` (líneas 201-205) por:

```tsx
              {historial.length > 1 && <option value="">Elige una carrera</option>}
              {historial.map((inscripcion) => (
                <option key={inscripcion.carrera} value={inscripcion.carrera}>
                  {mapaCarreras.get(inscripcion.carrera)?.nombre ?? inscripcion.carrera_nombre}
                </option>
              ))}
```

- [ ] **Step 6: Verificar verde**

Run: `cd frontend && npx vitest run`
Expected: PASS.

- [ ] **Step 7: Typecheck y lint**

Run: `cd frontend && npx tsc -b && npm run lint`
Expected: sin errores.

- [ ] **Step 8: Commit**

```bash
git add frontend/src
git commit -s -m "$(cat <<'EOF'
[feat][frontend] elegir carrera al agendar cuando el alumno tiene varias

- reemplazar PerfilAlumno.carrera/generacion por historial en los tipos de la API
- preseleccionar la única inscripción y ofrecer el selector completo con dos o más
- agregar la factory usuarioAlumno para los tests

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 2 — Correos alternos

## Task 7: `PerfilAlumno.correos_alternos`

**Files:**
- Modify: `backend/accounts/models.py`
- Create: `backend/accounts/migrations/0008_perfilalumno_correos_alternos.py` (generada)
- Modify: `backend/accounts/admin.py`
- Modify: `backend/asesorias/views.py:487-513` (`AdminAlumnosView`)
- Modify: `frontend/src/api/types.ts` (`AlumnoBusqueda`)
- Test: `backend/accounts/tests/test_perfiles.py`, `backend/accounts/tests/test_user_details.py`, `backend/asesorias/tests/test_api_admin.py`

**Interfaces:**
- Consumes: `PerfilAlumno` (Task 5).
- Produces: `PerfilAlumno.correos_alternos: list[str]`; `GET /api/asesorias/admin/alumnos/` agrega la clave `correos_alternos` a cada fila.

- [ ] **Step 1: Escribir los tests**

Agregar a `backend/accounts/tests/test_perfiles.py`:

```python
class CorreosAlternosTests(TestCase):
    def test_nace_como_lista_vacia(self):
        user = User.objects.create_user(email="ca@ciencias.unam.mx", password="x")
        perfil = PerfilAlumno.objects.create(user=user, numero_cuenta="312000010")
        perfil.refresh_from_db()
        self.assertEqual(perfil.correos_alternos, [])

    def test_guarda_varios_correos(self):
        user = User.objects.create_user(email="cb@ciencias.unam.mx", password="x")
        perfil = PerfilAlumno.objects.create(
            user=user, numero_cuenta="312000011",
            correos_alternos=["viejo@gmail.com", "otro@ciencias.unam.mx"],
        )
        perfil.refresh_from_db()
        self.assertEqual(len(perfil.correos_alternos), 2)
```

Agregar a `backend/accounts/tests/test_user_details.py`:

```python
class CorreosAlternosNoSeExponenAlAlumnoTests(TestCase):
    def test_el_perfil_del_alumno_no_incluye_correos_alternos(self):
        from accounts.tests.factories import crear_alumno

        user = User.objects.create_user(email="priv@ciencias.unam.mx", password="x")
        perfil = crear_alumno(user, "312000012")
        perfil.correos_alternos = ["privado@gmail.com"]
        perfil.save()

        self.client.force_login(user)
        response = self.client.get("/api/auth/user/")

        self.assertNotIn("correos_alternos", response.json()["perfil_alumno"])
        self.assertNotIn("privado@gmail.com", response.content.decode())
```

Agregar a `backend/asesorias/tests/test_api_admin.py`, dentro de la clase que ya prueba `AdminAlumnosView` (la que hace `GET /api/asesorias/admin/alumnos/`):

```python
    def test_el_sae_ve_los_correos_alternos_del_alumno(self):
        self.juan.correos_alternos = ["juan.viejo@gmail.com"]
        self.juan.save()
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/alumnos/?buscar=Juan")
        fila = next(f for f in response.data if f["perfil_id"] == self.juan.id)
        self.assertEqual(fila["correos_alternos"], ["juan.viejo@gmail.com"])
```

(`self.sae_user` es el usuario SAE que ya construye el `setUp` de esa clase; usar el nombre real que tenga.)

- [ ] **Step 2: Correr para verificar que fallan**

Run: `cd backend && uv run manage.py test accounts.tests.test_perfiles accounts.tests.test_user_details asesorias.tests.test_api_admin -v 2`
Expected: FAIL — `TypeError: PerfilAlumno() got unexpected keyword arguments: 'correos_alternos'`.

- [ ] **Step 3: Agregar el campo**

En `backend/accounts/models.py`, agregar el import al inicio:

```python
from django.contrib.postgres.fields import ArrayField
```

y el campo dentro de `PerfilAlumno`, debajo de `numero_cuenta`:

```python
    # Correos que la SAE conoce además del de login. NO participa en la
    # autenticación ni en la resolución de cuentas (ADR 0027 decisión 3):
    # `User.email` sigue siendo la única llave (ADR 0003 / 0019).
    correos_alternos = ArrayField(
        models.EmailField(), default=list, blank=True,
    )
```

- [ ] **Step 4: Generar la migración**

Run: `cd backend && uv run manage.py makemigrations accounts --name perfilalumno_correos_alternos`
Expected: `0008_perfilalumno_correos_alternos.py`.

- [ ] **Step 5: Mostrarlo en el admin**

En `backend/accounts/admin.py`, dentro de `PerfilAlumnoAdmin`, agregar:

```python
    fields = ("user", "numero_cuenta", "correos_alternos")
    list_display = ("numero_cuenta", "user", "correos_alternos")
```

(reemplazando el `list_display` anterior).

- [ ] **Step 6: Exponerlo al SAE**

En `backend/asesorias/views.py`, dentro de `AdminAlumnosView.get`, agregar la clave al dict de `data`:

```python
                "numero_cuenta": alumno.numero_cuenta,
                # Visible solo aquí y en el admin: este endpoint es EsMiembroSAE
                # (ADR 0027 decisión 3).
                "correos_alternos": alumno.correos_alternos,
```

- [ ] **Step 7: Verificar verde**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 8: Reflejarlo en los tipos del frontend**

En `frontend/src/api/types.ts`, en `AlumnoBusqueda`, agregar:

```ts
  /** Correos que la SAE conoce además del de login. Solo llega a endpoints SAE. */
  correos_alternos: string[]
```

- [ ] **Step 9: Verificar el frontend**

Run: `cd frontend && npx tsc -b && npx vitest run`
Expected: PASS. Si algún mock de `AlumnoBusqueda` en los tests de `AdminAsesorias` falla el typecheck, agregarle `correos_alternos: []`.

- [ ] **Step 10: Commit**

```bash
git add backend frontend/src/api/types.ts frontend/src
git commit -s -m "$(cat <<'EOF'
[feat][backend] guardar los correos alternos que la SAE conoce del alumno

- agregar PerfilAlumno.correos_alternos (ArrayField de EmailField)
- exponerlo en el admin y en GET /api/asesorias/admin/alumnos/, nunca al propio alumno
- reflejar el campo en AlumnoBusqueda del frontend

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 3 — `PeriodoAcademico` y scope de semestre

## Task 8: App `academico` + `semestre_vigente` corregida

**Files:**
- Create: `backend/academico/__init__.py`, `apps.py`, `models.py`, `admin.py`, `servicios.py`, `views.py`, `urls.py`, `serializers.py`, `migrations/__init__.py`, `tests/__init__.py`, `tests/test_servicios.py`
- Modify: `backend/config/settings/base.py` (`LOCAL_APPS`)
- Modify: `backend/asesorias/servicios.py:14-23`
- Modify: `backend/asesorias/tests/test_servicios.py:33-56`

**Interfaces:**
- Consumes: nada.
- Produces: `academico.servicios.semestre_vigente(hoy: datetime.date | None = None) -> str`. `asesorias.servicios.semestre_vigente` se conserva como re-export para no romper sus importadores (`asesorias/views.py:27`).

- [ ] **Step 1: Crear el esqueleto de la app**

Run:
```bash
cd backend && uv run manage.py startapp academico && mkdir -p academico/tests && touch academico/tests/__init__.py && rm -f academico/tests.py
```
Expected: `backend/academico/` con `apps.py`, `models.py`, `admin.py`, `views.py`, `migrations/`.

En `backend/config/settings/base.py`, dejar `LOCAL_APPS` así:

```python
LOCAL_APPS = [
    "accounts",
    "academico",
    "carreras",
    "materias",
    "asesorias",
]
```

- [ ] **Step 2: Escribir el test de la heurística**

Crear `backend/academico/tests/test_servicios.py`:

```python
import datetime

from django.test import SimpleTestCase

from academico.servicios import semestre_vigente


class SemestreVigenteTests(SimpleTestCase):
    """Convención UNAM: el semestre AAAA-1 arranca en agosto del año anterior.

    Espejo exacto de `semestreActual` de
    `frontend/src/features/asesorias/logica.ts`. Si divergen, el frontend y el
    backend etiquetan el mismo registro con claves distintas.
    """

    def test_julio_a_diciembre_es_el_semestre_1_del_anio_siguiente(self):
        self.assertEqual(semestre_vigente(datetime.date(2026, 7, 1)), "20271")
        self.assertEqual(semestre_vigente(datetime.date(2026, 8, 1)), "20271")
        self.assertEqual(semestre_vigente(datetime.date(2026, 12, 31)), "20271")

    def test_enero_a_junio_es_el_semestre_2_del_anio_en_curso(self):
        self.assertEqual(semestre_vigente(datetime.date(2027, 1, 1)), "20272")
        self.assertEqual(semestre_vigente(datetime.date(2027, 3, 15)), "20272")
        self.assertEqual(semestre_vigente(datetime.date(2027, 6, 30)), "20272")

    def test_sin_argumento_usa_la_fecha_local(self):
        from django.utils import timezone

        hoy = timezone.localdate()
        esperado = f"{hoy.year}2" if hoy.month <= 6 else f"{hoy.year + 1}1"
        self.assertEqual(semestre_vigente(), esperado)
```

- [ ] **Step 3: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test academico -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'academico.servicios'`.

- [ ] **Step 4: Implementar**

Crear `backend/academico/servicios.py`:

```python
import datetime

from django.utils import timezone


def semestre_vigente(hoy: datetime.date | None = None) -> str:
    """Clave `AAAAN` del semestre en curso según el calendario UNAM.

    Julio–diciembre pertenecen al semestre 1 del año siguiente (2026-08 ->
    "20271"); enero–junio, al semestre 2 del año en curso (2027-03 ->
    "20272"). Es la única fuente de la clave: `PeriodoAcademico` aporta las
    fechas del semestre, no decide cuál es.

    Espejo de `semestreActual` en
    `frontend/src/features/asesorias/logica.ts`.
    """
    if hoy is None:
        hoy = timezone.localdate()
    if hoy.month <= 6:
        return f"{hoy.year}2"
    return f"{hoy.year + 1}1"
```

- [ ] **Step 5: Verificar verde**

Run: `cd backend && uv run manage.py test academico -v 2`
Expected: PASS.

- [ ] **Step 6: Hacer que `asesorias` delegue**

En `backend/asesorias/servicios.py`, reemplazar la función `semestre_vigente` (líneas 14-23) por:

```python
# Reexport: `semestre_vigente` vive en `academico` desde el ADR 0027. La copia
# que estaba aquí usaba la convención vieja (enero–junio -> semestre 1 del año
# en curso) y difería del frontend. Se conserva el nombre importable para no
# tocar los call sites de `asesorias/views.py`.
from academico.servicios import semestre_vigente  # noqa: F401
```

y mover ese `import` al bloque de imports del inicio del archivo (arriba de `def ventana_agendable`).

- [ ] **Step 7: Corregir el test viejo de la heurística**

En `backend/asesorias/tests/test_servicios.py`, reemplazar la clase `SemestreVigenteTests` completa (líneas 33-56) por:

```python
class SemestreVigenteReexportTests(SimpleTestCase):
    def test_es_la_misma_funcion_que_la_de_academico(self):
        from academico.servicios import semestre_vigente as canonica
        from asesorias.servicios import semestre_vigente as reexportada

        self.assertIs(reexportada, canonica)
```

- [ ] **Step 8: Verificar toda la suite**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS. Los tests que fijan `semestre="20271"` en sus fixtures (`test_api_registro.py`, `test_api_admin.py`) siguen pasando porque la clave sigue siendo un `CharField` libre; los que dependen del semestre vigente calculado ahora coinciden con el frontend.

- [ ] **Step 9: Commit**

```bash
git add backend/academico backend/config/settings/base.py backend/asesorias/servicios.py backend/asesorias/tests/test_servicios.py
git commit -s -m "$(cat <<'EOF'
[fix][backend] corregir la heurística del semestre vigente y moverla a la app academico

- crear la app academico con servicios.semestre_vigente (jul–dic -> semestre 1 del año siguiente)
- alinear el backend con la heurística ya corregida del frontend en 1533d53
- dejar asesorias.servicios.semestre_vigente como reexport

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 9: Modelo `PeriodoAcademico` + admin

**Files:**
- Modify: `backend/academico/models.py`, `backend/academico/admin.py`, `backend/academico/servicios.py`
- Create: `backend/academico/migrations/0001_initial.py` (generada)
- Test: `backend/academico/tests/test_periodo.py`

**Interfaces:**
- Consumes: `semestre_vigente` (Task 8).
- Produces:
  - `academico.models.PeriodoAcademico` con `semestre` (único), `fecha_inicio`, `fecha_fin`, `registro_asesores_inicio`, `registro_asesores_fin`, y la propiedad `registro_asesores_abierto: bool`.
  - `academico.servicios.periodo_vigente(hoy=None) -> PeriodoAcademico | None`.
  - `academico.servicios.registro_asesores_abierto(hoy=None) -> bool` — la usa la Task 15.

- [ ] **Step 1: Escribir los tests**

Crear `backend/academico/tests/test_periodo.py`:

```python
import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase

from academico.models import PeriodoAcademico
from academico.servicios import periodo_vigente, registro_asesores_abierto, semestre_vigente


def crear_periodo(semestre="20271", **overrides):
    valores = {
        "fecha_inicio": datetime.date(2026, 8, 10),
        "fecha_fin": datetime.date(2026, 12, 4),
        "registro_asesores_inicio": datetime.date(2026, 7, 1),
        "registro_asesores_fin": datetime.date(2026, 8, 31),
    }
    valores.update(overrides)
    return PeriodoAcademico.objects.create(semestre=semestre, **valores)


class PeriodoAcademicoTests(TestCase):
    def test_semestre_unico(self):
        crear_periodo()
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_periodo()

    def test_registro_abierto_dentro_de_la_ventana(self):
        periodo = crear_periodo()
        self.assertTrue(periodo.esta_abierto_el_registro(datetime.date(2026, 7, 15)))
        self.assertTrue(periodo.esta_abierto_el_registro(datetime.date(2026, 7, 1)))
        self.assertTrue(periodo.esta_abierto_el_registro(datetime.date(2026, 8, 31)))

    def test_registro_cerrado_fuera_de_la_ventana(self):
        periodo = crear_periodo()
        self.assertFalse(periodo.esta_abierto_el_registro(datetime.date(2026, 6, 30)))
        self.assertFalse(periodo.esta_abierto_el_registro(datetime.date(2026, 9, 1)))


class PeriodoVigenteTests(TestCase):
    def test_devuelve_el_periodo_cuya_clave_coincide_con_la_heuristica(self):
        esperado = crear_periodo(semestre=semestre_vigente())
        crear_periodo(semestre="19991")
        self.assertEqual(periodo_vigente(), esperado)

    def test_devuelve_none_si_la_sae_no_dio_de_alta_el_periodo(self):
        crear_periodo(semestre="19991")
        self.assertIsNone(periodo_vigente())

    def test_registro_abierto_es_false_sin_periodo_vigente(self):
        self.assertFalse(registro_asesores_abierto())
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test academico.tests.test_periodo -v 2`
Expected: FAIL — `ImportError: cannot import name 'PeriodoAcademico'`.

- [ ] **Step 3: Implementar el modelo**

Escribir `backend/academico/models.py`:

```python
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PeriodoAcademico(models.Model):
    """Un semestre con sus fechas reales.

    Alta y edición manuales desde el admin de Django por la SAE cada
    semestre, mismo criterio que `PerfilSAE`/`PerfilAsesorAcademico`
    (ADR 0027 decisión 4). No modela subdivisiones internas del calendario
    (exámenes, vacaciones): deuda 0001 queda parcialmente resuelta.
    """

    semestre = models.CharField(max_length=5, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    registro_asesores_inicio = models.DateField()
    registro_asesores_fin = models.DateField()

    class Meta:
        ordering = ["-semestre"]
        verbose_name = "periodo académico"
        verbose_name_plural = "periodos académicos"

    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin del semestre es anterior a la de inicio.")
        if self.registro_asesores_fin < self.registro_asesores_inicio:
            raise ValidationError("La ventana de registro de asesores termina antes de abrir.")

    def esta_abierto_el_registro(self, hoy: datetime.date | None = None) -> bool:
        if hoy is None:
            hoy = timezone.localdate()
        return self.registro_asesores_inicio <= hoy <= self.registro_asesores_fin

    def __str__(self):
        return self.semestre
```

- [ ] **Step 4: Agregar los servicios**

Agregar al final de `backend/academico/servicios.py`:

```python
def periodo_vigente(hoy: datetime.date | None = None):
    """El `PeriodoAcademico` cuya clave coincide con la heurística, o `None`.

    `None` significa "la SAE todavía no dio de alta este semestre", no "no
    hay semestre": la clave siempre existe (ver `semestre_vigente`).
    """
    from academico.models import PeriodoAcademico

    return PeriodoAcademico.objects.filter(semestre=semestre_vigente(hoy)).first()


def registro_asesores_abierto(hoy: datetime.date | None = None) -> bool:
    """Si hoy cae dentro de la ventana de registro del semestre vigente.

    Sin `PeriodoAcademico` dado de alta responde `False`: sin fechas no hay
    forma de afirmar que la ventana está abierta.
    """
    periodo = periodo_vigente(hoy)
    return periodo is not None and periodo.esta_abierto_el_registro(hoy)
```

- [ ] **Step 5: Registrar en el admin**

Escribir `backend/academico/admin.py`:

```python
from django.contrib import admin

from .models import PeriodoAcademico


@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = (
        "semestre", "fecha_inicio", "fecha_fin",
        "registro_asesores_inicio", "registro_asesores_fin",
    )
    ordering = ("-semestre",)
```

- [ ] **Step 6: Generar la migración**

Run: `cd backend && uv run manage.py makemigrations academico`
Expected: `backend/academico/migrations/0001_initial.py`.

- [ ] **Step 7: Verificar verde**

Run: `cd backend && uv run manage.py test academico -v 2`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/academico
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar PeriodoAcademico con fechas de semestre y ventana de registro

- agregar el modelo, su migración y su alta manual en el admin
- agregar periodo_vigente() y registro_asesores_abierto() en academico.servicios

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 10: `GET /api/academico/periodo-vigente/`

**Files:**
- Modify: `backend/academico/serializers.py`, `backend/academico/views.py`, `backend/academico/urls.py`
- Modify: `backend/config/urls.py`
- Test: `backend/academico/tests/test_api.py`

**Interfaces:**
- Consumes: `periodo_vigente()` (Task 9).
- Produces: `GET /api/academico/periodo-vigente/` → `200 {semestre, fecha_inicio, fecha_fin, registro_asesores_inicio, registro_asesores_fin, registro_asesores_abierto}` o `404 {"detail": ...}`. Lo consume `usePeriodoVigente()` (Task 12).

- [ ] **Step 1: Escribir los tests**

Crear `backend/academico/tests/test_api.py`:

```python
import datetime

from rest_framework.test import APITestCase

from academico.servicios import semestre_vigente
from academico.tests.test_periodo import crear_periodo
from accounts.models import User

RUTA = "/api/academico/periodo-vigente/"


class PeriodoVigenteApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="quien.sea@ciencias.unam.mx", password="x")

    def test_requiere_sesion(self):
        self.assertEqual(self.client.get(RUTA).status_code, 401)

    def test_404_si_la_sae_no_dio_de_alta_el_periodo(self):
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get(RUTA).status_code, 404)

    def test_devuelve_el_detalle_del_periodo_vigente(self):
        crear_periodo(
            semestre=semestre_vigente(),
            registro_asesores_inicio=datetime.date(2000, 1, 1),
            registro_asesores_fin=datetime.date(2099, 12, 31),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(RUTA)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["semestre"], semestre_vigente())
        self.assertTrue(response.data["registro_asesores_abierto"])

    def test_registro_cerrado_fuera_de_la_ventana(self):
        crear_periodo(
            semestre=semestre_vigente(),
            registro_asesores_inicio=datetime.date(2000, 1, 1),
            registro_asesores_fin=datetime.date(2000, 1, 31),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(RUTA)
        self.assertFalse(response.data["registro_asesores_abierto"])
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test academico.tests.test_api -v 2`
Expected: FAIL — 404 de Django (la ruta no existe) en todos los casos.

- [ ] **Step 3: Escribir el serializer**

Crear `backend/academico/serializers.py`:

```python
from rest_framework import serializers

from .models import PeriodoAcademico


class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    registro_asesores_abierto = serializers.SerializerMethodField()

    class Meta:
        model = PeriodoAcademico
        fields = [
            "semestre", "fecha_inicio", "fecha_fin",
            "registro_asesores_inicio", "registro_asesores_fin",
            "registro_asesores_abierto",
        ]

    def get_registro_asesores_abierto(self, obj) -> bool:
        return obj.esta_abierto_el_registro()
```

- [ ] **Step 4: Escribir la vista y las rutas**

Escribir `backend/academico/views.py`:

```python
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import PeriodoAcademicoSerializer
from .servicios import periodo_vigente, semestre_vigente


class PeriodoVigenteView(RetrieveAPIView):
    """Detalle del periodo del semestre vigente.

    404 cuando la SAE todavía no lo dio de alta: no es un error del cliente,
    es información — el frontend usa ese 404 para no ofrecer el autoservicio
    de registro de asesor (ADR 0027 decisión 5).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PeriodoAcademicoSerializer

    def get_object(self):
        periodo = periodo_vigente()
        if periodo is None:
            raise NotFound(f"No hay periodo académico dado de alta para {semestre_vigente()}.")
        return periodo
```

Crear `backend/academico/urls.py`:

```python
from django.urls import path

from .views import PeriodoVigenteView

urlpatterns = [
    path("periodo-vigente/", PeriodoVigenteView.as_view(), name="periodo-vigente"),
]
```

En `backend/config/urls.py`, agregar debajo de la línea de `api/auth/`:

```python
    path("api/academico/", include("academico.urls")),
```

- [ ] **Step 5: Verificar verde**

Run: `cd backend && uv run manage.py test academico -v 2`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/academico backend/config/urls.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] exponer GET /api/academico/periodo-vigente/

- agregar la vista de solo lectura del periodo del semestre vigente
- devolver 404 cuando la SAE todavía no dio de alta el periodo

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 11: Acotar oferta, asesores y búsqueda al semestre vigente

Cierra la [deuda 0012](../../technical-debt/0012-oferta-asesorias-sin-scope-de-semestre.md). Además filtra por `asesor__activo=True`: sin eso, el autoservicio de la Fase 4 dejaría que un académico aún no validado publique disponibilidad y aparezca ante los alumnos.

**Files:**
- Modify: `backend/asesorias/views.py:101-210` (`BuscarDisponibilidadView`, `OfertaView`, `AsesoresDeMateriaView`)
- Test: `backend/asesorias/tests/test_api_oferta.py`, `backend/asesorias/tests/test_api_busqueda.py`

**Interfaces:**
- Consumes: `semestre_vigente()` (Task 8).
- Produces: las tres vistas solo consideran `RegistroAsesor` del semestre vigente con `asesor.activo=True`.

- [ ] **Step 1: Escribir los tests**

Agregar a `backend/asesorias/tests/test_api_oferta.py`:

```python
class OfertaScopeSemestreTests(APITestCase):
    """La oferta refleja el semestre vigente y a los asesores activos, no
    todo lo que tenga Disponibilidad.activa (deuda 0012, ADR 0027)."""

    def setUp(self):
        from accounts.models import PerfilAcademico, User
        from accounts.tests.factories import crear_alumno
        from asesorias.models import Disponibilidad, PerfilAsesorAcademico, RegistroAsesor
        from asesorias.servicios import semestre_vigente
        from carreras.models import Area, Carrera
        from materias.models import Materia
        import datetime

        self.area = Area.objects.create(nombre="Area scope")
        self.carrera = Carrera.objects.create(clave=941, nombre="Carrera Scope Test", area=self.area)
        self.materia_vieja = Materia.objects.create(
            clave="1941", nombre="Materia Vieja", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.materia_inactiva = Materia.objects.create(
            clave="1942", nombre="Materia De Inactivo", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )

        def asesor(email, trabajador, activo=True):
            u = User.objects.create_user(email=email, password="x")
            PerfilAcademico.objects.create(user=u, numero_trabajador=trabajador)
            return PerfilAsesorAcademico.objects.create(user=u, area=self.area, activo=activo)

        registro_viejo = RegistroAsesor.objects.create(asesor=asesor("v@ciencias.unam.mx", "94001"), semestre="20191")
        registro_viejo.materias.add(self.materia_vieja)
        registro_inactivo = RegistroAsesor.objects.create(
            asesor=asesor("i@ciencias.unam.mx", "94002", activo=False), semestre=semestre_vigente()
        )
        registro_inactivo.materias.add(self.materia_inactiva)
        for registro in (registro_viejo, registro_inactivo):
            Disponibilidad.objects.create(
                registro=registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
                formato="virtual", liga_virtual="https://zoom.us/j/2", activa=True,
            )

        self.alumno_user = User.objects.create_user(email="alumno.scope@ciencias.unam.mx", password="x")
        crear_alumno(self.alumno_user, "312000033", carrera=self.carrera)
        self.client.force_authenticate(user=self.alumno_user)

    def test_la_oferta_ignora_registros_de_semestres_pasados(self):
        nombres = [fila["nombre"] for fila in self.client.get("/api/asesorias/oferta/").data]
        self.assertNotIn("Materia Vieja", nombres)

    def test_la_oferta_ignora_a_los_asesores_inactivos(self):
        nombres = [fila["nombre"] for fila in self.client.get("/api/asesorias/oferta/").data]
        self.assertNotIn("Materia De Inactivo", nombres)

    def test_asesores_de_materia_ignora_registros_de_semestres_pasados(self):
        response = self.client.get(f"/api/asesorias/oferta/{self.materia_vieja.id}/asesores/")
        self.assertEqual(response.data, [])

    def test_la_busqueda_ignora_registros_de_semestres_pasados(self):
        response = self.client.get(
            f"/api/asesorias/disponibilidad/buscar/?materia={self.materia_vieja.id}"
        )
        self.assertEqual(response.data, [])
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test asesorias.tests.test_api_oferta.OfertaScopeSemestreTests -v 2`
Expected: FAIL — los cuatro tests: hoy las vistas solo miran `Disponibilidad.activa`.

- [ ] **Step 3: Implementar el scope**

En `backend/asesorias/views.py`:

En `BuscarDisponibilidadView.get`, reemplazar la construcción del queryset (línea 110-112) por:

```python
        # Scope de semestre vigente + asesor activo (ADR 0027 decisión 6,
        # cierra la deuda 0012). Antes bastaba con `activa=True`, lo que dejaba
        # agendable un registro de un semestre cerrado.
        disponibilidades = Disponibilidad.objects.filter(
            activa=True,
            registro__semestre=semestre_vigente(),
            registro__asesor__activo=True,
        ).select_related("registro__asesor__user")
```

En `OfertaView.get`, reemplazar la construcción de `materias` (líneas 164-169) por:

```python
        vigentes = Q(
            registros_asesor__semestre=semestre_vigente(),
            registros_asesor__asesor__activo=True,
            registros_asesor__disponibilidades__activa=True,
        )
        materias = (
            Materia.objects.filter(vigentes)
            .annotate(num_asesores=Count("registros_asesor", filter=vigentes, distinct=True))
            .distinct()
            .order_by("nombre")
        )
```

En `AsesoresDeMateriaView.get`, reemplazar el queryset `registros` (líneas 193-198) por:

```python
        registros = (
            RegistroAsesor.objects.filter(
                materias=materia,
                semestre=semestre_vigente(),
                asesor__activo=True,
                disponibilidades__activa=True,
            )
            .select_related("asesor__user", "asesor__area")
            .distinct()
            .order_by("id")
        )
```

- [ ] **Step 4: Verificar verde**

Run: `cd backend && uv run manage.py test asesorias -v 2`
Expected: PASS. Los tests existentes de `test_api_oferta.py` / `test_api_busqueda.py` que crean su `RegistroAsesor` con `semestre="20271"` fijo empezarán a fallar cuando la fecha real deje de caer en 20271; cambiar esos fixtures a `semestre=semestre_vigente()` (import: `from asesorias.servicios import semestre_vigente`).

- [ ] **Step 5: Suite completa**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias
git commit -s -m "$(cat <<'EOF'
[fix][backend] acotar oferta, asesores y búsqueda al semestre vigente

- filtrar las tres vistas por registro del semestre vigente y asesor activo
- dejar de ofrecer registros de semestres cerrados con disponibilidad activa
- cierra la deuda técnica 0012

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 12: Frontend — `usePeriodoVigente()`

**Files:**
- Create: `frontend/src/features/academico/api.ts`
- Create: `frontend/src/features/academico/api.test.ts`
- Modify: `frontend/src/api/types.ts`

**Interfaces:**
- Consumes: `GET /api/academico/periodo-vigente/` (Task 10).
- Produces:
  - `interface PeriodoVigente { semestre, fecha_inicio, fecha_fin, registro_asesores_inicio, registro_asesores_fin, registro_asesores_abierto }`
  - `usePeriodoVigente()` → `UseQueryResult<PeriodoVigente>`
  - `useRegistroAsesoresAbierto(): boolean` — usada por la Task 16.

- [ ] **Step 1: Escribir el test**

Crear `frontend/src/features/academico/api.test.ts`:

```ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import * as client from '../../api/client'
import { ApiError } from '../../api/client'
import { useRegistroAsesoresAbierto } from './api'

function envoltura({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('useRegistroAsesoresAbierto', () => {
  afterEach(() => vi.restoreAllMocks())

  it('es true cuando el periodo vigente reporta la ventana abierta', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue({
      semestre: '20271',
      fecha_inicio: '2026-08-10',
      fecha_fin: '2026-12-04',
      registro_asesores_inicio: '2026-07-01',
      registro_asesores_fin: '2026-08-31',
      registro_asesores_abierto: true,
    })
    const { result } = renderHook(() => useRegistroAsesoresAbierto(), { wrapper: envoltura })
    await waitFor(() => expect(result.current).toBe(true))
  })

  it('es false cuando la SAE todavía no dio de alta el periodo (404)', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new ApiError(404, { detail: 'no hay' }))
    const { result } = renderHook(() => useRegistroAsesoresAbierto(), { wrapper: envoltura })
    await waitFor(() => expect(result.current).toBe(false))
  })
})
```

Renombrar el archivo a `api.test.tsx` si vitest se queja del JSX en `.ts`.

- [ ] **Step 2: Correr para verificar que falla**

Run: `cd frontend && npx vitest run src/features/academico`
Expected: FAIL — no existe `src/features/academico/api`.

- [ ] **Step 3: Agregar el tipo**

En `frontend/src/api/types.ts`, agregar al final:

```ts
/** GET /api/academico/periodo-vigente/. 404 = la SAE no dio de alta el semestre. */
export interface PeriodoVigente {
  semestre: string
  fecha_inicio: string
  fecha_fin: string
  registro_asesores_inicio: string
  registro_asesores_fin: string
  registro_asesores_abierto: boolean
}
```

- [ ] **Step 4: Implementar el hook**

Crear `frontend/src/features/academico/api.ts`:

```ts
import { useQuery } from '@tanstack/react-query'
import { apiGet, ApiError } from '../../api/client'
import type { PeriodoVigente } from '../../api/types'

/**
 * Detalle del periodo vigente. El 404 (la SAE no ha dado de alta el semestre)
 * es una respuesta esperada, no un fallo: se deja pasar como error de la query
 * y quien la consume lo trata como "sin periodo". Sin reintentos, para no
 * insistir sobre un 404 que no va a cambiar en esta sesión.
 */
export function usePeriodoVigente() {
  return useQuery({
    queryKey: ['academico', 'periodo-vigente'],
    queryFn: () => apiGet<PeriodoVigente>('/api/academico/periodo-vigente/'),
    retry: (_conteo, error) => !(error instanceof ApiError && error.status === 404),
    staleTime: 5 * 60 * 1000,
  })
}

/** Si hoy se puede crear el RegistroAsesor del semestre vigente. Sin periodo
 *  dado de alta responde `false`, igual que el backend. */
export function useRegistroAsesoresAbierto(): boolean {
  const { data } = usePeriodoVigente()
  return data?.registro_asesores_abierto === true
}
```

- [ ] **Step 5: Verificar verde**

Run: `cd frontend && npx vitest run src/features/academico && npx tsc -b`
Expected: PASS, sin errores de tipos.

- [ ] **Step 6: Commit**

```bash
git add frontend/src
git commit -s -m "$(cat <<'EOF'
[feat][frontend] consultar el periodo académico vigente

- agregar usePeriodoVigente() y useRegistroAsesoresAbierto()
- tratar el 404 del endpoint como "la SAE no dio de alta el semestre", sin reintentos

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 4 — Autoservicio de asesor

## Task 13: 🛑 STOP — contrato del servicio externo de validación de académicos

**Esta tarea no escribe código. Se detiene y pregunta.**

- [ ] **Step 1: Preguntar a Héctor, con estas palabras**

> Antes de integrar la validación de "académico activo" del autoservicio de asesor necesito el contrato del servicio externo:
> 1. URL base y ruta exacta del endpoint que responde si un número de trabajador corresponde a un académico vigente.
> 2. Método (GET/POST) y forma del request: ¿el número de trabajador va en la ruta, en query string o en el body? ¿Con qué nombre de campo?
> 3. Autenticación: ¿API key en header, Basic, mTLS, IP allowlist? ¿Qué variables de entorno debo agregar a `backend/.env.example` y a los `docker-compose`?
> 4. Forma de la respuesta: ejemplo de un JSON de académico vigente y otro de uno no vigente. ¿Qué campo se lee? ¿Qué status devuelve para "no existe"?
> 5. Comportamiento esperado ante caída/timeout del servicio: ¿la solicitud del asesor se rechaza, o se acepta y queda pendiente de validación?
> 6. ¿Hay un entorno de pruebas contra el que pueda correr, o solo producción?
>
> Mientras tanto voy a construir el endpoint de solicitud con la validación aislada en `validar_academico_activo(numero_trabajador) -> bool`, con un stub que devuelve **`False`**: el `PerfilAsesorAcademico` se crea con `activo=False` y la SAE lo activa desde el admin. Elegí `False` y no `True` porque `activo=True` sin validación dejaría a un académico no vigente publicando disponibilidad y recibiendo alumnos, mientras que `False` solo deja el perfil pendiente — y como los permisos de asesor (`EsAsesorAcademico`) dependen de que el perfil **exista**, no de `activo`, el stub no bloquea el resto del plan: el asesor puede seguir cargando materias y horario.

- [x] **Step 2: Registrar la respuesta**

**Respuesta de Héctor (2026-08-16):** No hay un servicio dedicado con contrato propio. Lo que existe es el directorio público de la Facultad de Ciencias (`https://www.fciencias.unam.mx`), que el propio Héctor ya usa en otro proyecto (DirectorioFC, Apps Script). El orquestador exploró el endpoint en vivo con dos académicos de prueba (Claudia Solís Said, Luis Medrano González) y confirmó:

1. **Búsqueda:** `GET https://www.fciencias.unam.mx/gql/busquedadirectorio/<nombre-url-encoded>` → JSON `{"data":{"busca_directorio":[...]}}`. Sin resultados → `200` con arreglo vacío (nunca 404).
2. **Método:** GET, sin body. El campo de búsqueda es el **nombre completo como texto libre en la ruta**, no un identificador estructurado.
3. **Autenticación:** ninguna — endpoint público. No hace falta agregar variables de entorno.
4. **Detalle con materias/semestre:** `GET https://www.fciencias.unam.mx/directorio/<persona_id>` → HTML con un bloque JSON embebido (`queryData`); `persona__grupos[].calendario__periodo` usa el mismo formato `AAAAN` que `semestre_vigente()` (confirmado: `20271`, `20262`).
5. **Ante caída/timeout:** no hay SLA declarado (es la web pública de la Facultad, no un servicio dedicado) — la solicitud debe tratarse como no confirmada (pendiente), nunca aceptarse a ciegas.
6. **Entorno de pruebas:** solo producción (es el sitio público).

**Limitación real descubierta:** el directorio indexa por **nombre**, no por `numero_trabajador` — no hay forma determinista de correlacionar `PerfilAcademico.numero_trabajador` con una persona del directorio.

**Decisión de Héctor sobre cómo resolverlo:** validación automática **solo** cuando la búsqueda por nombre completo devuelve exactamente un resultado, **y** ese resultado coincide campo a campo (nombre, apellido1, apellido2, limpiando acentos/mayúsculas/espacios) con el nombre esperado. En cualquier otro caso — cero resultados, más de uno, o un nombre que no calza exactamente — la solicitud queda pendiente para que la SAE la valide a mano. "Activo" se define como "imparte clases en el semestre vigente" (`persona__grupos` con `calendario__periodo == semestre_vigente()`), no el campo `nombramientos`/`activo` del adaptador original de Héctor (ese calculaba otra cosa: vigencia del nombramiento, no docencia en el semestre).

Con esto, la Task 14 deja de construir un stub que siempre devuelve `False` y en su lugar integra esta validación real, con matching estricto y fallback pesimista (cualquier error de red/parseo también resuelve a `False`).

- [x] **Step 3: No hay commit en esta tarea.** Continuar a la Task 14.

---

## Task 14: Solicitud de `PerfilAsesorAcademico`

**Files:**
- Modify: `backend/asesorias/models.py:16-30`
- Create: `backend/asesorias/migrations/0006_perfilasesoracademico_solicitado_por_el_usuario.py` (generada)
- Create: `backend/asesorias/validacion_externa.py`
- Modify: `backend/asesorias/permissions.py`, `backend/asesorias/serializers.py`, `backend/asesorias/views.py`, `backend/asesorias/urls.py`
- Test: `backend/asesorias/tests/test_api_solicitud_asesor.py`

**Interfaces:**
- Consumes: `PerfilAcademico`, `carreras.Area`.
- Produces:
  - `asesorias.validacion_externa.validar_academico_activo(numero_trabajador: str) -> bool` (stub: `False`).
  - `asesorias.permissions.EsAcademico`.
  - `POST /api/asesorias/asesores/solicitud/` con body `{"area": <id>}` → `201 {"id", "area", "area_nombre", "activo"}`.

- [ ] **Step 1: Escribir los tests**

Crear `backend/asesorias/tests/test_api_solicitud_asesor.py`:

```python
from unittest.mock import patch

from rest_framework.test import APITestCase

from accounts.models import PerfilAcademico, User
from asesorias.models import PerfilAsesorAcademico
from carreras.models import Area

RUTA = "/api/asesorias/asesores/solicitud/"


class SolicitudAsesorTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area solicitud")
        self.academico_user = User.objects.create_user(email="aca@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.academico_user, numero_trabajador="70001")
        self.externo_user = User.objects.create_user(email="ext@ciencias.unam.mx", password="x")

    def test_requiere_perfil_academico(self):
        self.client.force_authenticate(user=self.externo_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertEqual(response.status_code, 403)

    def test_el_academico_crea_su_perfil_de_asesor(self):
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertEqual(response.status_code, 201)
        perfil = PerfilAsesorAcademico.objects.get(user=self.academico_user)
        self.assertEqual(perfil.area, self.area)
        self.assertTrue(perfil.solicitado_por_el_usuario)

    def test_con_el_stub_el_perfil_nace_inactivo(self):
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertFalse(response.data["activo"])

    def test_se_activa_solo_si_la_validacion_externa_lo_confirma(self):
        self.client.force_authenticate(user=self.academico_user)
        with patch("asesorias.views.validar_academico_activo", return_value=True):
            response = self.client.post(RUTA, {"area": self.area.id})
        self.assertTrue(response.data["activo"])

    def test_no_se_puede_solicitar_dos_veces(self):
        PerfilAsesorAcademico.objects.create(user=self.academico_user, area=self.area)
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": self.area.id})
        self.assertEqual(response.status_code, 409)

    def test_area_inexistente_da_400(self):
        self.client.force_authenticate(user=self.academico_user)
        response = self.client.post(RUTA, {"area": 999999})
        self.assertEqual(response.status_code, 400)
```

Y `backend/asesorias/tests/test_validacion_externa.py`:

```python
from django.test import SimpleTestCase

from asesorias.validacion_externa import validar_academico_activo


class ValidarAcademicoActivoTests(SimpleTestCase):
    def test_el_stub_no_concede_vigencia(self):
        """Contrato del servicio externo pendiente (deuda 0018): el stub es
        pesimista a propósito — nunca concede acceso operativo sin validación."""
        self.assertFalse(validar_academico_activo("70001"))
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `cd backend && uv run manage.py test asesorias.tests.test_api_solicitud_asesor asesorias.tests.test_validacion_externa -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'asesorias.validacion_externa'` y 404 en la ruta.

- [ ] **Step 3: Escribir el punto de validación aislado**

Crear `backend/asesorias/validacion_externa.py`:

```python
def validar_academico_activo(numero_trabajador: str) -> bool:
    """¿Es este número de trabajador el de un académico vigente?

    STUB. El contrato del servicio externo que responde esta pregunta no está
    definido todavía (deuda técnica 0018, ADR 0027 decisión 7). Devuelve
    `False` a propósito: con `False` la solicitud queda pendiente de que la
    SAE la active desde el admin; con `True` un académico no vigente podría
    publicar disponibilidad y recibir alumnos sin que nadie lo revisara.

    Esta es la ÚNICA función que debe cambiar cuando llegue el contrato: ni la
    vista ni el modelo saben cómo se responde la pregunta.
    """
    return False
```

- [ ] **Step 4: Agregar el campo de trazabilidad al modelo**

En `backend/asesorias/models.py`, dentro de `PerfilAsesorAcademico`, debajo de `activo`:

```python
    # Distingue el alta manual de la SAE (False) de una solicitud del propio
    # académico pendiente de validación externa (True). Sin esto, la SAE no
    # puede filtrar en el admin qué perfiles inactivos esperan su revisión.
    solicitado_por_el_usuario = models.BooleanField(default=False)
```

Run: `cd backend && uv run manage.py makemigrations asesorias --name perfilasesoracademico_solicitado_por_el_usuario`
Expected: `backend/asesorias/migrations/0006_....py`.

- [ ] **Step 5: Agregar el permiso**

En `backend/asesorias/permissions.py`, agregar:

```python
class EsAcademico(BasePermission):
    message = "Se requiere un perfil de académico."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_academico")
```

- [ ] **Step 6: Agregar el serializer**

En `backend/asesorias/serializers.py`, agregar (y ampliar el import de `.models` con `PerfilAsesorAcademico`, y el de `carreras.models` con `Area`):

```python
class SolicitudAsesorSerializer(serializers.ModelSerializer):
    """Body de POST /asesorias/asesores/solicitud/.

    El único campo que el usuario elige es `area`: `user` sale de la sesión y
    `activo` de la validación externa, nunca del payload.
    """

    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    area_nombre = serializers.CharField(source="area.nombre", read_only=True)

    class Meta:
        model = PerfilAsesorAcademico
        fields = ["id", "area", "area_nombre", "activo"]
        read_only_fields = ["id", "activo"]
```

- [ ] **Step 7: Agregar la vista y la ruta**

En `backend/asesorias/views.py`, agregar al final del archivo:

```python
class SolicitudAsesorView(APIView):
    """Autoservicio de alta como asesor académico (ADR 0027 decisión 7).

    Cierra la deuda 0002: la SAE deja de crear el perfil a mano; solo lo
    activa. La vigencia del académico la responde `validar_academico_activo`,
    hoy un stub (deuda 0018).
    """

    permission_classes = [EsAcademico]

    def post(self, request):
        if hasattr(request.user, "perfil_asesor_academico"):
            return Response(
                {"detail": "Ya tienes un perfil de asesor académico."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = SolicitudAsesorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activo = validar_academico_activo(request.user.perfil_academico.numero_trabajador)
        perfil = serializer.save(
            user=request.user, activo=activo, solicitado_por_el_usuario=True
        )
        return Response(
            SolicitudAsesorSerializer(perfil).data, status=status.HTTP_201_CREATED
        )
```

Ampliar los imports del archivo:

```python
from .permissions import (
    EsAcademico, EsAlumno, EsAlumnoOAsesorAcademico, EsAlumnoOMiembroSAE, EsAsesorAcademico,
    EsMiembroSAE, EsDuenoDelRegistro, EsDuenoDeLaAsesoria,
)
from .serializers import (
    AsesorDetalleAdminSerializer, MateriaDelRegistroSerializer, AsesoriaSerializer, CancelarSerializer,
    DesactivarDisponibilidadSerializer, DisponibilidadSerializer, MarcarAsistenciaSerializer, NotasSerializer,
    RegistroAsesorSerializer, ResultadoBusquedaSerializer, SesionFuturaSerializer, SolicitudAsesorSerializer,
)
from .validacion_externa import validar_academico_activo
```

En `backend/asesorias/urls.py`, agregar `SolicitudAsesorView` al import y este `path` a `urlpatterns`:

```python
    path("asesores/solicitud/", SolicitudAsesorView.as_view(), name="asesor-solicitud"),
```

- [ ] **Step 8: Mostrar el estado de solicitud en el admin**

En `backend/asesorias/admin.py`, en el `ModelAdmin` de `PerfilAsesorAcademico`, agregar `"solicitado_por_el_usuario"` a `list_display` y a `list_filter` (si el archivo no lo registra todavía con un `ModelAdmin` propio, registrarlo así):

```python
@admin.register(PerfilAsesorAcademico)
class PerfilAsesorAcademicoAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "activo", "solicitado_por_el_usuario")
    list_filter = ("activo", "solicitado_por_el_usuario", "area")
    search_fields = ("user__email",)
```

- [ ] **Step 9: Verificar verde**

Run: `cd backend && uv run manage.py test asesorias -v 2`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add backend/asesorias
git commit -s -m "$(cat <<'EOF'
[feat][backend] permitir que un académico solicite su perfil de asesor

- agregar POST /api/asesorias/asesores/solicitud/ con permiso EsAcademico
- aislar la vigencia del académico en validar_academico_activo (stub que devuelve False)
- marcar el perfil con solicitado_por_el_usuario para que la SAE filtre los pendientes

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 15: `POST /registros/` acotado a la ventana de registro

**Files:**
- Modify: `backend/asesorias/serializers.py` (`RegistroAsesorSerializer`)
- Test: `backend/asesorias/tests/test_api_registro.py`

**Interfaces:**
- Consumes: `academico.servicios.registro_asesores_abierto`, `semestre_vigente` (Tasks 8-9).
- Produces: `POST /api/asesorias/registros/` acepta solo el semestre vigente y solo con la ventana abierta; `GET`/materias siguen sin restricción.

- [x] **Step 1: Escribir los tests**

Agregar a `backend/asesorias/tests/test_api_registro.py`:

```python
class VentanaDeRegistroTests(APITestCase):
    def setUp(self):
        import datetime

        from academico.models import PeriodoAcademico
        from academico.servicios import semestre_vigente
        from accounts.models import PerfilAcademico, User
        from asesorias.models import PerfilAsesorAcademico
        from carreras.models import Area

        self.semestre = semestre_vigente()
        self.area = Area.objects.create(nombre="Area ventana")
        self.user = User.objects.create_user(email="ventana@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.user, numero_trabajador="70099")
        PerfilAsesorAcademico.objects.create(user=self.user, area=self.area)
        self.PeriodoAcademico = PeriodoAcademico
        self.date = datetime.date
        self.client.force_authenticate(user=self.user)

    def _periodo(self, inicio, fin):
        return self.PeriodoAcademico.objects.create(
            semestre=self.semestre,
            fecha_inicio=self.date(2000, 1, 1), fecha_fin=self.date(2099, 12, 31),
            registro_asesores_inicio=inicio, registro_asesores_fin=fin,
        )

    def test_sin_periodo_dado_de_alta_no_se_puede_registrar(self):
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 400)

    def test_con_la_ventana_abierta_se_crea(self):
        self._periodo(self.date(2000, 1, 1), self.date(2099, 12, 31))
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 201)

    def test_con_la_ventana_cerrada_se_rechaza(self):
        self._periodo(self.date(2000, 1, 1), self.date(2000, 1, 31))
        response = self.client.post("/api/asesorias/registros/", {"semestre": self.semestre})
        self.assertEqual(response.status_code, 400)

    def test_no_se_puede_registrar_un_semestre_que_no_es_el_vigente(self):
        self._periodo(self.date(2000, 1, 1), self.date(2099, 12, 31))
        response = self.client.post("/api/asesorias/registros/", {"semestre": "19991"})
        self.assertEqual(response.status_code, 400)
```

- [x] **Step 2: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test asesorias.tests.test_api_registro.VentanaDeRegistroTests -v 2`
Expected: FAIL — los cuatro casos devuelven 201.

- [x] **Step 3: Implementar la validación**

En `backend/asesorias/serializers.py`, reemplazar `RegistroAsesorSerializer` (líneas 10-14) por:

```python
class RegistroAsesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroAsesor
        fields = ["id", "semestre", "materias"]
        read_only_fields = ["materias"]

    def validate_semestre(self, value):
        """El autoservicio solo crea el registro del semestre vigente, y solo
        dentro de la ventana que fija `PeriodoAcademico` (ADR 0027 decisión 8).

        Solo aplica al alta: gestionar materias y horario de un registro que ya
        existe (incluido el de un semestre pasado) no pasa por aquí.
        """
        vigente = semestre_vigente()
        if value != vigente:
            raise serializers.ValidationError(
                f"Solo puedes registrarte en el semestre vigente ({vigente})."
            )
        if not registro_asesores_abierto():
            raise serializers.ValidationError(
                "El registro de asesores no está abierto para este semestre."
            )
        return value
```

y agregar al bloque de imports del archivo:

```python
from academico.servicios import registro_asesores_abierto, semestre_vigente
```

- [x] **Step 4: Verificar verde**

Run: `cd backend && uv run manage.py test asesorias -v 2`
Expected: PASS. Los tests preexistentes que hacen `POST /api/asesorias/registros/` (`test_api_registro.test_asesor_crea_su_registro`) necesitarán ahora un `PeriodoAcademico` del semestre vigente con ventana abierta en su `setUp`, y `semestre=semestre_vigente()` en vez de `"20271"`. Agregarlo.

- [x] **Step 5: Suite completa**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add backend/asesorias
git commit -s -m "$(cat <<'EOF'
[feat][backend] acotar el alta de RegistroAsesor a la ventana del periodo vigente

- rechazar POST /registros/ fuera de registro_asesores_inicio..fin y para semestres no vigentes
- dejar intacta la gestión de materias y horario de registros ya existentes

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Task 16: Frontend — `useEsAcademico`, ruta de solicitud y ventana de registro

**Files:**
- Modify: `frontend/src/auth/rol.ts`, `frontend/src/auth/rol.test.tsx`
- Modify: `frontend/src/auth/AuthContext.tsx` (`refrescarSesion`)
- Modify: `frontend/src/auth/RutaProtegida.tsx`, `frontend/src/auth/RutaProtegida.test.tsx`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/features/asesorias/screens/SolicitudAsesor.tsx` + `.test.tsx`
- Modify: `frontend/src/features/asesorias/api.ts`
- Modify: `frontend/src/features/asesorias/screens/Asesorias.tsx` + `.test.tsx`
- Modify: `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx` + `.test.tsx`

**Interfaces:**
- Consumes: `useRegistroAsesoresAbierto()` (Task 12), `POST /asesorias/asesores/solicitud/` (Task 14).
- Produces:
  - `useEsAcademico(): boolean` en `auth/rol.ts`.
  - `RutaDeAcademico` en `auth/RutaProtegida.tsx`.
  - `useSolicitarSerAsesor()` en `features/asesorias/api.ts`, `mutationFn: (areaId: number) => Promise<PerfilAsesorAcademico>`.
  - `refrescarSesion(): Promise<void>` en el valor de `useAuth()`.
  - Ruta `/asesorias/soy-asesor`.

- [x] **Step 1: Escribir los tests de rol y guard**

En `frontend/src/auth/rol.test.tsx`, agregar al final:

```tsx
function SondaAcademico() {
  const esAcademico = useEsAcademico()
  return <div data-testid="academico">{`academico=${esAcademico}`}</div>
}

describe('useEsAcademico', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reconoce al académico sin perfil de asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico'],
        perfil_academico: { id: 7, numero_trabajador: '70001' },
      }),
    )
    render(
      <AuthProvider>
        <SondaAcademico />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('academico')).toHaveTextContent('academico=true'))
  })

  it('no reconoce como académico a un alumno', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    render(
      <AuthProvider>
        <SondaAcademico />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('academico')).toHaveTextContent('academico=false'))
  })
})
```

(agregar `useEsAcademico` al import de `./rol` en la línea 4.)

En `frontend/src/auth/RutaProtegida.test.tsx`, agregar un caso siguiendo el patrón que ya usa el archivo para `RutaDeAsesorias`:

```tsx
  it('RutaDeAsesorias deja pasar al académico sin perfil de asesor', () => {
    // Es la puerta al autoservicio de registro: sin esto, un académico que
    // toca el tile de Asesorías rebota a /home y no encuentra dónde darse de alta.
    montarRuta(<RutaDeAsesorias><p>contenido</p></RutaDeAsesorias>, { roles: ['academico'] })
    expect(screen.getByText('contenido')).toBeInTheDocument()
  })
```

Ajustar `montarRuta` al helper real del archivo.

- [x] **Step 2: Correr para verificar que fallan**

Run: `cd frontend && npx vitest run src/auth`
Expected: FAIL — `useEsAcademico` no existe.

- [x] **Step 3: Implementar el hook y los guards**

En `frontend/src/auth/rol.ts`, agregar al final:

```ts
/**
 * Académico (ADR 0012: existe `PerfilAcademico`). Es distinto de `useEsAsesor`:
 * un académico sin `PerfilAsesorAcademico` todavía no es asesor, y este hook es
 * lo único que le permite descubrir que puede registrarse (ADR 0027 decisión 9).
 */
export function useEsAcademico(): boolean {
  return useAuth().roles.includes('academico')
}
```

En `frontend/src/auth/RutaProtegida.tsx`:
- agregar `useEsAcademico` al import de `./rol`;
- en `RutaDeAsesorias`, agregar `const esAcademico = useEsAcademico()` y cambiar la condición por `if (!esAsesor && !esAlumno && !esAcademico) return <Navigate to="/home" replace />`;
- agregar al final del archivo:

```tsx
export function RutaDeAcademico({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAcademico = useEsAcademico()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esAcademico) return <Navigate to="/home" replace />

  return <>{children}</>
}
```

- [x] **Step 4: Verificar verde**

Run: `cd frontend && npx vitest run src/auth`
Expected: PASS.

- [x] **Step 5: Escribir el test de la pantalla de solicitud**

Crear `frontend/src/features/asesorias/screens/SolicitudAsesor.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SolicitudAsesor } from './SolicitudAsesor'
import * as client from '../../../api/client'
import * as auth from '../../../auth/AuthContext'
import { usuarioDePrueba } from '../../../test/factories'

function montar() {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: usuarioDePrueba({ roles: ['academico'] }),
    roles: ['academico'],
    status: 'authenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
    refrescarSesion: vi.fn().mockResolvedValue(undefined),
  } as ReturnType<typeof auth.useAuth>)

  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SolicitudAsesor />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('SolicitudAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('envía el área elegida y avisa que queda pendiente de validación', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue([{ id: 2, nombre: 'Matemáticas' }])
    const apiPost = vi
      .spyOn(client, 'apiPost')
      .mockResolvedValue({ id: 3, area: 2, area_nombre: 'Matemáticas', activo: false })

    montar()
    fireEvent.change(await screen.findByLabelText('Área'), { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Solicitar' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/asesorias/asesores/solicitud/', { area: 2 }),
    )
    expect(await screen.findByText(/pendiente de que la SAE/i)).toBeInTheDocument()
  })
})
```

- [x] **Step 6: Correr para verificar que falla**

Run: `cd frontend && npx vitest run src/features/asesorias/screens/SolicitudAsesor.test.tsx`
Expected: FAIL — no existe `./SolicitudAsesor`.

- [x] **Step 7: Implementar la mutación y la pantalla**

Primero, `AuthContext` **no** usa TanStack Query: carga la sesión con un `apiGet` dentro de un `useEffect` y la guarda en `useState`, así que no hay caché que invalidar. Para que `roles` incluya `asesor_academico` justo después de la solicitud, en `frontend/src/auth/AuthContext.tsx`:

- agregar `refrescarSesion: () => Promise<void>` a `interface AuthContextValue`;
- definirla dentro de `AuthProvider`, arriba del `return`:

```tsx
  /** Vuelve a pedir la sesión al backend. Lo necesita cualquier acción que
   *  cambie los roles del propio usuario — hoy, el autoservicio de asesor:
   *  sin esto, `roles` seguiría sin `asesor_academico` hasta recargar. */
  async function refrescarSesion() {
    try {
      setUser(await apiGet<AuthUser>('/api/auth/user/'))
      setStatus('authenticated')
    } catch {
      setStatus('unauthenticated')
    }
  }
```

- e incluirla en el objeto que se pasa a `AuthContext.Provider`.

Cada test que hace `vi.spyOn(auth, 'useAuth').mockReturnValue({...})` (`Home.test.tsx`, `MenuUsuario.test.tsx` y los que use `RutaProtegida.test.tsx`) necesita `refrescarSesion: vi.fn()` en su doble; el `as ReturnType<typeof auth.useAuth>` que ya llevan no lo detecta, pero el typecheck del provider sí.

En `frontend/src/features/asesorias/api.ts`, agregar (importando `PerfilAsesorAcademico` de `../../api/types`):

```ts
/** Autoservicio de alta como asesor (ADR 0027 decisión 7). El perfil puede
 *  nacer inactivo: la vigencia la confirma un servicio externo. Quien la use
 *  debe llamar a `refrescarSesion()` de `useAuth` para que `roles` incluya
 *  `asesor_academico` sin recargar la página. */
export function useSolicitarSerAsesor() {
  return useMutation({
    mutationFn: (areaId: number) =>
      apiPost<PerfilAsesorAcademico>('/api/asesorias/asesores/solicitud/', { area: areaId }),
  })
}
```

Crear `frontend/src/features/asesorias/screens/SolicitudAsesor.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { apiGet } from '../../../api/client'
import { primerMensajeDeError } from '../../../api/errores'
import { useAuth } from '../../../auth/AuthContext'
import { Boton } from '../../../components/ui/Boton'
import { useSolicitarSerAsesor } from '../api'

interface Area {
  id: number
  nombre: string
}

export function SolicitudAsesor() {
  const navigate = useNavigate()
  const { data: areas = [] } = useQuery({
    queryKey: ['areas'],
    queryFn: () => apiGet<Area[]>('/api/carreras/areas/'),
    staleTime: Infinity,
  })
  const solicitar = useSolicitarSerAsesor()
  const { refrescarSesion } = useAuth()
  const [area, setArea] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [listo, setListo] = useState(false)

  if (listo) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <h1 className="text-lg font-semibold text-on-background">Solicitud enviada</h1>
        <p className="text-sm text-on-surface-variant">
          Tu perfil de asesor quedó pendiente de que la SAE confirme que tu nombramiento
          está vigente. Mientras tanto ya puedes cargar tus materias y tu horario.
        </p>
        <Boton type="button" onClick={() => navigate('/asesorias')} className="w-fit px-6">
          Ir a Asesorías
        </Boton>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit min-h-11 text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">Registrarme como asesor</h1>
      <p className="text-sm text-on-surface-variant">
        Elige el área en la que darás asesorías. La SAE confirmará que tu nombramiento
        esté vigente antes de publicar tu disponibilidad.
      </p>

      {error && <p role="alert" className="text-xs text-error">{error}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="area-solicitud" className="text-xs text-on-surface-variant">Área</label>
        <select
          id="area-solicitud"
          value={area ?? ''}
          onChange={(e) => setArea(e.target.value === '' ? null : Number(e.target.value))}
          className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
        >
          <option value="">Elige un área</option>
          {areas.map((a) => (
            <option key={a.id} value={a.id}>{a.nombre}</option>
          ))}
        </select>
      </div>

      <Boton
        type="button"
        disabled={area === null}
        cargando={solicitar.isPending}
        onClick={() => {
          if (area === null) return
          setError(null)
          solicitar.mutate(area, {
            onSuccess: async () => {
              await refrescarSesion()
              setListo(true)
            },
            onError: (err) => setError(primerMensajeDeError(err)),
          })
        }}
        className="w-fit px-6"
      >
        Solicitar
      </Boton>
    </main>
  )
}
```

- [x] **Step 8: Registrar la ruta**

En `frontend/src/App.tsx`, agregar `RutaDeAcademico` al import de `./auth/RutaProtegida`, `SolicitudAsesor` al de screens, y esta ruta antes de `/asesorias/:id`:

```tsx
        <Route
          path="/asesorias/soy-asesor"
          element={
            <RutaDeAcademico>
              <SolicitudAsesor />
            </RutaDeAcademico>
          }
        />
```

Nota de orden: `/asesorias/soy-asesor` debe declararse **antes** que `/asesorias/:id` para que el segmento literal gane sobre el paramétrico.

- [x] **Step 9: Ofrecer la entrada desde `Asesorias.tsx`**

En `frontend/src/features/asesorias/screens/Asesorias.tsx`, agregar `useEsAcademico` al import de `'../../../auth/rol'`, `const esAcademico = useEsAcademico()` junto a los otros hooks, y dentro del `<div className="flex gap-2">`, antes del bloque `{esAlumno && ...}`:

```tsx
        {esAcademico && !esAsesor && (
          <button
            type="button"
            onClick={() => navigate('/asesorias/soy-asesor')}
            className="foco-visible min-h-11 flex-1 rounded-full bg-primary px-3 text-sm font-semibold text-on-primary"
          >
            Registrarme como asesor
          </button>
        )}
```

- [x] **Step 10: Gatear `SinRegistroAsesor` por la ventana**

En `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx`:
- agregar `import { useRegistroAsesoresAbierto } from '../../academico/api'`;
- agregar `const ventanaAbierta = useRegistroAsesoresAbierto()`;
- reemplazar el `<div>` del input de semestre y el `<Boton>` por:

```tsx
      {ventanaAbierta ? (
        <Boton
          type="button"
          cargando={crearRegistro.isPending}
          onClick={() => crearRegistro.mutate(semestre, { onSuccess: () => mostrar('Registro creado') })}
          className="w-fit px-6"
        >
          Registrar semestre {semestre}
        </Boton>
      ) : (
        <p className="text-sm text-on-surface-variant">
          El registro de asesores para {semestre} no está abierto. La SAE publica las fechas
          de cada semestre.
        </p>
      )}
```

y borrar el `useState` de `semestre` editable a favor de una constante — el backend solo acepta el vigente (Task 15), así que dejar el campo editable ofrece algo que siempre falla:

```tsx
  const semestre = semestreActual()
```

(quitando el `import { useState } from 'react'` si queda sin uso).

Actualizar `SinRegistroAsesor.test.tsx`: los casos que escribían en el input de semestre pasan a asumir el vigente, y agregar uno nuevo:

```tsx
  it('no ofrece registrar cuando la ventana está cerrada', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new ApiError(404, { detail: 'no hay periodo' }))
    montar()
    expect(await screen.findByText(/no está abierto/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Registrar semestre/ })).not.toBeInTheDocument()
  })
```

- [x] **Step 11: Verificar verde**

Run: `cd frontend && npx vitest run && npx tsc -b && npm run lint`
Expected: PASS, sin errores.

- [x] **Step 12: Commit**

```bash
git add frontend/src
git commit -s -m "$(cat <<'EOF'
[feat][frontend] autoservicio de alta como asesor académico

- agregar useEsAcademico y el guard RutaDeAcademico
- agregar la pantalla /asesorias/soy-asesor y su mutación de solicitud
- dejar entrar al académico sin perfil de asesor a /asesorias y ofrecerle el alta
- ofrecer el alta de registro solo dentro de la ventana del periodo vigente

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 5 — Carga masiva de alumnos

## Task 17: 🛑 STOP — columnas del CSV real de alumnos

**Esta tarea no escribe código. Se detiene y pregunta.**

- [ ] **Step 1: Preguntar a Héctor, con estas palabras**

> Antes de escribir el management command `cargar_alumnos` necesito el CSV real:
> 1. El encabezado exacto del archivo (la primera línea, tal cual, con acentos y mayúsculas como vengan).
> 2. Una o dos filas de ejemplo (pueden ser inventadas, pero con el formato real de cada columna).
> 3. El mapeo columna → campo:
>    - **`User`**: ¿qué columna es el correo principal (el de login)? ¿Y `first_name`, `apellido1`, `apellido2` — vienen separados o en una sola columna de nombre completo? Si vienen juntos, ¿en qué orden?
>    - **`PerfilAlumno`**: ¿qué columna es `numero_cuenta`? ¿Qué columnas son correos alternos, y cuántas puede haber?
>    - **`HistoriaAcademica`**: ¿qué columna es la carrera, y cómo viene escrita (nombre, clave numérica, abreviatura)? ¿Qué columna es la generación, y en qué formato (`2023`, `2023-1`, `23`)?
> 4. Un alumno con dos carreras, ¿viene en dos filas con el mismo número de cuenta, o en una fila con dos columnas de carrera?
> 5. ¿Qué hago con una fila cuyo correo ya existe con otro número de cuenta? ¿Es un error de fila, o hay que actualizar?
> 6. ¿El comando debe poder correrse varias veces sobre el mismo archivo sin duplicar nada? (Asumo que sí — upsert por `numero_cuenta`, igual que `cargar_materias`.)
>
> Con eso escribo el comando siguiendo el patrón de `cargar_materias`: upsert por llave natural, reporte de creados/actualizados/errores por fila, sin abortar la carga completa por una fila mala.

- [x] **Step 2: Registrar la respuesta**

**Respuesta de Héctor (2026-08-17):**

Encabezado real (separado por tabs en el ejemplo, tratado como CSV estándar):

```
cuenta	ap1	ap2	nombre	carrera_id	curp	correo	gen
```

Fila de ejemplo (datos ficticios — no corresponden a una persona real):

```
312099999	Pérez	Gómez	Juan	122	PEGJ000101HDFXXX00	juan.perez@ciencias.unam.mx	2026
```

Mapeo columna → campo:
- `cuenta` → `PerfilAlumno.numero_cuenta` (llave natural del upsert).
- `ap1` / `ap2` → `User.apellido1` / `apellido2`. `nombre` → `User.first_name`.
- `correo` → `User.email` (login) **solo si el número de cuenta es nuevo**.
- `carrera_id` → clave numérica; resuelve contra `Carrera.clave` (no contra el nombre — a diferencia de `cargar_materias`, que resuelve por texto con `Carrera.objects.resolve`).
- `gen` → `HistoriaAcademica.generacion`.
- `curp` → columna nueva, sin campo existente. Decisión: agregar `User.curp` (`CharField`, `unique=True, null=True, blank=True` — es la llave única de población pero no obligatoria; `null=True` para que Postgres permita varias filas sin CURP bajo el `unique`).

Multi-carrera: **dos filas con el mismo `cuenta`**, una por carrera — confirmado. El comando crea/actualiza una `HistoriaAcademica` por fila vía `update_or_create(perfil_alumno, carrera)`.

Conflicto de correo: si `numero_cuenta` ya existe y el `correo` de la fila es distinto al `User.email` guardado, **no se pisa el correo de login** — el correo de la fila se agrega a `PerfilAlumno.correos_alternos` (sin duplicar, mismo criterio que la Task 14/`correos_alternos`). El caso inverso — un `correo` que ya pertenece a otro `numero_cuenta` — no lo cubrió la respuesta explícitamente; como `User.email` es `unique`, ese choque revienta como `IntegrityError` al crear el `User` nuevo y cae al mismo manejo de "fila con error" que ya usa el comando (no aborta la carga completa) — coherente con el resto del contrato, así que no hace falta una rama especial.

Re-corrible: sí, upsert por `numero_cuenta` (igual que `cargar_materias` upsertea por `Clave`).

- [x] **Step 3: No hay commit en esta tarea.** Continuar a la Task 18.

---

## Task 18: Management command `cargar_alumnos`

**Contrato real (Task 17), no hipotético.** Encabezado del CSV: `cuenta,ap1,ap2,nombre,carrera_id,curp,correo,gen`. `carrera_id` resuelve contra `Carrera.clave` (numérico), no contra el nombre. Sin columna de correo alterno: el correo alterno se detecta comparando el `correo` de la fila contra el `User.email` ya guardado cuando `cuenta` ya existe.

**Files:**
- Modify: `backend/accounts/models.py` (agregar `User.curp`), migración nueva
- Create: `backend/accounts/management/__init__.py`, `backend/accounts/management/commands/__init__.py`, `backend/accounts/management/commands/cargar_alumnos.py`
- Test: `backend/accounts/tests/test_cargar_alumnos.py`

**Interfaces:**
- Consumes: `User`, `PerfilAlumno`, `HistoriaAcademica`, `Carrera` (por `clave`).
- Produces: `uv run manage.py cargar_alumnos <csv_path>`. `User.curp: str | None`.

- [x] **Step 0: Agregar `User.curp`**

En `backend/accounts/models.py`, en `class User`, después de `apellido2`:

```python
    curp = models.CharField(
        _("CURP"), max_length=18, unique=True, null=True, blank=True,
    )
```

`null=True` (no solo `blank=True`): Postgres permite varias filas `NULL` bajo un `unique`, pero no varias cadenas vacías — y el CURP no es obligatorio (ADR: dato de identidad, pero la carga no debe fallar si falta).

Run: `cd backend && uv run manage.py makemigrations accounts`
Expected: crea `backend/accounts/migrations/0009_user_curp.py` (o el número que siga).

- [x] **Step 1: Escribir los tests**

Crear `backend/accounts/tests/test_cargar_alumnos.py`:

```python
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
```

- [x] **Step 2: Correr para verificar que falla**

Run: `cd backend && uv run manage.py test accounts.tests.test_cargar_alumnos -v 2`
Expected: FAIL — `CommandError: Unknown command: 'cargar_alumnos'`.

- [x] **Step 3: Implementar el comando**

Crear los `__init__.py` vacíos de `accounts/management/` y `accounts/management/commands/`, y `backend/accounts/management/commands/cargar_alumnos.py`:

```python
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
```

- [x] **Step 4: Verificar verde**

Run: `cd backend && uv run manage.py test accounts.tests.test_cargar_alumnos -v 2`
Expected: PASS.

- [x] **Step 5: Documentar el comando**

En `docs/development/getting-started.md`, en la sección "Comandos útiles", agregar:

```
uv run manage.py cargar_materias <csv>   # catálogo de materias
uv run manage.py cargar_alumnos <csv>    # padrón de alumnos (upsert por número de cuenta)
```

- [x] **Step 6: Suite completa**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add backend/accounts docs/development/getting-started.md
git commit -s -m "$(cat <<'EOF'
[feat][backend] agregar el management command cargar_alumnos

- agregar User.curp (opcional, único)
- cargar User, PerfilAlumno e HistoriaAcademica desde un CSV, con upsert por número de cuenta
- resolver carrera_id contra Carrera.clave; aceptar varias carreras por alumno (una fila por carrera)
- si la cuenta ya existe con otro correo, guardarlo como alterno sin pisar el de login
- reportar creados/actualizados/errores por fila sin abortar la carga completa

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 6 — Home

## Task 19: Home con tiles reales gateados por rol

**Files:**
- Modify: `frontend/src/screens/Home.tsx`
- Modify: `frontend/src/screens/Home.test.tsx`
- Delete: `frontend/src/data/services.ts`
- Modify: `frontend/src/components/icons/ServiceIcons.tsx`

**Interfaces:**
- Consumes: `useEsAlumno`, `useEsAcademico`, `useEsMiembroSAE` (Task 16).
- Produces: nada que consuman tareas posteriores.

- [x] **Step 1: Reescribir el test**

Reemplazar `frontend/src/screens/Home.test.tsx` completo por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Home } from './Home'
import * as rol from '../auth/rol'
import * as auth from '../auth/AuthContext'
import { usuarioDePrueba } from '../test/factories'

interface Roles {
  alumno?: boolean
  academico?: boolean
  sae?: boolean
}

function montar({ alumno = false, academico = false, sae = false }: Roles = {}) {
  vi.spyOn(rol, 'useEsAlumno').mockReturnValue(alumno)
  vi.spyOn(rol, 'useEsAcademico').mockReturnValue(academico)
  vi.spyOn(rol, 'useEsMiembroSAE').mockReturnValue(sae)
  // Home monta MenuUsuario, que llama a useAuth: sin este doble el hook
  // lanza por falta de AuthProvider.
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: usuarioDePrueba(),
    roles: [],
    status: 'authenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
    refrescarSesion: vi.fn().mockResolvedValue(undefined),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/asesorias" element={<p>pantalla de asesorías</p>} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Home', () => {
  afterEach(() => vi.restoreAllMocks())

  it('no pinta ningún servicio mock', () => {
    montar({ alumno: true })
    expect(screen.queryByText('Becas')).not.toBeInTheDocument()
    expect(screen.queryByText('Movilidad')).not.toBeInTheDocument()
  })

  it('ofrece Asesorías al alumno', () => {
    montar({ alumno: true })
    fireEvent.click(screen.getByRole('button', { name: 'Asesorías' }))
    expect(screen.getByText('pantalla de asesorías')).toBeInTheDocument()
  })

  it('ofrece Asesorías al académico', () => {
    montar({ academico: true })
    expect(screen.getByRole('button', { name: 'Asesorías' })).toBeInTheDocument()
  })

  it('ofrece el panel SAE al miembro de la SAE', () => {
    montar({ sae: true })
    fireEvent.click(screen.getByRole('button', { name: 'Asesorías · SAE' }))
    expect(screen.getByText('área SAE')).toBeInTheDocument()
  })

  it('el alumno no ve el panel SAE', () => {
    montar({ alumno: true })
    expect(screen.queryByRole('button', { name: 'Asesorías · SAE' })).not.toBeInTheDocument()
  })

  it('muestra una leyenda cuando ningún servicio aplica', () => {
    montar()
    expect(screen.getByText('Aún no contamos con servicios para ti.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Asesorías' })).not.toBeInTheDocument()
  })

  it('la hamburguesa del header abre el menú de la sesión', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Menú' }))
    expect(screen.getByText('usuaria@ciencias.unam.mx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })
})
```

- [x] **Step 2: Correr para verificar que falla**

Run: `cd frontend && npx vitest run src/screens/Home.test.tsx`
Expected: FAIL — sigue apareciendo "Becas" y no existe el tile "Asesorías".

- [x] **Step 3: Reescribir la pantalla**

Reemplazar `frontend/src/screens/Home.tsx` completo por:

```tsx
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { MenuUsuario } from '../components/MenuUsuario'
import { IconTutorias } from '../components/icons/ServiceIcons'
import { useEsAcademico, useEsAlumno, useEsMiembroSAE } from '../auth/rol'

/**
 * Los tiles son los servicios que existen de verdad y que este usuario puede
 * usar, no un catálogo aspiracional (ADR 0027 decisión 9). Se arman en el
 * cliente a partir de `roles`: todavía no hay un endpoint de catálogo de
 * servicios de la SAE (deuda 0019).
 */
export function Home() {
  const navigate = useNavigate()
  const esAlumno = useEsAlumno()
  const esAcademico = useEsAcademico()
  const esMiembroSAE = useEsMiembroSAE()

  const tiles = [
    {
      id: 'asesorias',
      etiqueta: 'Asesorías',
      ruta: '/asesorias',
      visible: esAlumno || esAcademico,
      containerClassName: 'bg-primary-container text-on-primary-container',
    },
    {
      id: 'sae-asesorias',
      etiqueta: 'Asesorías · SAE',
      ruta: '/sae/asesorias',
      visible: esMiembroSAE,
      containerClassName: 'bg-secondary-container text-on-secondary-container',
    },
  ].filter((tile) => tile.visible)

  return (
    <main className="min-h-svh px-4 pb-8">
      <header className="flex items-center gap-2 py-4">
        <Logo className="h-7 w-7 text-primary" />
        <span className="text-base font-semibold">Atenea</span>
        <span className="flex-1" />
        <MenuUsuario />
      </header>

      <p className="pb-4 text-sm text-on-surface-variant">Hola</p>

      {tiles.length === 0 ? (
        <p className="text-sm text-on-surface-variant">Aún no contamos con servicios para ti.</p>
      ) : (
        <div className="grid grid-cols-3 gap-3">
          {tiles.map((tile, indice) => (
            <button
              key={tile.id}
              type="button"
              onClick={() => navigate(tile.ruta)}
              style={{ animationDelay: `${indice * 30}ms` }}
              className={`entrada-lista presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl p-3 text-center ${tile.containerClassName}`}
            >
              <IconTutorias className="h-6 w-6" />
              <span className="text-xs font-semibold leading-tight">{tile.etiqueta}</span>
            </button>
          ))}
        </div>
      )}
    </main>
  )
}
```

- [x] **Step 4: Borrar el mock y los íconos huérfanos**

Run: `cd frontend && rm src/data/services.ts && rmdir src/data 2>/dev/null; grep -rn "IconOrientacionVocacional\|IconBecas\|IconIdiomas\|IconServicioSocial\|IconBolsaDeTrabajo\|IconMovilidad\|IconVoluntariado\|IconPracticasProfesionales" src/`
Expected: sin resultados (nadie los usa ya).

En `frontend/src/components/icons/ServiceIcons.tsx`, borrar los ocho componentes listados arriba y dejar únicamente `IconTutorias` y el `type IconProps`. Agregar arriba del archivo:

```tsx
/**
 * Íconos de servicios de la SAE. Hoy solo sobrevive el de Asesorías: los ocho
 * de los servicios mock se borraron junto con `data/services.ts` al retirarlos
 * de Home (ADR 0027 decisión 9). Vuelven cuando exista el servicio de verdad.
 */
```

- [x] **Step 5: Verificar verde**

Run: `cd frontend && npx vitest run && npx tsc -b && npm run lint`
Expected: PASS, sin errores.

- [x] **Step 6: Commit**

```bash
git add -A frontend/src
git commit -s -m "$(cat <<'EOF'
[feat][frontend] retirar los servicios mock de Home y gatear los tiles por rol

- borrar data/services.ts y los ocho íconos sin consumidor
- mostrar Asesorías a alumno y académico, y el panel SAE al miembro de la SAE
- mostrar una leyenda cuando ningún servicio aplica al usuario

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

# Fase 7 — Cierre documental

## Task 20: Deuda técnica y documentación de API

**Files:**
- Modify: `docs/technical-debt/0001-sin-modelo-calendario-academico.md`, `0002-alta-perfil-asesor-solo-admin.md`, `0008-perfil-alumno-una-sola-carrera.md`, `0012-oferta-asesorias-sin-scope-de-semestre.md`, `README.md`
- Create: `docs/technical-debt/0018-validacion-academico-activo-con-stub.md`, `docs/technical-debt/0019-home-sin-catalogo-de-servicios.md`
- Modify: `docs/development/api-frontend.md`

- [ ] **Step 1: Marcar 0002, 0008 y 0012 como Resueltas**

En cada uno de los tres archivos, reemplazar la línea `**Estado:** Activa` por:

- `0002`: `**Estado:** Resuelta — 2026-08-15 ([ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md))`
- `0008`: `**Estado:** Resuelta — 2026-08-15 ([ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md))`
- `0012`: `**Estado:** Resuelta — 2026-08-15 ([ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md))`

y agregar al final de cada uno una sección:

```markdown
## Cómo se resolvió
```

seguida de una línea:
- `0002`: ``POST /api/asesorias/asesores/solicitud/` deja que un `PerfilAcademico` cree su propio `PerfilAsesorAcademico`. La SAE ya no lo crea: solo lo activa tras la validación de vigencia (ver [deuda 0018](0018-validacion-academico-activo-con-stub.md)).`
- `0008`: `` `HistoriaAcademica(perfil_alumno, carrera, generacion)` reemplazó `PerfilAlumno.carrera`/`generacion`. Un alumno puede tener varias filas bajo el mismo número de cuenta, y `AgendarAsesoria` pregunta con cuál agenda cuando hay más de una.``
- `0012`: `` `OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` filtran por `registro__semestre == semestre_vigente()` y `registro__asesor__activo=True`, además de `Disponibilidad.activa`. La fuente del semestre vigente es `academico.servicios.semestre_vigente`.``

- [ ] **Step 2: Actualizar 0001 (parcialmente resuelta, sigue Activa)**

En `docs/technical-debt/0001-sin-modelo-calendario-academico.md`, agregar al final:

```markdown
## Estado tras el ADR 0027

Parcialmente resuelta, sigue **Activa**. Ya existe `academico.PeriodoAcademico` con fechas reales de inicio/fin de semestre y con la ventana de registro de asesores, y `OfertaMateria`/`RegistroAsesor` se acotan al semestre vigente derivado de ahí. Lo que **no** existe todavía: subdivisiones internas del calendario (periodo de exámenes, vacaciones, días inhábiles), y la ventana agendable de Asesorías sigue siendo la regla fija en código (semana en curso + siguiente), no derivada de `PeriodoAcademico`.
```

- [ ] **Step 3: Crear la deuda 0018**

Crear `docs/technical-debt/0018-validacion-academico-activo-con-stub.md`:

```markdown
# 0018 — La vigencia del académico no se valida: `validar_academico_activo` es un stub

**Estado:** Activa
**Origen:** [ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md)

## Qué se simplificó

`asesorias/validacion_externa.py::validar_academico_activo(numero_trabajador)` devuelve siempre `False`. El servicio externo que responde si un número de trabajador corresponde a un académico vigente existe, pero su contrato (endpoint, autenticación, forma de la respuesta) no está definido todavía. En consecuencia, todo `PerfilAsesorAcademico` creado por autoservicio nace con `activo=False` y necesita que la SAE lo active a mano desde el admin de Django.

## Por qué era razonable

El autoservicio ya elimina la mitad del trabajo manual (la SAE deja de crear el perfil y de capturar el área; solo revisa y activa), y el stub es la variante segura: con `True` un académico sin nombramiento vigente podría publicar disponibilidad y recibir alumnos sin que nadie lo revisara. Aislar la pregunta en una sola función deja la integración real como un cambio de una función, no del flujo.

## Señal de revisión

En cuanto se defina el contrato del servicio externo. El cambio es reescribir el cuerpo de `validar_academico_activo` (y agregar sus variables de entorno); ni la vista ni el modelo deberían tener que tocarse. Revisar también qué hacer ante caída del servicio: hoy no hay decisión tomada.
```

- [ ] **Step 4: Crear la deuda 0019**

Crear `docs/technical-debt/0019-home-sin-catalogo-de-servicios.md`:

```markdown
# 0019 — Home arma sus tiles en el cliente, sin catálogo de servicios en el backend

**Estado:** Activa
**Origen:** [ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md)

## Qué se simplificó

`Home.tsx` declara sus tiles como un arreglo literal en el propio componente y los filtra con los hooks de rol (`useEsAlumno`, `useEsAcademico`, `useEsMiembroSAE`). No hay endpoint que diga "estos son los servicios que este usuario puede usar": agregar un servicio nuevo de la SAE implica editar y desplegar el frontend.

## Por qué era razonable

Hay exactamente dos tiles y un solo servicio integrado (Asesorías). Un endpoint de catálogo con su modelo, su admin y su gating por rol sería más código que los dos tiles que sirve, y su forma correcta depende de cómo se vean los siguientes servicios — que todavía no existen. Los nueve servicios que había aquí antes eran mocks sin backend: retirarlos, no reemplazarlos, es lo que evita seguir prometiendo lo que no existe.

## Señal de revisión

Cuando se integre el segundo servicio real de la SAE, o cuando aparezca un servicio cuya visibilidad no se derive de un rol (por carrera, por generación, por convocatoria abierta). Ahí conviene el endpoint de catálogo que anticipaba el comentario original de `data/services.ts`.
```

- [ ] **Step 5: Actualizar el índice**

En `docs/technical-debt/README.md`:
- quitar de **Activa** las entradas de `0002`, `0008` y `0012`;
- agregar a **Activa**:
```markdown
- [0018 — La vigencia del académico no se valida: `validar_academico_activo` es un stub](0018-validacion-academico-activo-con-stub.md)
- [0019 — Home arma sus tiles en el cliente, sin catálogo de servicios en el backend](0019-home-sin-catalogo-de-servicios.md)
```
- agregar a **Resuelta**:
```markdown
- [0002 — Alta de `PerfilAsesorAcademico` solo por admin](0002-alta-perfil-asesor-solo-admin.md) — resuelta 2026-08-15
- [0008 — `PerfilAlumno` solo registra una carrera vigente](0008-perfil-alumno-una-sola-carrera.md) — resuelta 2026-08-15
- [0012 — Oferta/asesores/búsqueda no acotan por semestre vigente](0012-oferta-asesorias-sin-scope-de-semestre.md) — resuelta 2026-08-15
```

- [ ] **Step 6: Actualizar la guía de API para frontend**

En `docs/development/api-frontend.md`:
- en la sección de `accounts`, actualizar el ejemplo de `GET /api/auth/user/` para que `perfil_alumno` traiga `historial` en vez de `carrera`/`carrera_nombre`/`generacion`;
- agregar una sección nueva antes de `## carreras`:

```markdown
## `academico`

| Ruta | Método | Permiso | Qué devuelve |
|---|---|---|---|
| `/api/academico/periodo-vigente/` | GET | sesión | Detalle del `PeriodoAcademico` del semestre vigente |

```json
{ "semestre": "20271", "fecha_inicio": "2026-08-10", "fecha_fin": "2026-12-04",
  "registro_asesores_inicio": "2026-07-01", "registro_asesores_fin": "2026-08-31",
  "registro_asesores_abierto": true }
```

**404 es una respuesta esperada**: significa que la SAE todavía no dio de alta el periodo de ese semestre, no que la petición esté mal. El frontend calcula la clave del semestre por su cuenta (`semestreActual` en `logica.ts`) y usa este endpoint solo para fechas y ventanas.
```

- en la sección de `asesorias`, agregar a la tabla de rutas del asesor:

```markdown
| `/api/asesorias/asesores/solicitud/` | POST | `PerfilAcademico` | `{ "area": <id> }` → crea el `PerfilAsesorAcademico` del usuario. `409` si ya lo tiene. El perfil puede nacer `activo: false` (validación externa pendiente). |
```

- y una nota debajo de `POST /api/asesorias/registros/`:

```markdown
Solo acepta el semestre vigente y solo dentro de `registro_asesores_inicio..registro_asesores_fin` del `PeriodoAcademico` de ese semestre; fuera de ahí devuelve `400`. Consultar `/api/academico/periodo-vigente/` antes de ofrecer el alta.
```

- en el listado de oferta/búsqueda, agregar: `Las tres rutas se acotan al semestre vigente y a asesores con `activo=true`.`

- [ ] **Step 7: Verificar que el repo entero sigue verde**

Run: `cd backend && uv run manage.py test -v 1 && uv run manage.py makemigrations --check --dry-run`
Expected: PASS y `No changes detected`.

Run: `cd frontend && npx vitest run && npx tsc -b && npm run lint`
Expected: PASS, sin errores.

- [ ] **Step 8: Commit**

```bash
git add docs
git commit -s -m "$(cat <<'EOF'
[docs] cerrar las deudas 0002, 0008 y 0012 y registrar la deuda nueva

- marcar como resueltas la carrera única del alumno, el alta manual de asesor y el scope de semestre
- anotar la resolución parcial de la deuda 0001 con PeriodoAcademico
- agregar las deudas 0018 (stub de validación externa) y 0019 (Home sin catálogo de servicios)
- documentar /api/academico/periodo-vigente/ y el autoservicio de asesor en la guía de API

Signed-off-by: Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>
EOF
)"
```

---

## Notas de ejecución

- **Orden.** Las fases 1→2→3 son secuenciales (la 2 toca el `PerfilAlumno` que la 1 deja limpio; la 3 corrige la heurística de la que dependen la 4 y la 5). La fase 6 (Home) solo depende de que exista `useEsAcademico` (Task 16). Las tasks 13 y 17 son STOPs: si Héctor no está disponible, **detener el plan ahí**, no improvisar.
- **Migraciones.** El plan produce cinco: `accounts.0005/0006/0007/0008`, `academico.0001`, `asesorias.0006`. `uv run manage.py makemigrations --check --dry-run` debe decir `No changes detected` al terminar cada fase.
- **Regresión de fixtures.** Varios tests preexistentes fijan `semestre="20271"` a mano. A partir de la Task 11 eso deja de coincidir con el semestre vigente en cuanto la fecha real avance; el plan indica sustituirlos por `semestre_vigente()` conforme se toquen. Si un test falla con "lista vacía" tras la Task 11, esa es casi siempre la causa.
