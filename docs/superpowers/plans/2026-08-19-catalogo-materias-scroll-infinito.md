# Catálogo de materias: paginación + scroll infinito — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Paginar `GET /api/materias/materias/` (50 por página) con búsqueda en backend, y reescribir `DialogoAgregarMateria` con scroll infinito, búsqueda con debounce y selector de carrera, sin romper los 6 consumidores que dependen del catálogo completo.

**Architecture:** Backend: `pagination_class` propia de `MateriaViewSet` (no global) + `SearchFilter` sobre `nombre`/`clave`. Frontend: `catalogo/api.ts` gana un constructor de rutas, una función que recorre todas las páginas (para `useMaterias()`, que sigue devolviendo `Materia[]` completo) y un `useMateriasInfinitas()` con `useInfiniteQuery` usado solo por `DialogoAgregarMateria`. El diálogo pasa de filtrar en cliente a filtrar en backend, con `IntersectionObserver` sobre un `<li>` sentinela.

**Tech Stack:** Django 6 + DRF 3.17 (backend, `uv`); React 19 + TypeScript + Vite + TanStack Query v5 + Tailwind 4 + vitest/RTL (frontend).

**Spec:** [`docs/superpowers/specs/2026-08-19-catalogo-materias-scroll-infinito-design.md`](../specs/2026-08-19-catalogo-materias-scroll-infinito-design.md)

---

## Global Constraints

- **Tamaño de página: 50.** Valor fijado por este plan (el spec lo dejaba abierto). Se declara una sola vez, en `backend/materias/pagination.py`.
- **Debounce de búsqueda: 300ms.** Declarado como `RETRASO_BUSQUEDA_MS` en `DialogoAgregarMateria.tsx`.
- **La paginación es propia de `MateriaViewSet`.** Prohibido agregar `DEFAULT_PAGINATION_CLASS` a `REST_FRAMEWORK` en `backend/config/settings/base.py`. El resto de los listados del proyecto queda intacto.
- **Comando de tests backend:** desde `backend/`, `uv run manage.py test <ruta> -v 2`. Requiere Postgres: `docker compose -f docker-compose.dev.yml up -d postgres redis` desde la raíz del repo. Alternativa: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test <ruta> -v 2`.
- **Comandos frontend** (desde `frontend/`): test puntual `npx vitest run <ruta>`; suite `npm test`; build `npm run build`; lint `npm run lint`.
- **Commits:** formato `[type][scope] resumen` + lista de bullets + `Signed-off-by`. Usar `git commit -s` (git config ya tiene `Héctor Olvera Vital <hector.olvera@ciencias.unam.mx>`). Ver [`docs/development/commit-conventions.md`](../../development/commit-conventions.md).
- **Rama:** `dev`. No abrir PR ni hacer push salvo que Héctor lo pida.
- **No tocar** nada fuera de los archivos listados en cada tarea. Fuera de alcance explícito: paginar `RegistroAsesor`/`Disponibilidad`/`Asesoria`/`carreras`, y generalizar `apiGet` a un cliente consciente de paginación.
- **No "mejorar" el código de este plan.** Los bloques son literales: se pegan tal cual, incluidos comentarios y textos en español.

---

## File Structure

| Archivo | Responsabilidad | Acción | Tarea |
|---|---|---|---|
| `backend/materias/pagination.py` | `PaginacionMaterias(PageNumberPagination)`, `page_size = 50` | Crear | 1 |
| `backend/materias/views.py` | `pagination_class` + `filter_backends`/`search_fields` en `MateriaViewSet` | Modificar | 1 |
| `backend/materias/tests/test_api.py` | Tests existentes adaptados al envelope + tests de paginación y búsqueda | Modificar | 1 |
| `backend/asesorias/tests/test_api_flujo_completo.py:59` | Lee `response.data[0]` del catálogo — pasa a `response.data["results"][0]` | Modificar | 1 |
| `docs/development/api-frontend.md` | Sección `materias`: envelope, `?page`, `?search` | Modificar | 1 |
| `frontend/src/api/types.ts` | `RespuestaPaginada<T>` | Modificar | 2 |
| `frontend/src/features/catalogo/api.ts` | `construirRutaMaterias`, `obtenerTodasLasMaterias`, `useMaterias` | Modificar | 2 |
| `frontend/src/features/catalogo/api.test.ts` | Tests del constructor de rutas y del recorrido de páginas | Crear | 2 |
| `frontend/src/features/catalogo/api.ts` | `ParametrosMaterias`, `useMateriasInfinitas` | Modificar | 3 |
| `frontend/src/features/catalogo/api.test.ts` | Test del `queryFn`/`getNextPageParam` del hook infinito | Modificar | 3 |
| `frontend/src/test/setup.ts` | Stub no-op de `IntersectionObserver` para jsdom | Modificar | 4 |
| `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx` | Selector de carrera + búsqueda en backend + scroll infinito | Reescribir | 4 |
| `frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx` | Tests del diálogo nuevo | Reescribir | 4 |
| `docs/decisions/0029-paginacion-busqueda-catalogo-materias.md` | ADR de la decisión | Crear | 5 |
| `docs/technical-debt/0006-sin-paginacion-listados.md` | Sección de cobertura parcial 2026-08-19 | Modificar | 5 |
| `docs/technical-debt/0022-useMaterias-recorre-todas-las-paginas.md` | Deuda nueva del loop de N requests | Crear | 5 |
| `docs/technical-debt/README.md` | Índice: alta de 0022 | Modificar | 5 |

---

## Task 1: Backend — paginación + búsqueda en `MateriaViewSet`

**Files:**
- Create: `backend/materias/pagination.py`
- Modify: `backend/materias/views.py`
- Modify: `backend/materias/tests/test_api.py`
- Modify: `backend/asesorias/tests/test_api_flujo_completo.py:59`
- Modify: `docs/development/api-frontend.md:121-133`

**Interfaces:**
- Produces: `backend/materias/pagination.PaginacionMaterias` (subclase de `rest_framework.pagination.PageNumberPagination`, `page_size = 50`).
- Produces: `GET /api/materias/materias/` responde `{"count": int, "next": str|null, "previous": str|null, "results": [MateriaSerializer]}`; acepta `?page=<n>`, `?search=<texto>`, `?carrera=<id>`, `?habilitada_asesorias=<bool>`.

- [ ] **Step 1: Escribir los tests que fallan (reemplaza el archivo completo)**

Escribir `backend/materias/tests/test_api.py` con este contenido exacto:

```python
from accounts.models import User
from carreras.models import Area, Carrera
from materias.models import Materia
from rest_framework.test import APITestCase


class CatalogoMateriasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Test area")
        self.carrera1 = Carrera.objects.create(clave=801, nombre="Test carrera 1", area=self.area)
        self.carrera2 = Carrera.objects.create(clave=802, nombre="Test carrera 2", area=self.area)
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

    def tearDown(self):
        self.materia_otra_carrera.delete()
        self.materia_no_habilitada.delete()
        self.materia_habilitada.delete()
        self.carrera2.delete()
        self.carrera1.delete()
        self.area.delete()
        self.user.delete()

        return super().tearDown()

    def test_listar_todas(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

    def test_respuesta_trae_el_envelope_de_paginacion(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()), {"count", "next", "previous", "results"}
        )
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_detalle_no_trae_envelope(self):
        response = self.client.get(f"/api/materias/materias/{self.materia_habilitada.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["clave"], "1801")

    def test_filtrar_por_carrera(self):
        response = self.client.get(f"/api/materias/materias/?carrera={self.carrera1.id}")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801", "1802"})

    def test_filtrar_por_habilitada_asesorias(self):
        response = self.client.get("/api/materias/materias/?habilitada_asesorias=true")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801", "1901"})

    def test_filtrar_por_carrera_y_habilitada(self):
        response = self.client.get(
            f"/api/materias/materias/?carrera={self.carrera1.id}&habilitada_asesorias=true"
        )
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801"})

    def test_buscar_por_nombre_parcial_insensible_a_mayusculas(self):
        response = self.client.get("/api/materias/materias/?search=TOPO")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1901"})

    def test_buscar_por_clave(self):
        response = self.client.get("/api/materias/materias/?search=1802")
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1802"})

    def test_buscar_combinado_con_carrera_y_habilitada(self):
        response = self.client.get(
            f"/api/materias/materias/?search=a&carrera={self.carrera1.id}"
            "&habilitada_asesorias=true"
        )
        self.assertEqual(response.status_code, 200)
        claves = {m["clave"] for m in response.data["results"]}
        self.assertEqual(claves, {"1801"})

    def test_buscar_sin_coincidencias_devuelve_lista_vacia(self):
        response = self.client.get("/api/materias/materias/?search=zzzzz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])


class PaginacionMateriasApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="b@ciencias.unam.mx", password="x")
        self.area = Area.objects.create(nombre="Area paginacion")
        self.carrera = Carrera.objects.create(clave=803, nombre="Carrera paginacion", area=self.area)
        Materia.objects.bulk_create(
            [
                Materia(
                    clave=f"9{indice:03d}",
                    nombre=f"Materia {indice:03d}",
                    carrera=self.carrera,
                    nivel=1,
                    plan=2006,
                    habilitada_asesorias=True,
                )
                for indice in range(60)
            ]
        )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        Materia.objects.filter(carrera=self.carrera).delete()
        self.carrera.delete()
        self.area.delete()
        self.user.delete()

        return super().tearDown()

    def test_primera_pagina_trae_50_y_apunta_a_la_siguiente(self):
        response = self.client.get("/api/materias/materias/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 60)
        self.assertEqual(len(response.data["results"]), 50)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_segunda_pagina_trae_el_resto_y_cierra_la_secuencia(self):
        response = self.client.get("/api/materias/materias/?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_paginas_no_repiten_materias(self):
        primera = self.client.get("/api/materias/materias/")
        segunda = self.client.get("/api/materias/materias/?page=2")
        claves = [m["clave"] for m in primera.data["results"]] + [
            m["clave"] for m in segunda.data["results"]
        ]
        self.assertEqual(len(claves), 60)
        self.assertEqual(len(set(claves)), 60)

    def test_pagina_fuera_de_rango_devuelve_404(self):
        response = self.client.get("/api/materias/materias/?page=99")
        self.assertEqual(response.status_code, 404)

    def test_busqueda_acotada_cabe_en_una_pagina(self):
        # "007" coincide con el nombre "Materia 007" y con la clave "9007" —
        # la misma fila, una sola vez: SearchFilter une los campos con OR.
        response = self.client.get("/api/materias/materias/?search=007")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertIsNone(response.data["next"])
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `cd backend && uv run manage.py test materias.tests.test_api -v 2`
Expected: FAIL — `TypeError: list indices must be integers or slices, not str` / `KeyError` en `response.data["count"]` (la respuesta todavía es un array plano).

- [ ] **Step 3: Crear la clase de paginación**

Crear `backend/materias/pagination.py`:

```python
from rest_framework.pagination import PageNumberPagination


class PaginacionMaterias(PageNumberPagination):
    """Paginación del catálogo de materias (400+ registros).

    Propia de `MateriaViewSet`, no `DEFAULT_PAGINATION_CLASS`: el resto de los
    listados del proyecto sigue devolviendo la colección completa (deuda 0006)
    y cambiarlos globalmente los rompería sin haberlos revisado.

    50 por página: pocos round-trips para el loop de `useMaterias()` en el
    frontend, y primer render rápido en el scroll infinito del diálogo de
    agregar materia.
    """

    page_size = 50
```

- [ ] **Step 4: Conectar paginación y búsqueda al viewset**

Reemplazar el contenido completo de `backend/materias/views.py`:

```python
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Materia
from .pagination import PaginacionMaterias
from .serializers import MateriaSerializer


class MateriaViewSet(ReadOnlyModelViewSet):
    serializer_class = MateriaSerializer
    pagination_class = PaginacionMaterias
    # `?search=` de DRF: icontains sobre cada campo, unidos por OR. Se aplica
    # después de `get_queryset`, así que se combina con `carrera` y
    # `habilitada_asesorias` sin trabajo extra.
    filter_backends = [SearchFilter]
    search_fields = ["nombre", "clave"]

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

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `cd backend && uv run manage.py test materias.tests.test_api -v 2`
Expected: PASS — 15 tests.

- [ ] **Step 6: Adaptar el único otro test que consume el listado**

En `backend/asesorias/tests/test_api_flujo_completo.py`, línea 59, reemplazar:

```python
        materia_id = response.data[0]["id"]
```

por:

```python
        materia_id = response.data["results"][0]["id"]
```

- [ ] **Step 7: Correr la suite completa del backend**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS — ningún otro test consume `/api/materias/materias/` como array plano.

- [ ] **Step 8: Actualizar la doc de la API**

En `docs/development/api-frontend.md`, reemplazar el bloque de las líneas 121-133 (desde `## \`materias\`` hasta la línea que termina en `nunca vía API.`) por:

```markdown
## `materias`

Solo lectura, **paginado**: `PageNumberPagination` con `page_size = 50`, declarado en `materias/pagination.py` como `pagination_class` propia de este viewset (no hay `DEFAULT_PAGINATION_CLASS` global — el resto de los listados sigue devolviendo array plano, deuda [0006](../technical-debt/0006-sin-paginacion-listados.md)). Una página fuera de rango responde `404`.

Filtros por query param:

- `?page=<n>` — 1-indexado; se omite para la primera página.
- `?carrera=<id>` — comparación manual en `get_queryset`, no `django-filter`.
- `?habilitada_asesorias=<bool>` — solo `"1"`/`"true"` (case-insensitive) cuentan como verdadero; cualquier otro valor, incluido `"yes"`, se trata como falso.
- `?search=<texto>` — `SearchFilter` de DRF sobre `search_fields = ["nombre", "clave"]`: coincidencia parcial insensible a mayúsculas, OR entre los dos campos. Se combina con `carrera` y `habilitada_asesorias`.

| Método | Ruta | Response |
|---|---|---|
| `GET` | `/api/materias/materias/` | `{count, next, previous, results: [{id, clave, nombre, carrera, nivel, plan, habilitada_asesorias}]}` |
| `GET` | `/api/materias/materias/{id}/` | `{id, clave, nombre, carrera, nivel, plan, habilitada_asesorias}` — un objeto, **sin** envelope |

`carrera` aquí es un id plano (a diferencia de `carreras.area`, que va anidado). No hay endpoint para `OfertaMateria` — se carga por management command, nunca vía API.
```

- [ ] **Step 9: Commit**

```bash
cd /home/hyfi/Development/atenea-fc && git add backend/materias/pagination.py backend/materias/views.py backend/materias/tests/test_api.py backend/asesorias/tests/test_api_flujo_completo.py docs/development/api-frontend.md && git commit -s -m "$(cat <<'EOF'
[feat][backend] paginar y hacer buscable el catalogo de materias

- agregar PaginacionMaterias (PageNumberPagination, page_size=50) como
  pagination_class propia de MateriaViewSet, sin tocar REST_FRAMEWORK
- agregar SearchFilter con search_fields = ["nombre", "clave"], que se
  combina con los filtros carrera y habilitada_asesorias existentes
- adaptar los tests existentes al envelope {count, next, previous, results}
  y cubrir paginacion, busqueda y su combinacion con los filtros
- adaptar el paso 1 del test de flujo completo de asesorias, que leia
  response.data[0]
- documentar el envelope, ?page y ?search en api-frontend.md
EOF
)"
```

---

## Task 2: Frontend — `useMaterias()` recorre todas las páginas

**Files:**
- Modify: `frontend/src/api/types.ts` (agregar `RespuestaPaginada<T>` después de la interfaz `Materia`)
- Modify: `frontend/src/features/catalogo/api.ts`
- Test: `frontend/src/features/catalogo/api.test.ts` (crear)

**Interfaces:**
- Consumes: envelope `{count, next, previous, results}` de Task 1.
- Produces: `RespuestaPaginada<T>` en `frontend/src/api/types.ts` — `{ count: number; next: string | null; previous: string | null; results: T[] }`.
- Produces: `construirRutaMaterias(params?: ParametrosRutaMaterias): string` en `frontend/src/features/catalogo/api.ts`, con `interface ParametrosRutaMaterias { carrera?: number | null; search?: string; habilitada_asesorias?: boolean; page?: number }`.
- Produces: `obtenerTodasLasMaterias(): Promise<Materia[]>` en el mismo archivo.
- Produces: `useMaterias()` sigue devolviendo `UseQueryResult<Materia[]>` con `queryKey: ['materias']` — firma sin cambios para los 6 consumidores.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/features/catalogo/api.test.ts`:

```ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import { construirRutaMaterias, obtenerTodasLasMaterias } from './api'
import type { Materia } from '../../api/types'

const originalFetch = global.fetch

const mockLocalStorage = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', { value: mockLocalStorage, writable: true })

function materia(id: number): Materia {
  return {
    id,
    clave: `000${id}`,
    nombre: `Materia ${id}`,
    carrera: 1,
    nivel: null,
    plan: 2006,
    habilitada_asesorias: true,
  }
}

function respuesta(cuerpo: unknown) {
  return { ok: true, status: 200, json: async () => cuerpo } as Response
}

describe('construirRutaMaterias', () => {
  it('sin parámetros devuelve la ruta desnuda', () => {
    expect(construirRutaMaterias()).toBe('/api/materias/materias/')
  })

  it('omite page=1 porque el backend ya la sirve por defecto', () => {
    expect(construirRutaMaterias({ page: 1 })).toBe('/api/materias/materias/')
  })

  it('serializa habilitada_asesorias como 1 o 0', () => {
    expect(construirRutaMaterias({ habilitada_asesorias: true })).toBe(
      '/api/materias/materias/?habilitada_asesorias=1',
    )
    expect(construirRutaMaterias({ habilitada_asesorias: false })).toBe(
      '/api/materias/materias/?habilitada_asesorias=0',
    )
  })

  it('omite carrera null y search vacío', () => {
    expect(construirRutaMaterias({ carrera: null, search: '' })).toBe('/api/materias/materias/')
  })

  it('combina habilitada_asesorias, carrera, search y page', () => {
    expect(
      construirRutaMaterias({ habilitada_asesorias: true, carrera: 7, search: 'ál ge', page: 3 }),
    ).toBe('/api/materias/materias/?habilitada_asesorias=1&carrera=7&search=%C3%A1l+ge&page=3')
  })
})

describe('obtenerTodasLasMaterias', () => {
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('devuelve el array completo con una sola página', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue(respuesta({ count: 1, next: null, previous: null, results: [materia(1)] }))

    await expect(obtenerTodasLasMaterias()).resolves.toEqual([materia(1)])
  })

  it('recorre todas las páginas hasta que next es null y concatena los resultados', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        respuesta({
          count: 3,
          next: 'http://x/api/materias/materias/?page=2',
          previous: null,
          results: [materia(1)],
        }),
      )
      .mockResolvedValueOnce(
        respuesta({
          count: 3,
          next: 'http://x/api/materias/materias/?page=3',
          previous: 'http://x/api/materias/materias/',
          results: [materia(2)],
        }),
      )
      .mockResolvedValueOnce(
        respuesta({
          count: 3,
          next: null,
          previous: 'http://x/api/materias/materias/?page=2',
          results: [materia(3)],
        }),
      )
    global.fetch = fetchMock

    const materias = await obtenerTodasLasMaterias()

    expect(materias.map((m) => m.id)).toEqual([1, 2, 3])
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/materias/materias/')
    expect(String(fetchMock.mock.calls[1][0])).toContain('page=2')
    expect(String(fetchMock.mock.calls[2][0])).toContain('page=3')
  })

  it('devuelve vacío cuando el catálogo está vacío', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue(respuesta({ count: 0, next: null, previous: null, results: [] }))

    await expect(obtenerTodasLasMaterias()).resolves.toEqual([])
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd frontend && npx vitest run src/features/catalogo/api.test.ts`
Expected: FAIL — `does not provide an export named 'construirRutaMaterias'`.

- [ ] **Step 3: Agregar `RespuestaPaginada<T>` a los tipos**

En `frontend/src/api/types.ts`, insertar después de la interfaz `Materia` (que termina en la línea 64 con `}`) y antes de `export interface Carrera {`:

```ts
/**
 * Envelope de `PageNumberPagination` de DRF. Hoy solo lo usa el catálogo de
 * materias (`materias/pagination.py`, 50 por página); el resto de los
 * listados del proyecto sigue devolviendo array plano (deuda 0006).
 */
export interface RespuestaPaginada<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
```

- [ ] **Step 4: Reescribir `catalogo/api.ts`**

Reemplazar el contenido completo de `frontend/src/features/catalogo/api.ts`:

```ts
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../api/client'
import type { Materia, Carrera, RespuestaPaginada } from '../../api/types'

const RUTA_MATERIAS = '/api/materias/materias/'

export interface ParametrosRutaMaterias {
  /** `null` = todas las carreras. */
  carrera?: number | null
  /** Cadena vacía = sin búsqueda; viaja como `?search=` al backend. */
  search?: string
  habilitada_asesorias?: boolean
  /** 1-indexado. La página 1 se omite de la URL. */
  page?: number
}

/**
 * Arma la ruta del catálogo paginado. Vive aquí y no en `api/client.ts`: por
 * ahora este es el único endpoint paginado del proyecto, generalizar `apiGet`
 * es prematuro.
 */
export function construirRutaMaterias(params: ParametrosRutaMaterias = {}): string {
  const query = new URLSearchParams()
  if (params.habilitada_asesorias !== undefined) {
    query.set('habilitada_asesorias', params.habilitada_asesorias ? '1' : '0')
  }
  if (params.carrera !== undefined && params.carrera !== null) {
    query.set('carrera', String(params.carrera))
  }
  if (params.search !== undefined && params.search !== '') {
    query.set('search', params.search)
  }
  if (params.page !== undefined && params.page > 1) {
    query.set('page', String(params.page))
  }
  const cadena = query.toString()
  return cadena === '' ? RUTA_MATERIAS : `${RUTA_MATERIAS}?${cadena}`
}

/**
 * Recorre todas las páginas del catálogo y devuelve el array completo.
 *
 * Existe para que `useMaterias()` siga cumpliendo el contrato que asumen sus
 * consumidores de lookup (`useMapaMaterias`), que necesitan el catálogo entero
 * en memoria. Cuesta N requests secuenciales en vez de 1 — deuda 0022.
 */
export async function obtenerTodasLasMaterias(): Promise<Materia[]> {
  const materias: Materia[] = []
  let pagina = 1
  let hayMas = true
  while (hayMas) {
    const respuesta = await apiGet<RespuestaPaginada<Materia>>(
      construirRutaMaterias({ page: pagina }),
    )
    materias.push(...respuesta.results)
    hayMas = respuesta.next !== null
    pagina += 1
  }
  return materias
}

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: obtenerTodasLasMaterias,
    staleTime: Infinity,
  })
}

export function useCarreras() {
  return useQuery({
    queryKey: ['carreras'],
    queryFn: () => apiGet<Carrera[]>('/api/carreras/carreras/'),
    staleTime: Infinity,
  })
}

export function useMapaMaterias(): Map<number, Materia> {
  const { data } = useMaterias()
  return useMemo(() => new Map((data ?? []).map((materia) => [materia.id, materia])), [data])
}

export function useMapaCarreras(): Map<number, Carrera> {
  const { data } = useCarreras()
  return useMemo(() => new Map((data ?? []).map((carrera) => [carrera.id, carrera])), [data])
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `cd frontend && npx vitest run src/features/catalogo/api.test.ts`
Expected: PASS — 8 tests.

- [ ] **Step 6: Correr la suite completa y el typecheck**

Run: `cd frontend && npm test && npm run build && npm run lint`
Expected: PASS. Los 6 consumidores de `useMapaMaterias()` no cambian de firma; sus tests mockean el hook y siguen verdes.

- [ ] **Step 7: Commit**

```bash
cd /home/hyfi/Development/atenea-fc && git add frontend/src/api/types.ts frontend/src/features/catalogo/api.ts frontend/src/features/catalogo/api.test.ts && git commit -s -m "$(cat <<'EOF'
[feat][frontend] adaptar useMaterias al catalogo paginado

- agregar el tipo RespuestaPaginada<T> con el envelope de DRF
- agregar construirRutaMaterias, que serializa carrera/search/page y
  habilitada_asesorias como 1|0
- agregar obtenerTodasLasMaterias, que recorre paginas hasta next === null,
  para que useMaterias siga devolviendo Materia[] a los 6 consumidores de
  lookup sin cambios de firma
- cubrir el constructor de rutas y el recorrido de paginas con tests
EOF
)"
```

---

## Task 3: Frontend — hook `useMateriasInfinitas`

**Files:**
- Modify: `frontend/src/features/catalogo/api.ts`
- Test: `frontend/src/features/catalogo/api.test.ts`

**Interfaces:**
- Consumes: `construirRutaMaterias`, `ParametrosRutaMaterias`, `RespuestaPaginada<T>` de Task 2.
- Produces: `interface ParametrosMaterias { carrera?: number | null; search?: string; habilitada_asesorias?: boolean }` en `frontend/src/features/catalogo/api.ts`.
- Produces: `useMateriasInfinitas(params: ParametrosMaterias)` — `UseInfiniteQueryResult<InfiniteData<RespuestaPaginada<Materia>>>`. Task 4 usa de su retorno: `data` (con `data.pages[i].results`), `fetchNextPage`, `hasNextPage`, `isFetchingNextPage`.
- Produces: `siguientePagina(ultima: RespuestaPaginada<Materia>, todas: RespuestaPaginada<Materia>[]): number | undefined` — exportada solo para poder testear `getNextPageParam` sin montar React.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/features/catalogo/api.test.ts`, reemplazar la línea 2:

```ts
import { construirRutaMaterias, obtenerTodasLasMaterias } from './api'
```

por:

```ts
import { construirRutaMaterias, obtenerTodasLasMaterias, siguientePagina } from './api'
```

Y agregar al final del mismo archivo:

```ts
describe('siguientePagina', () => {
  function paginaCon(next: string | null): RespuestaPaginada<Materia> {
    return { count: 60, next, previous: null, results: [] }
  }

  it('devuelve undefined cuando next es null, para cortar el scroll infinito', () => {
    const cargadas = [paginaCon(null)]
    expect(siguientePagina(cargadas[0], cargadas)).toBeUndefined()
  })

  it('devuelve el número de páginas ya cargadas + 1', () => {
    const cargadas = [paginaCon('http://x/?page=2'), paginaCon('http://x/?page=3')]
    expect(siguientePagina(cargadas[1], cargadas)).toBe(3)
  })
})
```

Y ampliar el import de tipos de la línea 3 del archivo:

```ts
import type { Materia } from '../../api/types'
```

a:

```ts
import type { Materia, RespuestaPaginada } from '../../api/types'
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd frontend && npx vitest run src/features/catalogo/api.test.ts`
Expected: FAIL — `siguientePagina is not a function`.

- [ ] **Step 3: Agregar el hook infinito**

En `frontend/src/features/catalogo/api.ts`, cambiar la línea de import de TanStack Query:

```ts
import { useQuery } from '@tanstack/react-query'
```

por:

```ts
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
```

Y agregar al final del archivo:

```ts
export interface ParametrosMaterias {
  /** `null` = todas las carreras. */
  carrera?: number | null
  /** Cadena vacía = sin búsqueda. */
  search?: string
  habilitada_asesorias?: boolean
}

/**
 * `getNextPageParam` de `useMateriasInfinitas`, extraída para poder testearla
 * sin montar React. `next === null` corta el scroll infinito.
 */
export function siguientePagina(
  ultima: RespuestaPaginada<Materia>,
  todas: RespuestaPaginada<Materia>[],
): number | undefined {
  return ultima.next === null ? undefined : todas.length + 1
}

/**
 * Catálogo paginado para listar+buscar (hoy solo `DialogoAgregarMateria`).
 *
 * Los consumidores de lookup usan `useMaterias()`, no este hook: aquí el
 * catálogo llega por partes y no sirve para resolver un nombre por id.
 * `carrera` y `search` entran a la `queryKey`, así que cambiar cualquiera
 * reinicia la paginación desde la página 1.
 */
export function useMateriasInfinitas(params: ParametrosMaterias) {
  const carrera = params.carrera ?? null
  const search = params.search ?? ''
  const habilitadaAsesorias = params.habilitada_asesorias ?? null
  return useInfiniteQuery({
    queryKey: ['materias', 'infinitas', carrera, search, habilitadaAsesorias],
    queryFn: ({ pageParam }) =>
      apiGet<RespuestaPaginada<Materia>>(
        construirRutaMaterias({ ...params, page: pageParam }),
      ),
    initialPageParam: 1,
    getNextPageParam: siguientePagina,
  })
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd frontend && npx vitest run src/features/catalogo/api.test.ts`
Expected: PASS — 10 tests.

- [ ] **Step 5: Typecheck y lint**

Run: `cd frontend && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/hyfi/Development/atenea-fc && git add frontend/src/features/catalogo/api.ts frontend/src/features/catalogo/api.test.ts && git commit -s -m "$(cat <<'EOF'
[feat][frontend] agregar useMateriasInfinitas con useInfiniteQuery

- nuevo hook para listar+buscar el catalogo paginado, con carrera, search y
  habilitada_asesorias en la queryKey para reiniciar la paginacion al
  cambiar cualquiera de los tres
- extraer siguientePagina como getNextPageParam testeable: corta el scroll
  infinito cuando next === null
- cubrir siguientePagina con tests
EOF
)"
```

---

## Task 4: Frontend — `DialogoAgregarMateria` con carrera, búsqueda en backend y scroll infinito

**Files:**
- Modify: `frontend/src/test/setup.ts`
- Modify: `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx` (reescritura completa)
- Test: `frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx` (reescritura completa)

**Interfaces:**
- Consumes: `useMateriasInfinitas(params: ParametrosMaterias)` y `useCarreras()` de `../../catalogo/api`.
- Produces: `DialogoAgregarMateria` conserva exactamente sus props actuales — `{ abierto: boolean; cargando: boolean; error: string | null; onConfirmar: (materiaId: number) => void; onCerrar: () => void }`. `MisMaterias.tsx` no se toca.

- [ ] **Step 1: Agregar el stub de `IntersectionObserver` al setup de tests**

Reemplazar el contenido completo de `frontend/src/test/setup.ts`:

```ts
import '@testing-library/jest-dom/vitest'

// jsdom no implementa IntersectionObserver y el scroll infinito del catálogo
// de materias lo construye dentro de un efecto. Stub no-op por defecto: los
// tests que necesitan disparar la intersección lo sobreescriben en su archivo.
class ObservadorInterseccionStub {
  readonly root: Element | null = null
  readonly rootMargin: string = ''
  readonly thresholds: readonly number[] = []
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

globalThis.IntersectionObserver =
  ObservadorInterseccionStub as unknown as typeof IntersectionObserver
```

- [ ] **Step 2: Escribir los tests que fallan (reescritura completa del archivo)**

Reemplazar el contenido completo de `frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { DialogoAgregarMateria } from './DialogoAgregarMateria'
import * as catalogo from '../../catalogo/api'
import type { Carrera, Materia, RespuestaPaginada } from '../../../api/types'

let disparaInterseccion: (() => void) | null = null

class ObservadorEspia {
  constructor(callback: IntersectionObserverCallback) {
    disparaInterseccion = () =>
      callback(
        [{ isIntersecting: true } as IntersectionObserverEntry],
        this as unknown as IntersectionObserver,
      )
  }
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

function crearMateria(overrides: Partial<Materia>): Materia {
  return {
    id: 1, clave: '0001', nombre: 'Cálculo I', carrera: 1, nivel: null,
    plan: 1, habilitada_asesorias: true, ...overrides,
  }
}

function crearCarrera(id: number, nombre: string): Carrera {
  return { id, clave: 800 + id, nombre, area: { id: 1, nombre: 'Área' }, acepta_nuevo_ingreso: true }
}

function pagina(results: Materia[], next: string | null): RespuestaPaginada<Materia> {
  return { count: results.length, next, previous: null, results }
}

interface OpcionesMontaje {
  paginas?: RespuestaPaginada<Materia>[]
  hasNextPage?: boolean
  isFetchingNextPage?: boolean
  carreras?: Carrera[]
}

function montar(opciones: OpcionesMontaje = {}) {
  const {
    paginas = [pagina([crearMateria({ id: 1, nombre: 'Cálculo I' })], null)],
    hasNextPage = false,
    isFetchingNextPage = false,
    carreras = [crearCarrera(1, 'Matemáticas'), crearCarrera(2, 'Física')],
  } = opciones

  disparaInterseccion = null
  globalThis.IntersectionObserver = ObservadorEspia as unknown as typeof IntersectionObserver

  const fetchNextPage = vi.fn()
  const usarInfinitas = vi.spyOn(catalogo, 'useMateriasInfinitas').mockReturnValue({
    data: { pages: paginas, pageParams: paginas.map((_, i) => i + 1) },
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } as unknown as ReturnType<typeof catalogo.useMateriasInfinitas>)
  vi.spyOn(catalogo, 'useCarreras').mockReturnValue({
    data: carreras,
  } as ReturnType<typeof catalogo.useCarreras>)

  const onConfirmar = vi.fn()
  render(
    <DialogoAgregarMateria abierto cargando={false} error={null} onConfirmar={onConfirmar} onCerrar={vi.fn()} />,
  )
  return { onConfirmar, fetchNextPage, usarInfinitas }
}

describe('DialogoAgregarMateria', () => {
  afterEach(() => {
    disparaInterseccion = null
    vi.restoreAllMocks()
  })

  it('pide al backend solo las materias habilitadas para asesorías', () => {
    const { usarInfinitas } = montar()

    expect(usarInfinitas).toHaveBeenCalledWith({
      habilitada_asesorias: true,
      carrera: null,
      search: '',
    })
  })

  it('lista las materias de todas las páginas cargadas', () => {
    montar({
      paginas: [
        pagina([crearMateria({ id: 1, nombre: 'Cálculo I' })], 'http://x/?page=2'),
        pagina([crearMateria({ id: 2, nombre: 'Física' })], null),
      ],
    })

    expect(screen.getByRole('button', { name: 'Cálculo I' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Física' })).toBeInTheDocument()
  })

  it('manda la búsqueda al backend con debounce, sin filtrar en cliente', async () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'fís' } })

    expect(usarInfinitas).not.toHaveBeenCalledWith(
      expect.objectContaining({ search: 'fís' }),
    )
    await waitFor(
      () =>
        expect(usarInfinitas).toHaveBeenCalledWith({
          habilitada_asesorias: true,
          carrera: null,
          search: 'fís',
        }),
      { timeout: 2000 },
    )
  })

  it('cambiar de carrera dispara la query con el filtro, sin esperar el debounce', () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '2' } })

    expect(usarInfinitas).toHaveBeenCalledWith({
      habilitada_asesorias: true,
      carrera: 2,
      search: '',
    })
  })

  it('combina carrera y búsqueda en la misma query', async () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'ondas' } })

    await waitFor(
      () =>
        expect(usarInfinitas).toHaveBeenCalledWith({
          habilitada_asesorias: true,
          carrera: 2,
          search: 'ondas',
        }),
      { timeout: 2000 },
    )
  })

  it('vuelve a Todas las carreras al elegir la opción vacía', () => {
    const { usarInfinitas } = montar()

    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Carrera'), { target: { value: '' } })

    expect(usarInfinitas).toHaveBeenLastCalledWith({
      habilitada_asesorias: true,
      carrera: null,
      search: '',
    })
  })

  it('puebla el selector con el catálogo completo de carreras', () => {
    montar()

    expect(screen.getByRole('option', { name: 'Todas' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Matemáticas' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Física' })).toBeInTheDocument()
  })

  it('al llegar el sentinela a la vista pide la siguiente página', () => {
    const { fetchNextPage } = montar({ hasNextPage: true })

    expect(disparaInterseccion).not.toBeNull()
    act(() => disparaInterseccion?.())

    expect(fetchNextPage).toHaveBeenCalled()
  })

  it('no observa nada cuando ya no hay más páginas', () => {
    montar({ hasNextPage: false })

    expect(disparaInterseccion).toBeNull()
  })

  it('avisa mientras carga la siguiente página', () => {
    montar({ hasNextPage: true, isFetchingNextPage: true })

    expect(screen.getByText('Cargando más…')).toBeInTheDocument()
  })

  it('mantiene Agregar deshabilitado hasta que hay una materia seleccionada', () => {
    const { onConfirmar } = montar({
      paginas: [pagina([crearMateria({ id: 7, nombre: 'Física' })], null)],
    })

    expect(screen.getByRole('button', { name: 'Agregar' })).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Física' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }))

    expect(onConfirmar).toHaveBeenCalledWith(7)
  })
})
```

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `cd frontend && npx vitest run src/features/asesorias/components/DialogoAgregarMateria.test.tsx`
Expected: FAIL — `useMateriasInfinitas` no está siendo llamado por el componente (todavía usa `useMaterias`), y `getByLabelText('Carrera')` no encuentra nada.

- [ ] **Step 4: Reescribir el componente**

Reemplazar el contenido completo de `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx`:

```tsx
import { useEffect, useMemo, useRef, useState } from 'react'

import { Dialogo } from '../../../components/ui/Dialogo'
import { useCarreras, useMateriasInfinitas } from '../../catalogo/api'

/** Evita una request por tecla mientras el asesor escribe. */
const RETRASO_BUSQUEDA_MS = 300

interface DialogoAgregarMateriaProps {
  abierto: boolean
  cargando: boolean
  error: string | null
  onConfirmar: (materiaId: number) => void
  onCerrar: () => void
}

export function DialogoAgregarMateria({
  abierto,
  cargando,
  error,
  onConfirmar,
  onCerrar,
}: DialogoAgregarMateriaProps) {
  const [busqueda, setBusqueda] = useState('')
  const [busquedaDiferida, setBusquedaDiferida] = useState('')
  const [carrera, setCarrera] = useState<number | null>(null)
  const [seleccionada, setSeleccionada] = useState<number | null>(null)
  const sentinelaRef = useRef<HTMLLIElement | null>(null)

  useEffect(() => {
    const temporizador = setTimeout(() => setBusquedaDiferida(busqueda), RETRASO_BUSQUEDA_MS)
    return () => clearTimeout(temporizador)
  }, [busqueda])

  // Catálogo completo de carreras, no derivado de las materias cargadas: con
  // scroll infinito el selector estaría incompleto hasta scrollear todo.
  const { data: carreras = [] } = useCarreras()

  // El filtro por texto y por carrera ya no corre en cliente: viaja al backend
  // como `search` y `carrera`, y ambos entran a la queryKey del hook.
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useMateriasInfinitas({
    habilitada_asesorias: true,
    carrera,
    search: busquedaDiferida,
  })

  const materias = useMemo(() => (data?.pages ?? []).flatMap((pagina) => pagina.results), [data])

  // El sentinela es el último `<li>` del contenedor con overflow: cuando entra
  // a la vista, se pide la página siguiente. Solo se monta si `hasNextPage`.
  useEffect(() => {
    const nodo = sentinelaRef.current
    if (nodo === null || !hasNextPage) return
    const observador = new IntersectionObserver((entradas) => {
      if (entradas[0]?.isIntersecting === true) void fetchNextPage()
    })
    observador.observe(nodo)
    return () => observador.disconnect()
  }, [hasNextPage, fetchNextPage, materias.length])

  return (
    <Dialogo
      abierto={abierto}
      titulo="Agregar materia"
      error={error}
      etiquetaSalir="Cancelar"
      onCerrar={onCerrar}
      acciones={[
        {
          etiqueta: 'Agregar',
          cargando,
          deshabilitada: seleccionada === null,
          onClick: () => seleccionada !== null && onConfirmar(seleccionada),
        },
      ]}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="carrera-materia" className="text-xs text-on-surface-variant">
            Carrera
          </label>
          <select
            id="carrera-materia"
            value={carrera ?? ''}
            onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
            className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          >
            <option value="">Todas</option>
            {carreras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="busqueda-materia" className="text-xs text-on-surface-variant">
            Buscar materia
          </label>
          <input
            id="busqueda-materia"
            type="text"
            placeholder="Escribe para filtrar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="foco-visible h-10 w-full rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          />
        </div>

        <ul className="max-h-48 overflow-y-auto">
          {materias.map((materia, indice) => (
            <li key={materia.id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
              <button
                type="button"
                onClick={() => setSeleccionada(materia.id)}
                aria-pressed={seleccionada === materia.id}
                className={`foco-visible min-h-11 w-full rounded-md px-2 py-2 text-left text-sm ${
                  seleccionada === materia.id
                    ? 'bg-primary-container text-on-primary-container'
                    : 'fila-interactiva text-on-surface'
                }`}
              >
                {materia.nombre}
              </button>
            </li>
          ))}
          {hasNextPage && (
            <li ref={sentinelaRef} className="py-3 text-center text-xs text-on-surface-variant">
              {isFetchingNextPage ? 'Cargando más…' : ''}
            </li>
          )}
        </ul>
      </div>
    </Dialogo>
  )
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `cd frontend && npx vitest run src/features/asesorias/components/DialogoAgregarMateria.test.tsx`
Expected: PASS — 11 tests.

- [ ] **Step 6: Correr la suite completa, build y lint**

Run: `cd frontend && npm test && npm run build && npm run lint`
Expected: PASS. `MisMaterias.test.tsx` monta el diálogo cerrado: Radix no renderiza sus hijos, el sentinela nunca existe y no se construye ningún `IntersectionObserver`.

- [ ] **Step 7: Commit**

```bash
cd /home/hyfi/Development/atenea-fc && git add frontend/src/test/setup.ts frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx && git commit -s -m "$(cat <<'EOF'
[feat][frontend] scroll infinito, busqueda en backend y filtro de carrera al agregar materia

- reemplazar el .filter() en cliente por useMateriasInfinitas con search
  (debounce de 300ms) y carrera en la queryKey
- agregar el selector de carrera poblado con useCarreras (catalogo completo,
  no derivado de las materias ya cargadas), con el mismo layout que
  OfertaAsesorias
- cargar la pagina siguiente con IntersectionObserver sobre un <li> sentinela
  al fondo del contenedor con overflow, montado solo si hasNextPage
- stubear IntersectionObserver en el setup de vitest, que jsdom no implementa
- reescribir los tests del dialogo: paginas concatenadas, debounce, carrera,
  combinacion carrera+busqueda y disparo del sentinela
EOF
)"
```

---

## Task 5: Documentación — ADR 0029 y deuda técnica

**Files:**
- Create: `docs/decisions/0029-paginacion-busqueda-catalogo-materias.md`
- Create: `docs/technical-debt/0022-useMaterias-recorre-todas-las-paginas.md`
- Modify: `docs/technical-debt/0006-sin-paginacion-listados.md`
- Modify: `docs/technical-debt/README.md:27` (agregar 0022 al final de la lista "Activa")

**Interfaces:**
- Consumes: todo lo implementado en Tasks 1-4. No produce código.

- [ ] **Step 1: Crear el ADR**

Crear `docs/decisions/0029-paginacion-busqueda-catalogo-materias.md`:

```markdown
# 0029 — Paginación y búsqueda del catálogo de materias

**Status:** Accepted
**Date:** 2026-08-19

## Context

`GET /api/materias/materias/` devolvía el catálogo completo (400+ registros) en una sola respuesta, sin paginación y sin búsqueda por texto: `DialogoAgregarMateria` traía todo el array y filtraba en cliente con `.filter()`. Es el caso con volumen real del proyecto y la razón por la que la [deuda 0006](../technical-debt/0006-sin-paginacion-listados.md) sigue activa.

No había convención previa: `REST_FRAMEWORK` en `config/settings/base.py` nunca definió `DEFAULT_PAGINATION_CLASS`, y ningún viewset del proyecto declaraba `pagination_class`. Tampoco existía en el frontend ningún uso de `useInfiniteQuery`, `fetchNextPage` ni `IntersectionObserver`.

El resto de los listados (`RegistroAsesor`, `Disponibilidad`, `Asesoria`, `carreras`) no está en alcance de este sprint y no fue revisado.

## Decision

**Paginación acotada al viewset, no global.** `PaginacionMaterias(PageNumberPagination)` con `page_size = 50` vive en `materias/pagination.py` y se declara como `pagination_class` de `MateriaViewSet`. `REST_FRAMEWORK` queda intacto: agregar `DEFAULT_PAGINATION_CLASS` cambiaría el contrato de todos los listados del proyecto sin haberlos revisado ni testeado.

50 por página es el balance entre pocos round-trips para el consumidor que necesita el catálogo entero y primer render rápido en el scroll infinito. `Materia.Meta.ordering = ["nombre"]` ya garantiza un orden determinista, requisito de cualquier paginación por offset.

**La búsqueda se mueve al backend.** `filter_backends = [SearchFilter]` con `search_fields = ["nombre", "clave"]` (`icontains`, OR entre campos), combinable con los filtros `carrera` y `habilitada_asesorias` que ya resolvía `get_queryset`. Sin esto, paginar rompería silenciosamente el filtro en cliente: dejaría de ver el catálogo completo.

**Dos modos de fetching sobre el mismo endpoint, en el frontend:**

- `useMaterias()` conserva su firma (`Materia[]`) recorriendo todas las páginas dentro de `obtenerTodasLasMaterias()` hasta `next === null`. Los 6 consumidores de lookup (`useMapaMaterias` en `DetalleAsesoria`, `AgendarAsesoria`, `Asesorias`, `MisMaterias`, `AdminOfertaMateria`, `AdminAsesorias`) no listan para el usuario: resuelven nombre por id y necesitan el catálogo entero en memoria. El costo de N requests queda registrado como [deuda 0022](../technical-debt/0022-useMaterias-recorre-todas-las-paginas.md).
- `useMateriasInfinitas(params)` con `useInfiniteQuery` es el modo de listar+buscar, usado únicamente por `DialogoAgregarMateria`. `carrera`, `search` y `habilitada_asesorias` entran a la `queryKey`, así que cambiar cualquiera reinicia la paginación desde la página 1 sin código extra.

`apiGet` **no** se generaliza a un cliente consciente de paginación: el constructor de rutas y el envelope se manejan en `features/catalogo/api.ts`. Materias es hoy el único endpoint paginado; generalizar antes del segundo es prematuro.

`DialogoAgregarMateria` suma un `<select>` de carrera poblado con `useCarreras()` — el catálogo completo de carreras, no las carreras de las materias ya cargadas, que con scroll infinito estaría incompleto hasta scrollear todo.

## Consequences

- La respuesta de listado de materias es un **breaking change**: `{count, next, previous, results}` en vez de `Materia[]`. Todo consumidor nuevo debe leer `results`. El detalle (`/{id}/`) no cambia.
- El scroll infinito introduce el primer `IntersectionObserver` del proyecto; jsdom no lo implementa, así que `frontend/src/test/setup.ts` lleva un stub no-op y los tests que necesitan disparar la intersección lo sobreescriben en su archivo.
- La búsqueda deja de ser instantánea: cuesta un round-trip con 300ms de debounce, y a cambio busca sobre el catálogo completo (antes solo sobre lo que hubiera en memoria) y también por `clave`.
- Cargar el catálogo entero pasa de 1 request a 8 (400 materias / 50). Ver deuda 0022.
- La deuda 0006 **no se cierra**: sigue sin haber convención de paginación de proyecto y el resto de los listados sigue devolviendo la colección completa.

## Alternatives considered

- **`DEFAULT_PAGINATION_CLASS` global.** Fija la convención de una vez, que es justamente lo que pide la señal de revisión de la deuda 0006. Se descarta para este sprint: cambiaría el contrato de `asesorias`, `carreras` y `academico` sin revisar sus consumidores, y el pedido era acotado a materias. Queda como el camino natural cuando se ataque la deuda 0006 completa.
- **Endpoint aparte sin paginar para el caso de lookup.** Evitaría los N requests de `useMaterias()`. Se descarta: agrega superficie de API para un problema de rendimiento que todavía no se midió, y `staleTime: Infinity` hace que el costo se pague una sola vez por sesión. Registrado como deuda 0022 con su señal de revisión.
- **Exponer `page_size` como query param** para que el lookup pida una página gigante y el diálogo una chica. Se descarta por la misma razón: resuelve un costo no medido y deja al cliente decidir el tamaño de página, que es exactamente lo que la paginación existe para acotar.
- **Dejar la búsqueda en cliente sobre las páginas ya cargadas.** Cero cambios de backend. Se descarta porque rompe silenciosamente: el usuario buscaría solo dentro de lo que alcanzó a scrollear, sin ninguna señal de que el resto del catálogo existe.
- **Botón "cargar más" en vez de scroll infinito.** Más simple y sin `IntersectionObserver`. Se descarta porque el pedido explícito fue scroll infinito.
```

- [ ] **Step 2: Crear la deuda 0022**

Crear `docs/technical-debt/0022-useMaterias-recorre-todas-las-paginas.md`:

```markdown
# 0022 — `useMaterias()` recorre todas las páginas: N requests por carga del catálogo

**Estado:** Activa
**Origen:** [ADR 0029](../decisions/0029-paginacion-busqueda-catalogo-materias.md)

## Qué se simplificó

Al paginar `GET /api/materias/materias/` (50 por página), `useMaterias()` conservó su contrato de devolver `Materia[]` completo recorriendo todas las páginas dentro de `obtenerTodasLasMaterias()` (`frontend/src/features/catalogo/api.ts`): pide `?page=1`, `?page=2`, … hasta que `next` es `null`, en serie. Con 400+ materias son 8 requests secuenciales en vez de 1.

## Por qué era razonable

Los 6 consumidores de `useMapaMaterias()` (`DetalleAsesoria`, `AgendarAsesoria`, `Asesorias`, `MisMaterias`, `AdminOfertaMateria`, `AdminAsesorias`) no listan materias para el usuario: resuelven nombre por id y asumen el catálogo entero disponible sincrónicamente. Migrarlos a paginado los rompería sin ningún beneficio para el usuario, y estaba fuera del alcance del sprint. El costo se paga una sola vez por sesión (`staleTime: Infinity`) y todavía no se midió en producción.

## Señal de revisión

Cualquiera de estas tres: (a) el catálogo crece lo suficiente para que la cascada de requests sea perceptible en la primera pantalla que monte `useMapaMaterias()`; (b) se ataca la deuda [0006](0006-sin-paginacion-listados.md) completa y se fija una convención de paginación de proyecto — ahí se decide de una vez cómo se sirve el caso lookup; (c) aparece un segundo consumidor que necesita el catálogo completo bajo una latencia peor (móvil, red institucional).
```

- [ ] **Step 3: Registrar la cobertura parcial en la deuda 0006**

En `docs/technical-debt/0006-sin-paginacion-listados.md`, agregar al final del archivo (después de la sección `## Cobertura parcial (2026-08-04)`):

```markdown
## Cobertura parcial (2026-08-19)

`GET /api/materias/materias/` quedó paginado (`PageNumberPagination`, 50 por página) y con búsqueda por texto en el backend (`SearchFilter` sobre `nombre`/`clave`), con scroll infinito en `DialogoAgregarMateria` — ver [ADR 0029](../decisions/0029-paginacion-busqueda-catalogo-materias.md). Es el listado con volumen real del proyecto (400+ registros) y el único que se navega como lista.

**Esto no resuelve este ítem.** La paginación es `pagination_class` propia de `MateriaViewSet`: `REST_FRAMEWORK` en `config/settings/base.py` sigue **sin** `DEFAULT_PAGINATION_CLASS`, y `RegistroAsesor`, `Disponibilidad`, `Asesoria` y `carreras` siguen devolviendo la colección completa. La señal de revisión sigue vigente tal cual: falta la convención de proyecto, decidida una vez y no ad-hoc por app.

Además, la forma en que se preservó el contrato del caso lookup (`useMaterias()` recorre todas las páginas) abrió la deuda [0022](0022-useMaterias-recorre-todas-las-paginas.md).
```

- [ ] **Step 4: Agregar 0022 al índice**

En `docs/technical-debt/README.md`, insertar después de la línea 27 (`- [0021 — Envío de correo depende de una cuenta de Workspace dedicada y su app password](0021-smtp-cuenta-dedicada-app-password.md)`), como último ítem de la sección `### Activa`:

```markdown
- [0022 — `useMaterias()` recorre todas las páginas: N requests por carga del catálogo](0022-useMaterias-recorre-todas-las-paginas.md)
```

- [ ] **Step 5: Verificar que los enlaces relativos resuelven**

Run: `cd /home/hyfi/Development/atenea-fc && ls docs/decisions/0029-paginacion-busqueda-catalogo-materias.md docs/technical-debt/0022-useMaterias-recorre-todas-las-paginas.md && grep -c "0022" docs/technical-debt/README.md docs/technical-debt/0006-sin-paginacion-listados.md`
Expected: los dos archivos existen; `README.md:1` y `0006-...md:1`.

- [ ] **Step 6: Commit**

```bash
cd /home/hyfi/Development/atenea-fc && git add docs/decisions/0029-paginacion-busqueda-catalogo-materias.md docs/technical-debt/0022-useMaterias-recorre-todas-las-paginas.md docs/technical-debt/0006-sin-paginacion-listados.md docs/technical-debt/README.md && git commit -s -m "$(cat <<'EOF'
[docs] registrar ADR 0029 y la deuda 0022 de la paginacion de materias

- ADR 0029: pagination_class propia del viewset en vez de global, busqueda
  movida al backend, y los dos modos de fetching del frontend
- deuda 0022: useMaterias recorre todas las paginas, 8 requests por carga
- deuda 0006: cobertura parcial 2026-08-19, sigue Activa por falta de
  convencion de proyecto
- alta de 0022 en el indice de deuda tecnica
EOF
)"
```

---

## Verificación final

- [ ] **Step 1: Suite completa de backend**

Run: `cd backend && uv run manage.py test -v 1`
Expected: PASS.

- [ ] **Step 2: Suite completa, build y lint de frontend**

Run: `cd frontend && npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 3: Verificar que no se tocó la configuración global de DRF**

Run: `cd /home/hyfi/Development/atenea-fc && grep -c "DEFAULT_PAGINATION_CLASS" backend/config/settings/base.py`
Expected: `0`.

- [ ] **Step 4: Verificar el árbol limpio**

Run: `cd /home/hyfi/Development/atenea-fc && git status --short`
Expected: sin salida.
