# Addendum MVP — Asesorías SAE: filtro de asesor por búsqueda y detalle read-only

> **For agentic workers:** este archivo es un ADDENDUM del plan
> [`2026-08-09-asesorias-sae-admin-frontend-plan.md`](2026-08-09-asesorias-sae-admin-frontend-plan.md).
> Se ejecuta con las mismas sub-skills (`superpowers:subagent-driven-development` o
> `superpowers:executing-plans`). Los pasos usan checkbox (`- [ ]`).
> **Todo bloque de código es VERBATIM: transcribir tal cual, sin improvisar.**

**Goal:** tres cambios de alcance MVP sobre la vista SAE de Asesorías, ya aprobados por el usuario:

1. El filtro de **asesor** pasa de `<select>` a **búsqueda** (por nombre *o* número de trabajador), espejo exacto del filtro de alumno. Requiere extender el backend **sin crear vistas nuevas**.
2. Las **notas salen de la tarjeta**: la tarjeta admin ya no las muestra y se vuelve **clicable**, navegando a un detalle read-only `/sae/asesorias/:id` donde sí se ven.
3. El backend va en **un solo commit aparte** (sólo toca `backend/asesorias/`; no se mezcla con commits de `frontend/`).

---

## Relación con el plan base

Tasks 1–5 del plan base ya están commiteadas. Este addendum **revisa** tres puntos de ese plan:

| Punto del plan base | Estado | Motivo |
|---|---|---|
| **Task 5** — `TarjetaAsesoria` en modo admin ("ambos nombres + `notas`, **no interactiva**") | **Superseded parcialmente por Task C.** El modo admin ya NO renderiza `notas` y SÍ es interactivo (navega a `/sae/asesorias/:id`). Se conservan: `destacar`, `tabIndex=-1` en la variante no interactiva, `InsigniaEstado`, la secundaria con ambos nombres. | El usuario pidió sacar las notas de la lista y darles una vista propia. El comentario "en modo admin no hay ruta de detalle en esta fase (spec §Out of scope)" queda obsoleto: esa ruta se crea en la Task E. |
| **Task 6** — `FiltroAsesor` como `<select>` (plan base líneas 1219–1237) | **Superseded por Task D.** La Task D redacta `AdminAsesorias.tsx` **completa** (reusa tabs, `Historial`, `ListaDeSemestre`, `ListaAdmin` del plan base sin cambios) con `FiltroAsesor` de búsqueda. Al ejecutar la Task 6 se usa el código de la Task D, no el de las líneas 1150–1393 del plan base. | El directorio de asesores crece; un `<select>` no escala y no permite buscar por número de trabajador. |
| **Task 12** — rutas `/sae/*` en `App.tsx` | **Ampliada por la Task E (Step 5).** Se agrega una sexta ruta `/sae/asesorias/:id` → `AdminDetalleAsesoria`, bajo `RutaDeSAE`. | La ruta de detalle no existía en el plan base. |
| **Task 3** — tipos y hooks admin | **Ampliada por la Task B.** `AsesorDirectorio` gana `numero_trabajador`; se crea `AsesorBusqueda` y el hook `useBuscarAsesores`. | Espejo de `AlumnoBusqueda` / `useBuscarAlumnos`. |

> **⚑ Nota obligatoria para las Tasks 10 y 11 del plan base:** desde la Task B, `AsesorDirectorio` tiene un campo **requerido** nuevo, `numero_trabajador: string`. **Las fixtures de `AsesorDirectorio` de `AdminAsesores.test.tsx` (Task 10) y `AdminAsesorDetalle.test.tsx` (Task 11) deben incluirlo** o no compilarán (`npm run build` falla en `tsc`). Valor sugerido: `numero_trabajador: '30001'`. Las fixtures de este addendum ya están al día: la Task D usa `AsesorBusqueda`, que lo trae por definición, y no queda ningún literal `AsesorDirectorio` en los tests aquí redactados.

**Decisión de documentación:** esto es una **extensión menor sobre [ADR 0023](../../decisions/0023-asesorias-sae-admin-api.md)** (área SAE de asesorías, API admin) y [ADR 0024](../../decisions/0024-asesorias-sae-admin-frontend.md) (frontend). **No se abre un ADR nuevo**: no cambia ninguna decisión estructural — se añade un parámetro `?buscar=` a un endpoint admin existente y una pantalla de detalle que consume datos ya expuestos. **No se crea deuda técnica nueva**; la falta de paginación sigue cubierta por [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).

---

## Orden de ejecución y dependencias

```
Task A (BACKEND, commit único)   ──▶  Task B (types + hook)  ──▶  Task D (pantalla + filtro)
                                                              ──▶  Task E (detalle SAE)
Task C (tarjeta)  ─────────────────────────────────────────────▶  Task D, Task E
```

1. **Task A** — backend. Va primero y **sola en su commit** (sólo archivos de `backend/asesorias/`).
2. **Task B** — `types.ts` + `api.ts`. Depende de A (consume el contrato nuevo).
3. **Task C** — `TarjetaAsesoria`. Independiente de A/B; puede correr en paralelo con B.
4. **Task D** — `AdminAsesorias` (ejecuta/reemplaza la Task 6 del plan base). Depende de B y C.
5. **Task E** — `AdminDetalleAsesoria` + nota para Task 12. Depende de C (es el destino de la navegación) y de los tipos de la Task 3.

**Gate de mockup:** la Task D hereda el gate de la Task 6 del plan base (mockup + aprobación antes de escribir código). La Task E es pantalla nueva → **también lleva gate**. Las Tasks A, B y C no llevan gate (backend / tipos / componente existente).

## Global Constraints (heredadas del plan base — recordatorio)

- **Frontend, siempre desde `frontend/`:** test puntual `npx vitest run <ruta>`; suite `npm test`; build `npm run build`; lint `npm run lint`.
- **Backend, siempre desde `backend/`:** `uv run python manage.py test <ruta.de.puntos> -v 2` (runner de Django; **no hay pytest** en este repo — verificado: `backend/pyproject.toml` no declara pytest y los planes previos usan `uv run manage.py test`).
- `@testing-library/user-event` **NO** está instalado: tests con `fireEvent`.
- Sin dependencias nuevas. TanStack Query con `apiGet` de `src/api/client.ts` y **query keys planas**.
- Imports **relativos** en los componentes (jsdom), nunca el alias `@/`.
- A11y: `min-h-11` en todo lo interactivo, `.foco-visible`, `truncate`+`title` en nombres de materia.
- **Sólo lectura:** ninguna pantalla `/sae/*` monta mutaciones.
- Commits: `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>`.

---

## Task A: `?buscar=` y `numero_trabajador` en `AdminAsesoresView` (BACKEND, commit único)

**Files:**
- Modify: `backend/asesorias/views.py` (clase `AdminAsesoresView`, líneas 379–406)
- Modify: `backend/asesorias/tests/test_api_admin.py` (clase `AdminAsesoresApiTests`, línea 248)

**Interfaces:**
- Consumes: `PerfilAsesorAcademico` (`asesorias.models`), `PerfilAcademico` (`accounts.models`, OneToOne con `User`, `related_name="perfil_academico"`, campo `numero_trabajador`), `semestre_vigente` (`asesorias.servicios`), `EsMiembroSAE`.
- Produces: `GET /api/asesorias/admin/asesores/` sigue devolviendo el directorio completo ordenado por nombre, ahora con la clave extra `numero_trabajador`; con `?buscar=` filtra por nombre (first_name / apellido1 / apellido2) **o** número de trabajador.

**Decisiones de diseño de esta task (registrar en el commit, no re-litigar):**

1. **Un solo endpoint, no dos.** `GET /admin/asesores/` sirve al directorio (Task 10) y al autocompletar del filtro (Task D). `?buscar=` es opcional; sin él, el comportamiento actual no cambia (mismo contrato + una clave nueva).
2. **Corte sólo cuando hay `?buscar=`.** Espejo de `AdminAlumnosView`: `LIMITE_AUTOCOMPLETAR_ASESORES = 20` se aplica **únicamente** en modo autocompletar. Sin `buscar`, el endpoint devuelve el directorio completo sin corte, porque el mismo endpoint alimenta el directorio de la Task 10, que debe listarlos todos. Paginación del directorio → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).
   Para que el corte sea determinista se ordena en SQL (`order_by` sobre las columnas del nombre) **antes** de rebanar; el `data.sort` final sigue existiendo porque `nombre_completo` es una propiedad de Python y el orden por columnas no es idéntico.
3. **`numero_trabajador` puede no existir.** Un `PerfilAsesorAcademico` no garantiza un `PerfilAcademico`. El acceso inverso a un OneToOne inexistente lanza `RelatedObjectDoesNotExist`, que hereda de `AttributeError` → `getattr(user, "perfil_academico", None)` devuelve `None` sin excepción. En ese caso el payload lleva `""` (nunca `null`), para que el tipo del frontend sea `string` y no `string | null`.
4. **El filtro por nombre se hace sobre columnas**, no sobre `nombre_completo` (propiedad de Python), igual que en `AdminAlumnosView`.

- [ ] **Step 1: Escribir los tests que fallan**

En `backend/asesorias/tests/test_api_admin.py`, dentro de la clase `AdminAsesoresApiTests`, insertar los siguientes tests **justo antes** de `def test_no_sae_recibe_403(self):` (línea 320). **No se modifica el `setUp` existente** — el asesor sin `PerfilAcademico` se crea dentro de su propio test para no romper `test_lista_todos_los_asesores_ordenados_por_nombre`, que asegura `ids == {activo, inactivo}`.

```python
    def test_incluye_numero_trabajador(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        fila = next(a for a in response.data if a["perfil_id"] == self.asesor_activo.id)
        self.assertEqual(fila["numero_trabajador"], "30001")

    def test_asesor_sin_perfil_academico_reporta_numero_trabajador_vacio(self):
        sin_perfil_user = User.objects.create_user(
            email="sin-perfil@ciencias.unam.mx", password="x", first_name="Nadia",
        )
        sin_perfil = PerfilAsesorAcademico.objects.create(
            user=sin_perfil_user, area=self.area, activo=True,
        )
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        self.assertEqual(response.status_code, 200)
        fila = next(a for a in response.data if a["perfil_id"] == sin_perfil.id)
        self.assertEqual(fila["numero_trabajador"], "")

    def test_sin_buscar_devuelve_todos(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_activo.id, self.asesor_inactivo.id})

    def test_busca_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=zo")
        self.assertEqual(response.status_code, 200)
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_activo.id})

    def test_busca_por_numero_de_trabajador(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=30002")
        ids = {a["perfil_id"] for a in response.data}
        self.assertEqual(ids, {self.asesor_inactivo.id})

    def test_busqueda_sin_coincidencias_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=zzzzz")
        self.assertEqual(response.data, [])

    def test_la_busqueda_conserva_el_orden_por_nombre(self):
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=3000")
        nombres = [a["nombre"] for a in response.data]
        self.assertEqual(nombres, sorted(nombres))

    def test_la_busqueda_respeta_el_limite_de_resultados(self):
        from asesorias.views import LIMITE_AUTOCOMPLETAR_ASESORES

        for indice in range(LIMITE_AUTOCOMPLETAR_ASESORES + 5):
            user = User.objects.create_user(
                email=f"masivo{indice}@ciencias.unam.mx", password="x", first_name="Masivo",
            )
            PerfilAcademico.objects.create(user=user, numero_trabajador=f"9000{indice:02d}")
            PerfilAsesorAcademico.objects.create(user=user, area=self.area, activo=True)
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/?buscar=masivo")
        self.assertEqual(len(response.data), LIMITE_AUTOCOMPLETAR_ASESORES)

    def test_el_directorio_sin_buscar_no_lleva_corte(self):
        for indice in range(LIMITE_AUTOCOMPLETAR_ASESORES_ESPERADO + 5):
            user = User.objects.create_user(
                email=f"pleno{indice}@ciencias.unam.mx", password="x", first_name="Pleno",
            )
            PerfilAcademico.objects.create(user=user, numero_trabajador=f"8000{indice:02d}")
            PerfilAsesorAcademico.objects.create(user=user, area=self.area, activo=True)
        self.client.force_authenticate(user=self.sae_user)
        response = self.client.get("/api/asesorias/admin/asesores/")
        # Los 2 del setUp + los 25 recién creados: el directorio va completo.
        self.assertEqual(len(response.data), 27)
```

Y añadir, **al final del bloque de imports** de `backend/asesorias/tests/test_api_admin.py` (después de la línea 8, `from rest_framework.test import APITestCase`):

```python

# El directorio no lleva corte; la constante sólo se usa para dimensionar el
# fixture del test que lo comprueba.
LIMITE_AUTOCOMPLETAR_ASESORES_ESPERADO = 20
```

> Nota de fixtures (verificada en el `setUp` de `AdminAsesoresApiTests`, líneas 249–289): `self.asesor_activo` = usuario `Zoe` (`first_name="Zoe"`, sin apellidos), `numero_trabajador="30001"`; `self.asesor_inactivo` = usuario `Aldo`, `numero_trabajador="30002"`. Por eso `?buscar=zo` matchea sólo a Zoe y `?buscar=3000` matchea a los dos.

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `cd backend && uv run python manage.py test asesorias.tests.test_api_admin.AdminAsesoresApiTests -v 2`
Expected: FAIL — `KeyError: 'numero_trabajador'` en los tests de payload y los tests de `?buscar=` devuelven los 2 asesores en vez de filtrar.

- [ ] **Step 3: Implementar la vista**

En `backend/asesorias/views.py`, reemplazar **íntegramente** la clase `AdminAsesoresView` (líneas 379–406) por:

```python
# Autocompletar, no listado: el filtro de asesor de `AdminAsesorias` usa el
# mismo endpoint que el directorio, con `?buscar=`. El corte aplica sólo en ese
# modo — sin `buscar`, el directorio va completo (deuda 0006).
LIMITE_AUTOCOMPLETAR_ASESORES = 20


class AdminAsesoresView(APIView):
    """Directorio de asesores para el área SAE.

    `?buscar=` (opcional) filtra por nombre o número de trabajador y corta a
    `LIMITE_AUTOCOMPLETAR_ASESORES`; sin él devuelve el directorio completo,
    que es lo que consume la pantalla de directorio.
    """

    permission_classes = [EsMiembroSAE]

    def get(self, request):
        semestre = semestre_vigente()
        asesores = PerfilAsesorAcademico.objects.select_related(
            "user", "area", "user__perfil_academico"
        ).annotate(
            num_materias_semestre_vigente=Count(
                "registros__materias",
                filter=Q(registros__semestre=semestre),
                distinct=True,
            )
        )
        buscar = request.query_params.get("buscar")
        if buscar:
            # `nombre_completo` es una propiedad de Python: se busca sobre las
            # columnas que la componen, más el número de trabajador, que vive
            # en `accounts.PerfilAcademico` y no en el perfil de asesor.
            asesores = asesores.filter(
                Q(user__first_name__icontains=buscar)
                | Q(user__apellido1__icontains=buscar)
                | Q(user__apellido2__icontains=buscar)
                | Q(user__perfil_academico__numero_trabajador__icontains=buscar)
            )
            # El corte necesita un orden estable en SQL; el `data.sort` de
            # abajo reordena la página ya recortada por `nombre_completo`.
            asesores = asesores.order_by(
                "user__first_name", "user__apellido1", "user__apellido2"
            )[:LIMITE_AUTOCOMPLETAR_ASESORES]
        data = [
            {
                "perfil_id": asesor.id,
                "nombre": asesor.user.nombre_completo,
                # Un asesor puede no tener PerfilAcademico: el acceso inverso a
                # un OneToOne inexistente lanza RelatedObjectDoesNotExist, que
                # hereda de AttributeError, así que `getattr` con default basta.
                "numero_trabajador": getattr(
                    getattr(asesor.user, "perfil_academico", None), "numero_trabajador", ""
                ),
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

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `cd backend && uv run python manage.py test asesorias.tests.test_api_admin.AdminAsesoresApiTests -v 2`
Expected: PASS (14 casos: los 5 previos + los 9 nuevos).

- [ ] **Step 5: Suite de `asesorias` completa (sin regresiones)**

Run: `cd backend && uv run python manage.py test asesorias -v 2`
Expected: PASS.

- [ ] **Step 6: Check de Django**

Run: `cd backend && uv run python manage.py check`
Expected: `System check identified no issues`. **No hay migración**: no se tocó ningún modelo.

- [ ] **Step 7: Commit (SÓLO backend)**

```bash
git add backend/asesorias/views.py backend/asesorias/tests/test_api_admin.py
git commit -m "[feat][asesorias] busqueda de asesores por nombre o numero de trabajador

- ?buscar= en GET /admin/asesores/ sobre first_name/apellido1/apellido2 y numero_trabajador
- numero_trabajador en el payload del directorio, \"\" si el asesor no tiene PerfilAcademico
- corte de 20 solo en modo autocompletar: sin buscar el directorio va completo (deuda 0006)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

> **Verificar antes de commitear:** `git status --short` no debe listar ningún archivo bajo `frontend/`.

---

## Task B: `numero_trabajador`, `AsesorBusqueda` y `useBuscarAsesores` (amplía Task 3)

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/features/asesorias/api.ts`
- Test: `frontend/src/features/asesorias/api.test.ts` (ya existe)

**Interfaces:**
- Consumes: contrato de la Task A; `apiGet` de `src/api/client.ts`.
- Produces: `AsesorDirectorio.numero_trabajador`, interfaz `AsesorBusqueda`, helper `rutaBuscarAsesores`, hook `useBuscarAsesores`.

> **Nota de contrato para las Tasks 10 y 11 del plan base:** `AsesorDirectorio` gana un campo **requerido**. Las fixtures de `AdminAsesores.test.tsx` (Task 10) y cualquier literal `AsesorDirectorio` en tests deben incluir `numero_trabajador`. La fixture `ASESORES` de la Task 6 ya viene corregida en la Task D de este addendum.

- [ ] **Step 1: Escribir el test que falla**

`useBuscarAlumnos` no tiene test propio: `api.test.ts` sólo prueba el helper puro `rutaAdminAsesorias` (verificado). Para poder testear la URL del autocompletar de asesores **sin** montar TanStack Query, se extrae un helper puro y se prueba ése — mismo patrón que `rutaAdminAsesorias`.

En `frontend/src/features/asesorias/api.test.ts`, reemplazar la línea 2 por:

```ts
import { rutaAdminAsesorias, rutaBuscarAsesores } from './api'
```

Y añadir, **después** del `describe('rutaAdminAsesorias', ...)` que cierra el archivo:

```ts
describe('rutaBuscarAsesores', () => {
  it('manda el término en ?buscar=', () => {
    expect(rutaBuscarAsesores('ana')).toBe('/api/asesorias/admin/asesores/?buscar=ana')
  })

  it('escapa los caracteres del término', () => {
    expect(rutaBuscarAsesores('ana lópez')).toBe(
      '/api/asesorias/admin/asesores/?buscar=ana%20l%C3%B3pez',
    )
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run (desde `frontend/`): `npx vitest run src/features/asesorias/api.test.ts`
Expected: FAIL — `rutaBuscarAsesores` no está exportado.

- [ ] **Step 3: Añadir los tipos**

En `frontend/src/api/types.ts`, reemplazar el bloque `AsesorDirectorio` (líneas 182–189) por:

```ts
/** GET /api/asesorias/admin/asesores/ */
export interface AsesorDirectorio {
  perfil_id: number
  nombre: string
  // Vive en `accounts.PerfilAcademico`, no en el perfil de asesor: el backend
  // lo resuelve y manda "" cuando el asesor no tiene PerfilAcademico.
  numero_trabajador: string
  area_nombre: string
  activo: boolean
  num_materias_semestre_vigente: number
}

/** Subconjunto de `AsesorDirectorio` que consume el autocompletar del filtro
 *  de asesor. Espejo de `AlumnoBusqueda`: el endpoint es el mismo directorio
 *  con `?buscar=`, la pantalla sólo lee estos tres campos. */
export interface AsesorBusqueda {
  perfil_id: number
  nombre: string
  numero_trabajador: string
}
```

- [ ] **Step 4: Añadir el helper y el hook**

En `frontend/src/features/asesorias/api.ts`:

**(a)** reemplazar el bloque de import de tipos (líneas 3–7) por:

```ts
import type {
  RegistroAsesor, Disponibilidad, Asesoria, SesionesFuturas,
  MateriaOferta, AsesorDisponible, SlotDisponibilidad, EstadoAsesoria,
  AsesoriaAdmin, AsesorDirectorio, AsesorDetalle, AlumnoBusqueda, AsesorBusqueda,
} from '../../api/types'
```

**(b)** añadir al **final del archivo**, después de `useBuscarAlumnos`:

```ts
/** URL del autocompletar de asesores. Es el mismo endpoint del directorio
 *  (`useAdminAsesores`) con `?buscar=`; se extrae para poder testear la
 *  construcción de la query sin montar TanStack Query. */
export function rutaBuscarAsesores(buscar: string): string {
  return `/api/asesorias/admin/asesores/?buscar=${encodeURIComponent(buscar)}`
}

/** Autocompletar de asesor para el filtro de `AdminAsesorias`. Espejo de
 *  `useBuscarAlumnos`: busca por nombre o número de trabajador y sólo pega al
 *  servidor a partir de 2 caracteres. */
export function useBuscarAsesores(buscar: string) {
  return useQuery({
    queryKey: ['admin', 'asesores', 'buscar', buscar],
    queryFn: () => apiGet<AsesorBusqueda[]>(rutaBuscarAsesores(buscar)),
    enabled: buscar.length >= 2,
  })
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/api.test.ts`
Expected: PASS (8 casos: 6 previos + 2 nuevos).

- [ ] **Step 6: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/features/asesorias/api.ts frontend/src/features/asesorias/api.test.ts
git commit -m "[feat][frontend] autocompletar de asesores para el filtro SAE

- numero_trabajador en AsesorDirectorio y tipo AsesorBusqueda nuevo
- rutaBuscarAsesores + useBuscarAsesores sobre /admin/asesores/?buscar=
- espejo exacto de useBuscarAlumnos: minimo 2 caracteres antes de consultar

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task C: `TarjetaAsesoria` admin sin notas y con navegación a detalle (revisa Task 5)

**Files:**
- Modify: `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`
- Modify: `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx`

**Interfaces:**
- Consumes: `useEsAsesor`, `InsigniaEstado`, `useNavigate`.
- Produces: en modo `admin` la tarjeta muestra materia + `fecha · hora · alumno · asesor` + `InsigniaEstado`, **sin notas**, y es un `<button>` que navega a `/sae/asesorias/:id` **llevando la sesión en el router state**. Fuera de `admin`, el comportamiento no cambia (asesor → botón a `/asesorias/:id`, sin state; alumno → `<div>` no interactivo).

**Decisiones:**
1. `AsesoriaEnTarjeta` **conserva** `'notas'` en el `Pick`. La tarjeta ya no lo renderiza, pero ahora **sí lo transporta**: la sesión completa viaja en el router state hacia el detalle, que es quien muestra las notas.
2. El destino depende del modo (`admin` → `/sae/asesorias/:id`), no del rol: un miembro SAE que además sea asesor no debe caer en el detalle del asesor (que monta mutaciones).
3. **La sesión viaja por `navigate(..., { state })`, no por caché ni por endpoint.** El listado admin está cacheado **por combinación de filtros**, así que una sesión del historial (`{semestre}`) no aparece en la query por defecto (próximas agendadas) y el detalle no podría resolverla. Pasar `{ asesoria, nombreMateria }` en el state elimina el problema de raíz: sin `?semestre=`, sin segunda petición y sin endpoint nuevo. El costo es que un deep-link o un refresh pierden el state → el detalle muestra "Asesoría no encontrada" (Task E).

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar **íntegramente** `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx` por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { TarjetaAsesoria } from './TarjetaAsesoria'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

/** Ruta de destino de mentira: verifica a la vez que la navegación ocurrió y
 *  qué llegó en el router state. */
function EspiaDeEstado() {
  const { state } = useLocation() as { state: { asesoria?: Asesoria; nombreMateria?: string } | null }
  return (
    <div>
      <p>detalle SAE</p>
      <p data-testid="materia-en-estado">{state?.nombreMateria ?? ''}</p>
      <p data-testid="notas-en-estado">{state?.asesoria?.notas ?? ''}</p>
    </div>
  )
}

function crearAsesoria(overrides: Partial<Asesoria> = {}): Asesoria {
  return {
    id: 1, alumno: 10, alumno_nombre: 'Beto Alumno', asesor_nombre: 'Ana Asesora',
    disponibilidad: 1, materia: 1, carrera: 1, fecha: '2026-08-03', hora_inicio: '10:00:00',
    formato: 'virtual', ubicacion: '', liga_virtual: '', estado: 'agendada', asistio: null,
    notas: '', creado_en: '2026-08-01T10:00:00Z', ...overrides,
  }
}

describe('TarjetaAsesoria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('para el alumno muestra el nombre del asesor y no navega', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.getByText(/Ana Asesora/)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('para el asesor muestra el nombre del alumno en un botón', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(true)
    render(<TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.getByText(/Beto Alumno/)).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('nunca renderiza las notas', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(<TarjetaAsesoria asesoria={crearAsesoria({ notas: 'texto privado' })} nombreMateria="Cálculo I" indice={0} />, { wrapper: MemoryRouter })
    expect(screen.queryByText(/texto privado/)).not.toBeInTheDocument()
  })

  it('en modo admin muestra ambos nombres y tampoco las notas', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <TarjetaAsesoria
        asesoria={crearAsesoria({ notas: 'el alumno llegó tarde' })}
        nombreMateria="Cálculo I"
        indice={0}
        admin
      />,
      { wrapper: MemoryRouter },
    )
    expect(screen.getByText(/Beto Alumno · Ana Asesora/)).toBeInTheDocument()
    expect(screen.queryByText(/el alumno llegó tarde/)).not.toBeInTheDocument()
  })

  it('en modo admin es interactiva aunque quien mire no sea asesor', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} admin />,
      { wrapper: MemoryRouter },
    )
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('en modo admin navega al detalle SAE y no al del asesor', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(true)
    render(
      <MemoryRouter initialEntries={['/sae/asesorias']}>
        <Routes>
          <Route
            path="/sae/asesorias"
            element={
              <TarjetaAsesoria
                asesoria={crearAsesoria({ notas: 'trae dudas' })}
                nombreMateria="Cálculo I"
                indice={0}
                admin
              />
            }
          />
          <Route path="/sae/asesorias/1" element={<EspiaDeEstado />} />
          <Route path="/asesorias/1" element={<p>detalle del asesor</p>} />
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText('detalle SAE')).toBeInTheDocument()
  })

  it('en modo admin lleva la sesión y la materia en el router state', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <MemoryRouter initialEntries={['/sae/asesorias']}>
        <Routes>
          <Route
            path="/sae/asesorias"
            element={
              <TarjetaAsesoria
                asesoria={crearAsesoria({ notas: 'trae dudas' })}
                nombreMateria="Cálculo I"
                indice={0}
                admin
              />
            }
          />
          <Route path="/sae/asesorias/1" element={<EspiaDeEstado />} />
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByTestId('materia-en-estado')).toHaveTextContent('Cálculo I')
    expect(screen.getByTestId('notas-en-estado')).toHaveTextContent('trae dudas')
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: FAIL — en modo admin la tarjeta sigue imprimiendo `Notas:` y sigue siendo un `<div>` (no hay `button`).

- [ ] **Step 3: Implementar**

Reemplazar **íntegramente** `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx` por:

```tsx
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { useEsAsesor } from '../../../auth/rol'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

/** Lo mínimo que la tarjeta necesita: lo cumplen `Asesoria` y `AsesoriaAdmin`.
 *  `notas` se conserva en la forma aunque la tarjeta ya no lo renderice: en
 *  modo admin la sesión completa viaja en el router state al detalle SAE, que
 *  es quien muestra las notas. */
export type AsesoriaEnTarjeta = Pick<
  Asesoria,
  'id' | 'estado' | 'fecha' | 'hora_inicio' | 'alumno_nombre' | 'asesor_nombre' | 'notas'
>

interface TarjetaAsesoriaProps {
  asesoria: AsesoriaEnTarjeta
  nombreMateria: string
  indice: number
  /** Resalta y enfoca la tarjeta recién agendada (post-agendado). */
  destacar?: boolean
  /** Modo SAE: ambos nombres, sin notas, y navega al detalle read-only. */
  admin?: boolean
}

export function TarjetaAsesoria({
  asesoria,
  nombreMateria,
  indice,
  destacar = false,
  admin = false,
}: TarjetaAsesoriaProps) {
  const navigate = useNavigate()
  const esAsesor = useEsAsesor()
  const ref = useRef<HTMLElement | null>(null)
  const fecha = FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))

  // El asesor ve al alumno; el alumno ve al asesor. El SAE ve a los dos.
  const contraparte = esAsesor ? asesoria.alumno_nombre : asesoria.asesor_nombre
  const hora = asesoria.hora_inicio.slice(0, 5)
  const secundaria = admin
    ? `${fecha} · ${hora} · ${asesoria.alumno_nombre} · ${asesoria.asesor_nombre}`
    : `${fecha} · ${hora} · ${contraparte}`

  // El destino depende del MODO, no del rol: un miembro SAE que además sea
  // asesor no debe caer en el detalle del asesor, que monta mutaciones.
  const interactiva = admin || esAsesor

  // El detalle SAE no tiene endpoint propio y el listado admin está cacheado
  // por combinación de filtros: la sesión viaja en el router state para que el
  // detalle no dependa de qué query la trajo (próximas vs. un semestre).
  const irAlDetalle = () => {
    if (admin) {
      navigate(`/sae/asesorias/${asesoria.id}`, { state: { asesoria, nombreMateria } })
    } else {
      navigate(`/asesorias/${asesoria.id}`)
    }
  }

  useEffect(() => {
    if (destacar && ref.current) {
      ref.current.scrollIntoView({ block: 'center' })
      ref.current.focus()
    }
  }, [destacar])

  const contenido = (
    <div className="flex w-full items-center justify-between gap-3">
      <div className="flex min-w-0 flex-col gap-1">
        <span className="text-sm font-medium text-on-surface">{nombreMateria}</span>
        <span className="text-xs text-on-surface-variant">{secundaria}</span>
      </div>
      <InsigniaEstado estado={asesoria.estado} />
    </div>
  )

  const clasesBase = `flex w-full rounded-lg bg-surface-container px-4 py-3 text-left${destacar ? ' pulso-exito' : ''}`

  return (
    <li className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
      {interactiva ? (
        <button
          ref={(el) => { ref.current = el }}
          type="button"
          onClick={irAlDetalle}
          className={`foco-visible ${clasesBase}`}
        >
          {contenido}
        </button>
      ) : (
        // tabIndex=-1 permite el focus programático de `destacar` sin meterla
        // en el orden de tabulación.
        <div ref={(el) => { ref.current = el }} tabIndex={-1} className={`foco-visible ${clasesBase}`}>
          {contenido}
        </div>
      )}
    </li>
  )
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: PASS (7 casos).

- [ ] **Step 5: Sin regresiones en los consumidores + build/lint**

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx && npm run build && npm run lint`
Expected: PASS. `Asesorias.tsx` no usa `admin`, así que su comportamiento es idéntico.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/components/TarjetaAsesoria.tsx frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx
git commit -m "[feat][frontend] tarjeta admin clicable y sin notas en la lista

- el modo admin deja de renderizar notas: se leen en el detalle /sae/asesorias/:id
- la tarjeta admin navega a ese detalle llevando la sesion en el router state
- el destino depende del modo y no del rol; revisa la task 5, que la definia estatica

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task D: Pantalla `AdminAsesorias` con filtro de asesor por búsqueda (ejecuta/supersede Task 6)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AdminAsesorias.tsx`
- Test: `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx`

**Interfaces:**
- Consumes: `useAdminAsesorias`, `useAdminSemestres`, `useBuscarAlumnos`, `useBuscarAsesores` (Task B); `proximas`/`historial` (Task 4); `TarjetaAsesoria` con `admin` (Task C); `useMapaMaterias`; `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent`; `Skeleton`.
- Produces: componente `AdminAsesorias`. Tabs Próximas/Historial con subtabs por semestre; **dos filtros de búsqueda simétricos** (Asesor y Alumno), cada uno input + lista de resultados + chip de selección; enlaces "Consultar oferta" y "Asesores".

**Cambio frente al plan base:** `useAdminAsesores` (directorio completo) **ya no se usa en esta pantalla** — lo reemplaza `useBuscarAsesores`. El estado del filtro pasa de `number | null` a `AsesorBusqueda | null`, y `idAsesor = asesor?.perfil_id ?? null` alimenta los filtros de la query, igual que el de alumno. `useAdminAsesores` sigue vivo para la Task 10 (directorio).

- [ ] **Step 1: GATE — mockup y aprobación del usuario**

Generar un artefacto HTML (herramienta `Artifact`) con el layout de `/sae/asesorias`: encabezado "Asesorías · SAE", botones "Consultar oferta" y "Asesores", el bloque de filtros con **los dos buscadores simétricos** (input + lista de resultados; el de asesor mostrando nombre + número de trabajador, el de alumno nombre + número de cuenta; chip ✕ cuando hay selección), los tabs Próximas/Historial, los subtabs de semestre y 3 tarjetas admin de ejemplo (**ambos nombres + insignia, sin notas**, clicables).

**DETENERSE AQUÍ.** Esperar aprobación explícita del usuario antes de escribir código. Si pide cambios, actualizar el artefacto y volver a esperar.

- [ ] **Step 2: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesorias } from './AdminAsesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import * as rol from '../../../auth/rol'
import type { AlumnoBusqueda, AsesorBusqueda, AsesoriaAdmin } from '../../../api/types'

const ASESORES: AsesorBusqueda[] = [
  { perfil_id: 7, nombre: 'Ana López', numero_trabajador: '30001' },
]

const ALUMNOS: AlumnoBusqueda[] = [
  { perfil_id: 15, nombre: 'Juan Pérez', numero_cuenta: '312345678' },
]

function asesoria(overrides: Partial<AsesoriaAdmin> = {}): AsesoriaAdmin {
  return {
    id: 1,
    estado: 'agendada',
    fecha: '2026-08-20',
    hora_inicio: '10:00:00',
    materia: 1,
    carrera: 1,
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: '',
    alumno_nombre: 'Juan Pérez',
    asesor_nombre: 'Ana López',
    asistio: null,
    notas: 'trae dudas del examen',
    ...overrides,
  }
}

function montar() {
  vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
  const adminAsesorias = vi.spyOn(api, 'useAdminAsesorias').mockReturnValue({
    data: [asesoria()], isPending: false,
  } as ReturnType<typeof api.useAdminAsesorias>)
  vi.spyOn(api, 'useAdminSemestres').mockReturnValue({
    data: ['20262', '20261'], isPending: false,
  } as ReturnType<typeof api.useAdminSemestres>)
  vi.spyOn(api, 'useBuscarAsesores').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useBuscarAsesores>)
  vi.spyOn(api, 'useBuscarAlumnos').mockReturnValue({
    data: ALUMNOS, isPending: false,
  } as ReturnType<typeof api.useBuscarAlumnos>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )

  render(
    <MemoryRouter initialEntries={['/sae/asesorias']}>
      <Routes>
        <Route path="/sae/asesorias" element={<AdminAsesorias />} />
        <Route path="/sae/asesorias/oferta" element={<p>oferta SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
  return adminAsesorias
}

describe('AdminAsesorias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra los tabs Próximas e Historial', () => {
    montar()
    expect(screen.getByRole('tab', { name: 'Próximas' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Historial' })).toBeInTheDocument()
  })

  it('lista las sesiones con ambos nombres y sin las notas', () => {
    montar()
    expect(screen.getByText(/Juan Pérez · Ana López/)).toBeInTheDocument()
    expect(screen.queryByText(/trae dudas del examen/)).not.toBeInTheDocument()
  })

  it('el historial ofrece un subtab por semestre', () => {
    montar()
    fireEvent.click(screen.getByRole('tab', { name: 'Historial' }))
    expect(screen.getByRole('tab', { name: '20262' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '20261' })).toBeInTheDocument()
  })

  it('elegir un semestre consulta ese semestre', () => {
    const adminAsesorias = montar()
    fireEvent.click(screen.getByRole('tab', { name: 'Historial' }))
    fireEvent.click(screen.getByRole('tab', { name: '20261' }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: null, alumno: null, semestre: '20261' })
  })

  it('buscar y elegir un asesor dispara la consulta con ese asesor', () => {
    const adminAsesorias = montar()
    fireEvent.change(screen.getByLabelText('Asesor'), { target: { value: 'ana' } })
    // Acotado a la lista de resultados: la tarjeta admin también es un botón
    // y su nombre accesible incluye "Ana López".
    const resultados = screen.getByRole('list', { name: 'Resultados de asesores' })
    fireEvent.click(within(resultados).getByRole('button', { name: /Ana López/ }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: 7, alumno: null })
  })

  it('el filtro de alumno dispara la consulta con ese alumno', () => {
    const adminAsesorias = montar()
    fireEvent.change(screen.getByLabelText('Alumno'), { target: { value: 'jua' } })
    const resultados = screen.getByRole('list', { name: 'Resultados de alumnos' })
    fireEvent.click(within(resultados).getByRole('button', { name: /Juan Pérez/ }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: null, alumno: 15 })
  })

  it('navega a la consulta de oferta', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Consultar oferta' }))
    expect(screen.getByText('oferta SAE')).toBeInTheDocument()
  })
})
```

> **Por qué los clicks van acotados con `within`:** desde la Task C la tarjeta admin es un `<button>` cuyo nombre accesible incluye `Juan Pérez · Ana López`, igual que los botones de resultado de ambos buscadores. `within(screen.getByRole('list', { name: 'Resultados de asesores' }))` desambigua: los `<ul>` de resultados llevan `aria-label="Resultados de asesores"` / `"Resultados de alumnos"` **en el componente real** (`FiltroAsesor` / `FiltroAlumno`, ver Step 4), no sólo en el test. Las listas sólo existen con ≥2 caracteres escritos, así que `getByRole('list', …)` es unívoco.

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesorias.test.tsx`
Expected: FAIL — `AdminAsesorias` no existe.

- [ ] **Step 4: Implementar la pantalla**

Crear `frontend/src/features/asesorias/screens/AdminAsesorias.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import { Skeleton } from '../../../components/ui/Skeleton'
import { TarjetaAsesoria } from '../components/TarjetaAsesoria'
import { useAdminAsesorias, useAdminSemestres, useBuscarAlumnos, useBuscarAsesores } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { historial, proximas } from '../logica'
import type { AlumnoBusqueda, AsesorBusqueda, AsesoriaAdmin } from '../../../api/types'

export function AdminAsesorias() {
  const navigate = useNavigate()
  const mapaMaterias = useMapaMaterias()
  const [asesor, setAsesor] = useState<AsesorBusqueda | null>(null)
  const [alumno, setAlumno] = useState<AlumnoBusqueda | null>(null)
  const idAsesor = asesor?.perfil_id ?? null
  const idAlumno = alumno?.perfil_id ?? null

  const { data: asesorias = [], isPending } = useAdminAsesorias({ asesor: idAsesor, alumno: idAlumno })
  const nombreMateria = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <h1 className="text-lg font-semibold text-on-background">Asesorías · SAE</h1>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => navigate('/sae/asesorias/oferta')}
          className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
        >
          Consultar oferta
        </button>
        <button
          type="button"
          onClick={() => navigate('/sae/asesores')}
          className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
        >
          Asesores
        </button>
      </div>

      <div className="flex flex-col gap-3">
        <FiltroAsesor valor={asesor} onCambiar={setAsesor} />
        <FiltroAlumno valor={alumno} onCambiar={setAlumno} />
      </div>

      <Tabs defaultValue="proximas">
        <TabsList>
          <TabsTrigger value="proximas">Próximas</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="proximas">
          <ListaAdmin
            asesorias={proximas(asesorias)}
            cargando={isPending}
            nombreMateria={nombreMateria}
            vacio="No hay asesorías próximas con estos filtros."
          />
        </TabsContent>
        <TabsContent value="historial">
          <Historial asesor={idAsesor} alumno={idAlumno} nombreMateria={nombreMateria} />
        </TabsContent>
      </Tabs>
    </main>
  )
}

function FiltroAsesor({
  valor,
  onCambiar,
}: {
  valor: AsesorBusqueda | null
  onCambiar: (a: AsesorBusqueda | null) => void
}) {
  const [busqueda, setBusqueda] = useState('')
  // Espejo del filtro de alumno: el directorio crece y hay que poder buscar
  // por número de trabajador, así que es búsqueda en servidor y no un select.
  const { data: resultados = [] } = useBuscarAsesores(busqueda)

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="filtro-asesor" className="text-xs text-on-surface-variant">Asesor</label>
      <input
        id="filtro-asesor"
        type="text"
        placeholder="Nombre o número de trabajador…"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
      />

      {valor !== null ? (
        <button
          type="button"
          onClick={() => { onCambiar(null); setBusqueda('') }}
          aria-label={`Quitar filtro de ${valor.nombre}`}
          className="foco-visible min-h-11 w-fit rounded-full bg-primary-container px-3 text-sm text-on-primary-container"
        >
          {valor.nombre} ✕
        </button>
      ) : (
        busqueda.length >= 2 && resultados.length > 0 && (
          <ul className="flex flex-col gap-1" aria-label="Resultados de asesores">
            {resultados.map((a) => (
              <li key={a.perfil_id}>
                <button
                  type="button"
                  onClick={() => onCambiar(a)}
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-md bg-surface-container px-3 text-left text-sm text-on-surface"
                >
                  <span className="truncate" title={a.nombre}>{a.nombre}</span>
                  <span className="ml-3 shrink-0 text-xs text-on-surface-variant">{a.numero_trabajador}</span>
                </button>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  )
}

function FiltroAlumno({
  valor,
  onCambiar,
}: {
  valor: AlumnoBusqueda | null
  onCambiar: (a: AlumnoBusqueda | null) => void
}) {
  const [busqueda, setBusqueda] = useState('')
  // El conjunto de alumnos es grande: búsqueda en servidor, no select.
  const { data: resultados = [] } = useBuscarAlumnos(busqueda)

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="filtro-alumno" className="text-xs text-on-surface-variant">Alumno</label>
      <input
        id="filtro-alumno"
        type="text"
        placeholder="Nombre o número de cuenta…"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
      />

      {valor !== null ? (
        <button
          type="button"
          onClick={() => { onCambiar(null); setBusqueda('') }}
          aria-label={`Quitar filtro de ${valor.nombre}`}
          className="foco-visible min-h-11 w-fit rounded-full bg-primary-container px-3 text-sm text-on-primary-container"
        >
          {valor.nombre} ✕
        </button>
      ) : (
        busqueda.length >= 2 && resultados.length > 0 && (
          <ul className="flex flex-col gap-1" aria-label="Resultados de alumnos">
            {resultados.map((a) => (
              <li key={a.perfil_id}>
                <button
                  type="button"
                  onClick={() => onCambiar(a)}
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-md bg-surface-container px-3 text-left text-sm text-on-surface"
                >
                  <span className="truncate" title={a.nombre}>{a.nombre}</span>
                  <span className="ml-3 shrink-0 text-xs text-on-surface-variant">{a.numero_cuenta}</span>
                </button>
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  )
}

function Historial({
  asesor,
  alumno,
  nombreMateria,
}: {
  asesor: number | null
  alumno: number | null
  nombreMateria: (id: number) => string
}) {
  const { data: semestres = [], isPending } = useAdminSemestres()
  const [activo, setActivo] = useState<string | null>(null)
  const semestre = activo ?? semestres[0] ?? null

  if (isPending) return <Skeleton className="h-8 w-40" />
  if (semestre === null) return <p className="text-sm text-on-surface-variant">Aún no hay historial.</p>

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Semestre">
        {semestres.map((s) => (
          <button
            key={s}
            type="button"
            role="tab"
            aria-selected={s === semestre}
            onClick={() => setActivo(s)}
            className={`foco-visible min-h-11 rounded-full px-3 text-sm ${
              s === semestre ? 'bg-primary-container text-on-primary-container' : 'border border-outline text-primary'
            }`}
          >
            {s}
          </button>
        ))}
      </div>
      <ListaDeSemestre asesor={asesor} alumno={alumno} semestre={semestre} nombreMateria={nombreMateria} />
    </div>
  )
}

function ListaDeSemestre({
  asesor,
  alumno,
  semestre,
  nombreMateria,
}: {
  asesor: number | null
  alumno: number | null
  semestre: string
  nombreMateria: (id: number) => string
}) {
  const { data: asesorias = [], isPending } = useAdminAsesorias({ asesor, alumno, semestre })
  return (
    <ListaAdmin
      asesorias={historial(asesorias)}
      cargando={isPending}
      nombreMateria={nombreMateria}
      vacio="Sin sesiones en este semestre."
    />
  )
}

function ListaAdmin({
  asesorias,
  cargando,
  nombreMateria,
  vacio,
}: {
  asesorias: AsesoriaAdmin[]
  cargando: boolean
  nombreMateria: (id: number) => string
  vacio: string
}) {
  if (cargando) {
    return (
      <ul className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <li key={i}><Skeleton className="h-16" /></li>
        ))}
      </ul>
    )
  }

  if (asesorias.length === 0) {
    return <p className="text-sm text-on-surface-variant">{vacio}</p>
  }

  return (
    <ul className="flex flex-col gap-2">
      {asesorias.map((asesoria, indice) => (
        <TarjetaAsesoria
          key={asesoria.id}
          asesoria={asesoria}
          nombreMateria={nombreMateria(asesoria.materia)}
          indice={indice}
          admin
        />
      ))}
    </ul>
  )
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesorias.test.tsx`
Expected: PASS (7 casos).

- [ ] **Step 6: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminAsesorias.tsx frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx
git commit -m "[feat][frontend] pantalla SAE de asesorias agendadas e historico

- tabs Proximas/Historial con subtabs por semestre admin-wide
- filtros simetricos de busqueda: asesor (nombre o numero de trabajador) y alumno
- tarjetas en modo admin: ambos nombres, sin notas, clicables al detalle SAE

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task E: Pantalla `AdminDetalleAsesoria` (`/sae/asesorias/:id`, read-only)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AdminDetalleAsesoria.tsx`
- Test: `frontend/src/features/asesorias/screens/AdminDetalleAsesoria.test.tsx`
- Nota para Task 12: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `useLocation`/`useNavigate` de `react-router-dom`; `InsigniaEstado`; tipo `AsesoriaAdmin`.
- Produces: componente `AdminDetalleAsesoria`. Espejo **read-only** de `DetalleAsesoria`: botón volver, materia + `InsigniaEstado`, campos (fecha, hora, alumno, asesor, formato con ubicación o liga, asistencia) y "Notas de la sesión" sólo si no están vacías. **Cero mutaciones**: no importa `useGuardarNotas`, `useCancelarAsesoria`, `useMarcarAsistencia` ni `DialogoCancelar`; no hay `textarea` ni panel de "sesiones anteriores".

**Decisiones:**
1. **Sin endpoint nuevo y sin lectura de caché.** La sesión llega **por router state** desde `TarjetaAsesoria` (Task C): `state.asesoria` (`AsesoriaAdmin`, que ya incluye `notas`) y `state.nombreMateria` (`string`). La pantalla **no llama a ningún hook de datos**: nada de `useAdminAsesorias`, `useMapaMaterias`, `useParams` ni `?semestre=`. Esto evita el problema de que el listado admin esté cacheado por filtros y una sesión del historial no aparezca en la query por defecto.
2. **Deep-link / refresh → "Asesoría no encontrada".** Sin state no hay de dónde reconstruir la sesión; se muestra ese estado con el botón de volver. Es aceptable en el MVP: `/sae/asesorias/:id` no es una URL que se comparta ni se marque.
3. **No se muestra la carrera.** No aporta al supervisor y `AsesoriaAdmin` la trae sólo como `id`; `DetalleAsesoria` del asesor sí la resuelve con `useMapaCarreras` y no se toca.
4. **La ruta conserva el `:id`** aunque el componente no lo lea: mantiene la URL legible y deja la puerta abierta a resolver por `id` si algún día hay endpoint de detalle.

- [ ] **Step 1: GATE — mockup y aprobación del usuario**

Generar un artefacto HTML (herramienta `Artifact`) con el layout de `/sae/asesorias/:id`: botón "← Volver a Asesorías SAE", tarjeta con nombre de materia + insignia de estado, la lista de campos (Fecha, Hora, Alumno, Asesor, Formato con ubicación o liga, Asistencia) y el bloque "Notas de la sesión" en solo lectura. Mostrar también la variante sin notas y la variante "no encontrada".

**DETENERSE AQUÍ.** Esperar aprobación explícita del usuario antes de escribir código.

- [ ] **Step 2: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AdminDetalleAsesoria.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminDetalleAsesoria } from './AdminDetalleAsesoria'
import type { AsesoriaAdmin } from '../../../api/types'

function asesoria(overrides: Partial<AsesoriaAdmin> = {}): AsesoriaAdmin {
  return {
    id: 1,
    estado: 'realizada',
    fecha: '2026-08-20',
    hora_inicio: '10:00:00',
    materia: 1,
    carrera: 1,
    formato: 'presencial',
    ubicacion: 'Salón 4',
    liga_virtual: '',
    alumno_nombre: 'Juan Pérez',
    asesor_nombre: 'Ana López',
    asistio: true,
    notas: 'trae dudas del examen',
    ...overrides,
  }
}

/** La pantalla se alimenta sólo del router state; `MemoryRouter` acepta
 *  entradas como objeto `Location`, así que el state se inyecta ahí. */
function montar(state: unknown = { asesoria: asesoria(), nombreMateria: 'Cálculo I' }) {
  render(
    <MemoryRouter initialEntries={[{ pathname: '/sae/asesorias/1', state }]}>
      <Routes>
        <Route path="/sae/asesorias/:id" element={<AdminDetalleAsesoria />} />
        <Route path="/sae/asesorias" element={<p>lista SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminDetalleAsesoria', () => {
  it('muestra la materia, el estado y ambos nombres', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Cálculo I' })).toBeInTheDocument()
    expect(screen.getByText('Realizada')).toBeInTheDocument()
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('Ana López')).toBeInTheDocument()
  })

  it('muestra las notas de la sesión', () => {
    montar()
    expect(screen.getByText('Notas de la sesión')).toBeInTheDocument()
    expect(screen.getByText('trae dudas del examen')).toBeInTheDocument()
  })

  it('sin notas no muestra la sección de notas', () => {
    montar({ asesoria: asesoria({ notas: '   ' }), nombreMateria: 'Cálculo I' })
    expect(screen.queryByText('Notas de la sesión')).not.toBeInTheDocument()
  })

  it('no ofrece ninguna acción de escritura', () => {
    montar()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Guardar/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Cancelar/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /asistió/i })).not.toBeInTheDocument()
  })

  it('la sesión presencial muestra la ubicación', () => {
    montar()
    expect(screen.getByText('Salón 4')).toBeInTheDocument()
  })

  it('la sesión virtual muestra la liga', () => {
    montar({
      asesoria: asesoria({ formato: 'virtual', ubicacion: '', liga_virtual: 'https://meet.example.com/x' }),
      nombreMateria: 'Cálculo I',
    })
    expect(screen.getByRole('link', { name: 'Liga de la sesión' })).toHaveAttribute(
      'href',
      'https://meet.example.com/x',
    )
  })

  it('sin router state (deep-link o refresh) muestra el estado vacío', () => {
    montar(null)
    expect(screen.getByText(/No se encontró la asesoría/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Volver a Asesorías SAE/ })).toBeInTheDocument()
  })

  it('sin nombre de materia en el state cae al identificador', () => {
    montar({ asesoria: asesoria() })
    expect(screen.getByRole('heading', { name: 'Materia #1' })).toBeInTheDocument()
  })

  it('el botón volver regresa a la lista SAE', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Volver a Asesorías SAE/ }))
    expect(screen.getByText('lista SAE')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/AdminDetalleAsesoria.test.tsx`
Expected: FAIL — `AdminDetalleAsesoria` no existe.

- [ ] **Step 4: Implementar la pantalla**

Crear `frontend/src/features/asesorias/screens/AdminDetalleAsesoria.tsx`:

```tsx
import { useLocation, useNavigate } from 'react-router-dom'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import type { AsesoriaAdmin } from '../../../api/types'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
})

/** Lo que `TarjetaAsesoria` deja en el router state al navegar en modo admin. */
interface EstadoDetalleSAE {
  asesoria?: AsesoriaAdmin
  nombreMateria?: string
}

/**
 * Detalle read-only de una sesión para el área SAE.
 *
 * No hay endpoint de detalle admin y el listado está cacheado por combinación
 * de filtros (una sesión del historial no vive en la query por defecto), así
 * que la sesión llega por router state desde la tarjeta: esta pantalla no
 * consulta nada.
 *
 * Espejo de `DetalleAsesoria` sin ninguna mutación: el área /sae/* es de sólo
 * lectura, así que aquí no se monta guardar notas, cancelar ni asistencia.
 */
export function AdminDetalleAsesoria() {
  const navigate = useNavigate()
  const { state } = useLocation() as { state: EstadoDetalleSAE | null }
  const asesoria = state?.asesoria

  const volver = (
    <button
      type="button"
      onClick={() => navigate('/sae/asesorias')}
      className="foco-visible min-h-11 w-fit text-sm text-primary"
    >
      ← Volver a Asesorías SAE
    </button>
  )

  // Sin state no hay de dónde reconstruir la sesión: pasa en deep-link o al
  // recargar. En el MVP se acepta y se devuelve al usuario a la lista.
  if (!asesoria) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <p className="text-sm text-on-surface-variant">
          No se encontró la asesoría. Vuelve a la lista y ábrela desde ahí.
        </p>
        {volver}
      </main>
    )
  }

  const nombreMateria = state?.nombreMateria ?? `Materia #${asesoria.materia}`
  const notas = asesoria.notas.trim()

  return (
    <main className="flex min-h-svh flex-col gap-6 px-6 py-6">
      {volver}

      <section className="rounded-lg bg-surface-container p-4">
        <div className="mb-2 flex items-center justify-between gap-3">
          <h1 className="truncate text-base font-semibold text-on-surface" title={nombreMateria}>
            {nombreMateria}
          </h1>
          <InsigniaEstado estado={asesoria.estado} />
        </div>
        <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
          <dt>Fecha</dt>
          <dd>{FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))}</dd>
          <dt>Hora</dt>
          <dd>{asesoria.hora_inicio.slice(0, 5)}</dd>
          <dt>Alumno</dt>
          <dd>{asesoria.alumno_nombre}</dd>
          <dt>Asesor</dt>
          <dd>{asesoria.asesor_nombre}</dd>
          <dt>Formato</dt>
          <dd>
            {asesoria.formato === 'virtual' ? (
              <a
                href={asesoria.liga_virtual}
                target="_blank"
                rel="noreferrer"
                className="foco-visible text-primary underline"
              >
                Liga de la sesión
              </a>
            ) : (
              asesoria.ubicacion
            )}
          </dd>
          <dt>Asistencia</dt>
          <dd>
            {asesoria.asistio === null
              ? 'Sin registrar'
              : asesoria.asistio
                ? 'El alumno asistió'
                : 'El alumno no asistió'}
          </dd>
        </dl>
      </section>

      {notas !== '' && (
        <section className="rounded-lg bg-surface-container-low p-4">
          <h2 className="mb-2 text-sm font-medium text-on-surface">Notas de la sesión</h2>
          <p className="whitespace-pre-line text-sm text-on-surface-variant">{notas}</p>
        </section>
      )}
    </main>
  )
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/AdminDetalleAsesoria.test.tsx`
Expected: PASS (9 casos).

- [ ] **Step 6: Nota para la Task 12 (`App.tsx`) — NO se commitea aquí**

Al ejecutar la **Task 12** del plan base, además de las 5 rutas ya listadas hay que añadir esta sexta. En el bloque de imports de la Task 12 (Step 1), agregar:

```tsx
import { AdminDetalleAsesoria } from './features/asesorias/screens/AdminDetalleAsesoria'
```

Y en el Step 2, insertar esta ruta **después** de `/sae/asesorias/oferta/:materiaId` y **antes** de `/sae/asesores` (React Router v7 casa por especificidad, no por orden, así que la posición es sólo de legibilidad):

```tsx
        <Route
          path="/sae/asesorias/:id"
          element={
            <RutaDeSAE>
              <AdminDetalleAsesoria />
            </RutaDeSAE>
          }
        />
```

El Step 4 de la Task 12 (suite completa) debe listar también `AdminDetalleAsesoria` entre los verdes esperados.

- [ ] **Step 7: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminDetalleAsesoria.tsx frontend/src/features/asesorias/screens/AdminDetalleAsesoria.test.tsx
git commit -m "[feat][frontend] detalle read-only de asesoria para el area SAE

- /sae/asesorias/:id muestra datos de la sesion y las notas, sin edicion
- la sesion llega por router state desde la tarjeta: sin endpoint ni consulta nueva
- deep-link o refresh caen en el estado \"no encontrada\" con vuelta a la lista

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Verificación final del addendum

- [ ] `cd backend && uv run python manage.py test -v 2` → PASS
- [ ] Desde `frontend/`: `npm test && npm run build && npm run lint` → PASS
- [ ] `git log --oneline -6` muestra el commit de backend **aislado** (sin archivos de `frontend/` en `git show --stat`)

---

## Puntos resueltos por el orquestador (2026-08-12) — ya incorporados arriba

Los cuatro `⚠️ VERIFICAR` del borrador quedaron cerrados con estas decisiones. **No re-litigar; el código de arriba ya las refleja.**

1. **Sesiones del historial en el detalle SAE → router state.** Se descartó leer de la caché por-filtro y se descartó el `?semestre=`. `TarjetaAsesoria` (Task C) navega con `navigate('/sae/asesorias/:id', { state: { asesoria, nombreMateria } })` y `AdminDetalleAsesoria` (Task E) lee `useLocation().state`. La pantalla de detalle **no monta ningún hook de datos**. Sin state (deep-link/refresh) → "No se encontró la asesoría" + volver. Se descarta la prop `rutaDetalle` y cualquier cambio en `ListaAdmin`.

2. **Fixtures de `AsesorDirectorio`.** Verificado: en este addendum no queda ningún literal `AsesorDirectorio` (la Task D usa `AsesorBusqueda`, que incluye `numero_trabajador`). La obligación para las Tasks 10 y 11 quedó anotada en el bloque **⚑ Nota obligatoria** al inicio del documento.

3. **Ambigüedad de `/Ana López/`.** Resuelta *en el test*, no como contingencia: los clicks en resultados van con `within(screen.getByRole('list', { name: 'Resultados de asesores' | 'Resultados de alumnos' }))`. Los `aria-label` están en el **componente real** (`FiltroAsesor` y `FiltroAlumno`, Task D Step 4), no sólo en el test.

4. **Límite en `?buscar=` de asesores.** Se aplica `LIMITE_AUTOCOMPLETAR_ASESORES = 20` **sólo cuando viene `buscar`**, con `order_by` en SQL antes del corte para que sea determinista. Sin `buscar`, el directorio va completo (lo consume la Task 10). Cubierto por dos tests: `test_la_busqueda_respeta_el_limite_de_resultados` y `test_el_directorio_sin_buscar_no_lleva_corte`.
