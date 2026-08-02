# Flujo de Asesorías Académicas — Vista de Asesor (Frontend) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir en el frontend (React + TS + Vite) el flujo completo del asesor académico — registrar disponibilidad semanal, ver sesiones agendadas/histórico, y gestionar el ciclo de vida de una asesoría (cancelar, marcar asistencia, notas) — sobre una base de autenticación real que hoy no existe.

**Architecture:** SPA de una sola página con `react-router-dom`, estado de servidor manejado con TanStack Query (caché + `isPending`/`isError` por request, que alimenta directamente las animaciones de carga pedidas), un `AuthContext` propio para sesión (JWT body+localStorage en dev, cookies httpOnly en prod, mismo código para ambos gracias a `credentials:'include'` uniforme), y diálogos accesibles con Radix UI primitives sin adoptar una librería de componentes completa (mantiene la decisión de ADR-0014 de UI hecha a mano con Tailwind).

**Tech Stack:** React 19, TypeScript, Vite, Tailwind v4 (tokens M3 existentes), react-router-dom v7, @tanstack/react-query, @radix-ui/react-dialog, @radix-ui/react-tabs, Vitest + React Testing Library (nuevo, el frontend no tenía test runner).

## Global Constraints

- Sin paginación en ningún endpoint del backend — todo `list` es un array plano; no diseñar para `{results, count, next}` (deuda técnica 0006).
- Formato de commit `[type][scope] resumen` + lista de cambios + `Signed-off-by`, commits atómicos (ADR 0007). Scope `frontend` salvo los archivos de `docs/`.
- Copy de UI en español, coherente con las pantallas existentes (`Login.tsx`, `Home.tsx`).
- No agregar una librería de componentes completa ni un framework de animación (Framer Motion, GSAP) — solo Radix UI *primitives* (headless, sin estilos) para accesibilidad de diálogos/tabs, y CSS puro para motion. Ver sección "Decisiones de diseño".
- Todo endpoint de `asesorias`/`carreras`/`materias` requiere sesión autenticada; ninguno de estos requests debe ejecutarse antes de que `AuthContext` confirme `status === 'authenticated'`.
- Respetar `prefers-reduced-motion` en toda animación nueva.
- No implementar protección CSRF adicional en `api/client.ts` — deuda técnica 0009 ya aceptada, fuera de alcance de este plan.

---

## Contexto

### Por qué este plan

El backend de asesorías académicas está completo (ADR-0016 modelos, ADR-0017 API DRF) y probado end-to-end, incluida la implementación de cookies httpOnly en producción (ADR-0018, cerrado 2026-08-01). El frontend, en cambio, es un scaffold: `Login.tsx` navega directo a `/home` sin llamar a la API, `api/client.ts` solo tiene un `apiGet` sin manejo de auth, y no existe ni una sola pantalla, hook o componente relacionado con asesorías. Se decidió (ver Decisiones de alcance) construir primero el flujo de **asesor** — registro de disponibilidad semanal y gestión del ciclo de vida de sus sesiones — dejando búsqueda/booking de alumno y los tableros de solo-lectura de administración para fases posteriores, cada una con su propio spec y plan.

Como el flujo de asesor requiere sesión autenticada y no hay ninguna pantalla protegida hoy, este plan incluye como prerequisito construir el wiring real de autenticación (Google OAuth vía GIS, login por email/contraseña, cliente HTTP con `POST`/`PATCH`/`DELETE`, refresh silencioso, rutas protegidas) — decisión explícita del usuario en brainstorming, en vez de asumir que existe en otro plan.

### Decisiones de alcance (brainstorming)

1. **Fase 1 (este plan, a detalle):** vista de asesor — registrar disponibilidad del semestre, ver asesorías (próximas/historial), detalle con notas de sesiones previas del mismo alumno, cancelar/marcar asistencia/notas.
2. **Fase 2 (fuera de este plan):** vista de alumno — buscar asesorías por materia, ver asesores/disponibilidad disponibles, agendar.
3. **Fase 3 (fuera de este plan):** vista de administración — lista de asesores por semestre (solo lectura de su disponibilidad y asesorías), lista de alumnos que han solicitado asesorías por semestre.

### Gaps de API descubiertos (documentados como deuda técnica, no resueltos en este plan)

Durante la exploración se confirmaron dos vacíos de contrato que **no se resuelven aquí** por decisión explícita del usuario ("backend aparte, documéntalo como deuda técnica"):

1. **`AsesoriaSerializer` solo expone IDs planos** (`alumno`, `materia`, `carrera`, `disponibilidad`), sin nombre. `materia`/`carrera` se resuelven en el frontend contra los catálogos de solo lectura ya existentes (`/api/materias/materias/`, `/api/carreras/carreras/`) — sin costo extra, ya se cargan para otros fines. **`alumno` no tiene ninguna vía de resolución**: no existe endpoint que exponga `PerfilAlumno.user.first_name` a un tercero (el asesor). La UI de este plan muestra `"Alumno #<id>"` como placeholder.
2. **`/api/auth/user/` no expone qué perfil (rol) tiene el usuario autenticado.** No hay forma de saber "este usuario es asesor" sin sondear un endpoint exclusivo de asesor y leer el código de estado. Este plan implementa ese sondeo como solución interina (Task 5).

Ambos comparten causa raíz (la API no expone información de perfil más allá de lo que el propio dueño del perfil puede ver de sí mismo vía `/api/auth/user/`). Task 1 de este plan escribe el ítem de deuda técnica correspondiente, **referenciado explícitamente en qué tareas dependen de él** para que sea buscable antes de que el costo del workaround se vuelva indispensable de resolver (cuando se construya la Fase 3, el sondeo por-rol no escala a "admin ve todos los roles").

Hay un tercer gap, más chico, encontrado al leer `backend/asesorias/serializers.py` directamente: `AsesoriaSerializer.Meta.fields` tampoco incluye `motivo_cancelacion` ni `cancelado_por`, aunque ambos existen en el modelo `Asesoria` y se llenan en `cancelar()`. A diferencia de los otros dos gaps, este no es "falta un endpoint de un tercero" — es simplemente que el serializer no expone dos campos del propio objeto que el asesor ya puede ver. Se documenta en el mismo ítem de deuda técnica (Task 1) y la Task 13 diseña el panel de "cancelada" sin depender de `motivo_cancelacion`, ya que el campo nunca llega al frontend con el contrato actual.

### Decisiones de arquitectura (brainstorming)

| Decisión | Elegida | Alternativa descartada | Por qué |
|---|---|---|---|
| Estado de servidor | TanStack Query | Hooks manuales (`useState`+`useEffect` por pantalla) | Da `isPending`/`isFetching`/`isError` gratis por request — exactamente lo que pide el usuario para animaciones de carga — y invalidación de caché declarativa tras cada mutación, sin repetir lógica en 6+ pantallas. |
| Animación | CSS puro (`@keyframes`, transiciones Tailwind) | Framer Motion / GSAP | Coherente con la filosofía "sin librería" ya fijada en ADR-0014; las animaciones pedidas son sutiles (skeleton, spinner de botón, pulso de éxito), no coreografía compleja — no justifica una dependencia nueva. |
| Diálogos/confirmaciones | Radix UI primitives (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`) | Modal propio a mano | Focus trap, `Escape`, ARIA ya resueltos — evitar implementar accesibilidad de teclado a mano en el diálogo de cancelación (acción destructiva) y el de notas. |
| Detección de rol tras login | Sondeo a `GET /api/asesorias/registros/` (200→asesor, 403→no) | Endpoint dedicado de perfil | El endpoint no existe (ver gap #2); sondear un endpoint ya exclusivo de asesor es la única vía sin tocar backend. Documentado como deuda técnica. |
| UI de disponibilidad semanal | Grilla visual (filas=hora, columnas=día, clic en celda) | Lista agrupada por día | Más intuitiva para planear un horario recurrente; mejor terreno para el feedback de acción pedido (pulso al crear, fade-out al eliminar). |
| Rango horario de la grilla | 07:00–21:00 en bloques de 30 min (28 filas) | Rango dinámico/configurable | El modelo `Disponibilidad` no impone límites de hora — este es un recorte de UI, no del backend. Documentado aquí para que quede explícito, no oculto en el código. |
| Estructura de carpetas | Nueva carpeta `features/asesorias/` (api/lógica/pantallas/componentes) junto al `screens/` plano existente | Seguir metiendo todo en `screens/` | El dominio de asesorías tiene 3 pantallas + hooks + componentes propios; `screens/` plano no escala para eso. `screens/` existente no se toca salvo `Login.tsx`. |

---

## Estructura de archivos

```
frontend/src/
  api/
    client.ts            # MODIFICAR: apiGet existente + apiPost/apiPatch/apiDelete, auth, refresh
    types.ts              # NUEVO: tipos compartidos de la API (AuthUser, Materia, Asesoria, ...)
    health.ts              # sin cambios
  auth/
    AuthContext.tsx        # NUEVO: proveedor de sesión, loginWithPassword/loginWithGoogle/logout
    google.ts               # NUEVO: loader de Google Identity Services (GIS)
    RutaProtegida.tsx        # NUEVO: RutaDeAsesor (guard de ruta por rol)
  features/
    catalogo/
      api.ts                # NUEVO: useMaterias/useCarreras/useMapaMaterias/useMapaCarreras
    asesorias/
      api.ts                 # NUEVO: hooks de RegistroAsesor/Disponibilidad/Asesoria
      logica.ts               # NUEVO: funciones puras (filtros, gating de acciones, fechas)
      logica.test.ts           # NUEVO
      screens/
        SesionesAsesor.tsx      # NUEVO: lista con tabs Próximas/Historial
        DetalleAsesoria.tsx      # NUEVO: detalle + historial de notas + acciones
        DisponibilidadAsesor.tsx  # NUEVO: registro de semestre + grilla semanal
      components/
        TarjetaAsesoria.tsx       # NUEVO
        GrillaDisponibilidad.tsx   # NUEVO
        DialogoCancelar.tsx         # NUEVO
        DialogoNuevoBloque.tsx       # NUEVO
        DialogoAgregarMateria.tsx     # NUEVO
  components/ui/
    Skeleton.tsx             # NUEVO
    InsigniaEstado.tsx        # NUEVO
    Boton.tsx                  # NUEVO: botón con spinner integrado
    Retroalimentacion.tsx       # NUEVO: banner de éxito/error post-mutación
  screens/
    Login.tsx                 # MODIFICAR: wiring real de auth
  test/
    setup.ts                   # NUEVO: setup de Vitest + jest-dom
  App.tsx                      # MODIFICAR: rutas nuevas + providers
  main.tsx                      # MODIFICAR: QueryClientProvider + AuthProvider
  index.css                      # MODIFICAR: keyframes de motion

frontend/
  vite.config.ts                  # MODIFICAR: bloque `test` de Vitest
  package.json                     # MODIFICAR: nuevas dependencias
  .env.example                      # MODIFICAR: VITE_GOOGLE_OAUTH_CLIENT_ID

docs/
  superpowers/specs/2026-08-01-asesorias-frontend-asesor-design.md   # NUEVO (Task 1)
  superpowers/plans/2026-08-01-asesorias-frontend-asesor.md           # NUEVO (Task 1, copia de este plan)
  technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md      # NUEVO (Task 1)
```

---

## Task 1: Documentar spec, plan y deuda técnica

Formaliza en el repositorio las decisiones tomadas en brainstorming antes de tocar código, siguiendo las convenciones de `CLAUDE.md`.

**Files:**
- Create: `docs/superpowers/specs/2026-08-01-asesorias-frontend-asesor-design.md`
- Create: `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md`
- Create: `docs/superpowers/plans/2026-08-01-asesorias-frontend-asesor.md`

**Interfaces:**
- Produces: nada que otras tareas consuman en código; es documentación de referencia.

- [ ] **Step 1: Crear el ítem de deuda técnica**

```markdown
# 0010 — API no expone perfil ni rol del usuario autenticado

**Estado:** Activa
**Origen:** [ADR 0017](../decisions/0017-asesorias-academicas-api.md), [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md)

## Qué se simplificó

`GET /api/auth/user/` devuelve únicamente `{pk, email, first_name}` — no indica
qué perfil de negocio (`PerfilAlumno`, `PerfilAsesorAcademico`, `PerfilAcademico`)
tiene el usuario autenticado. Tampoco existe ningún endpoint donde un usuario
pueda resolver el nombre de **otro** usuario a partir del id de su perfil:
`AsesoriaSerializer` expone `alumno` como un id plano (`PerfilAlumno.id`), y no
hay ruta para que un asesor consulte el nombre asociado a ese id.

El frontend de la Fase 1 (asesorías — vista de asesor) resuelve esto con dos
workarounds:

1. **Detección de rol tras login:** sondea `GET /api/asesorias/registros/`
   (exclusivo de `EsAsesorAcademico`) y usa el código de estado (200 vs 403)
   para decidir si el usuario es asesor. No escala a más de un rol sin agregar
   una llamada de sondeo por cada rol a verificar.
2. **Nombre de alumno en la UI:** se muestra `"Alumno #<id>"` en vez de un
   nombre, en la lista y detalle de asesorías del asesor.

Un tercer campo relacionado, encontrado en `backend/asesorias/serializers.py`:
`AsesoriaSerializer.Meta.fields` no incluye `motivo_cancelacion` ni
`cancelado_por`, aunque el modelo `Asesoria` sí los tiene y `cancelar()` los
llena. El panel de "asesoría cancelada" en el detalle del asesor no puede
mostrar el motivo por esta razón — muestra solo el estado, sin motivo, hasta
que se agreguen esos dos campos al serializer.

## Por qué era razonable

Agregar campos de perfil/rol al serializer de `User` o de `Asesoria` es un
cambio de backend pequeño pero con superficie propia (qué campos exponer, a
quién, si expandir `alumno` a un objeto rompe compatibilidad con lo que ya
consume el body de creación) — se decidió tratarlo como su propio cambio de
backend en vez de mezclarlo dentro del plan de frontend que lo necesita.

## Señal de revisión

- Antes de construir la **Fase 2** (vista de alumno): si el alumno también
  necesita ver el nombre de su asesor, el mismo gap se repite en el otro
  sentido — dos parches iguales es la señal de que ya no es aceptable
  posponerlo.
- Antes de construir la **Fase 3** (vista de administración): el patrón de
  "sondear un endpoint por rol" no funciona para un panel que necesita listar
  *todos* los roles de *todos* los usuarios — en ese punto el sondeo deja de
  ser viable y este ítem se vuelve bloqueante, no solo incómodo.
- Si un asesor pide ver el motivo de una cancelación hecha por el alumno: la
  señal de que `motivo_cancelacion`/`cancelado_por` ya no pueden seguir fuera
  del serializer.
```

- [ ] **Step 2: Crear el spec de diseño**

Contenido: copiar las secciones "Contexto", "Decisiones de alcance", "Gaps de
API descubiertos" y "Decisiones de arquitectura" de este mismo documento
(arriba), más la sección "Pantallas y flujos" que se detalla en las Tasks 9,
11 y 12 más abajo (screens `DisponibilidadAsesor`, `SesionesAsesor`,
`DetalleAsesoria`) y la sección "Sistema de motion" de la Task 7. Es el mismo
contenido, reformateado como spec independiente para que quede indexado junto
al resto de `docs/superpowers/specs/`.

- [ ] **Step 3: Copiar este plan a `docs/superpowers/plans/`**

Guardar el contenido completo de este archivo de plan en
`docs/superpowers/plans/2026-08-01-asesorias-frontend-asesor.md`, siguiendo la
convención de ubicación de `superpowers:writing-plans`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-08-01-asesorias-frontend-asesor-design.md \
        docs/superpowers/plans/2026-08-01-asesorias-frontend-asesor.md \
        docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md
git commit -s -m "[docs] agregar spec, plan y deuda técnica del flujo de asesor" \
  -m "- Spec de diseño del flujo de asesorías académicas (vista de asesor)" \
  -m "- Plan de implementación (auth real + disponibilidad + sesiones + estados)" \
  -m "- Deuda técnica 0010: API no expone perfil/rol del usuario autenticado"
```

---

## Task 2: Cliente HTTP con auth, mutaciones y refresh

**Files:**
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`
- Test: `frontend/src/api/client.test.ts`

**Interfaces:**
- Produces: `apiGet<T>(path)`, `apiPost<T>(path, data?)`, `apiPatch<T>(path, data)`, `apiDelete(path)`, `ApiError` (con `status: number`, `body: unknown`). Todas las tasks siguientes que llamen a la API usan estas cuatro funciones.

- [ ] **Step 1: Escribir tipos compartidos**

```typescript
// frontend/src/api/types.ts
export interface AuthUser {
  pk: number
  email: string
  first_name: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: AuthUser
}

export interface Materia {
  id: number
  clave: string
  nombre: string
  carrera: number
  nivel: string | null
  plan: number
  habilitada_asesorias: boolean
}

export interface Carrera {
  id: number
  clave: number
  nombre: string
  area: { id: number; nombre: string }
  acepta_nuevo_ingreso: boolean
}

export interface RegistroAsesor {
  id: number
  semestre: string
  materias: number[]
}

export type FormatoAsesoria = 'presencial' | 'virtual'
export type EstadoAsesoria = 'agendada' | 'cancelada' | 'realizada'

export interface Disponibilidad {
  id: number
  registro: number
  dia_semana: number
  hora_inicio: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  activa: boolean
}

export interface Asesoria {
  id: number
  alumno: number
  disponibilidad: number
  materia: number
  carrera: number
  fecha: string
  hora_inicio: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  estado: EstadoAsesoria
  asistio: boolean | null
  notas: string
  creado_en: string
}
```

- [ ] **Step 2: Escribir el test que falla**

```typescript
// frontend/src/api/client.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiGet, apiPost, ApiError } from './client'

const originalFetch = global.fetch

describe('apiGet', () => {
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('lanza ApiError con status y body cuando la respuesta no es ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'No puedes operar sobre una sesión ajena.' }),
    } as Response)

    await expect(apiGet('/api/asesorias/asesorias/1/')).rejects.toMatchObject({
      status: 403,
      body: { detail: 'No puedes operar sobre una sesión ajena.' },
    })
  })

  it('devuelve el JSON parseado cuando la respuesta es ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: 1 }),
    } as Response)

    await expect(apiGet<{ id: number }>('/api/materias/materias/1/')).resolves.toEqual({ id: 1 })
  })
})

describe('apiPost', () => {
  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('manda el body como JSON con Content-Type', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    } as Response)
    global.fetch = fetchMock

    await apiPost('/api/asesorias/asesorias/1/cancelar/', { motivo: 'ya no puedo' })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ motivo: 'ya no puedo' }))
    expect(init.credentials).toBe('include')
  })
})
```

- [ ] **Step 3: Correr el test y confirmar que falla**

Run: `cd frontend && npx vitest run src/api/client.test.ts`
Expected: FAIL — `apiPost`/`ApiError` no existen todavía en `client.ts`.

- [ ] **Step 4: Reescribir `client.ts`**

```typescript
// frontend/src/api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export const CLAVE_ACCESS = 'atenea_access'
export const CLAVE_REFRESH = 'atenea_refresh'

export class ApiError extends Error {
  status: number
  body: unknown
  constructor(status: number, body: unknown) {
    super(`API error ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function tokenDeAcceso(): string | null {
  return import.meta.env.PROD ? null : localStorage.getItem(CLAVE_ACCESS)
}

async function refrescarToken(): Promise<boolean> {
  const body = import.meta.env.PROD ? {} : { refresh: localStorage.getItem(CLAVE_REFRESH) }
  const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  if (!response.ok) return false
  if (!import.meta.env.PROD) {
    const data = (await response.json()) as { access: string }
    localStorage.setItem(CLAVE_ACCESS, data.access)
  }
  return true
}

async function solicitar<T>(path: string, init: RequestInit = {}, permitirReintento = true): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  const token = tokenDeAcceso()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  })

  if (response.status === 401 && permitirReintento) {
    const seRefresco = await refrescarToken()
    if (seRefresco) return solicitar<T>(path, init, false)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, body)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return solicitar<T>(path, { method: 'GET' })
}

export function apiPost<T>(path: string, data?: unknown): Promise<T> {
  return solicitar<T>(path, {
    method: 'POST',
    body: data !== undefined ? JSON.stringify(data) : undefined,
  })
}

export function apiPatch<T>(path: string, data: unknown): Promise<T> {
  return solicitar<T>(path, { method: 'PATCH', body: JSON.stringify(data) })
}

export function apiDelete(path: string): Promise<void> {
  return solicitar<void>(path, { method: 'DELETE' })
}
```

- [ ] **Step 5: Correr el test y confirmar que pasa**

Run: `cd frontend && npx vitest run src/api/client.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/api/types.ts
git commit -s -m "[feat][frontend] extender cliente HTTP con POST/PATCH/DELETE y refresh" \
  -m "- apiPost/apiPatch/apiDelete junto al apiGet existente" \
  -m "- ApiError tipado (status + body) para que las pantallas distingan 400/403/409" \
  -m "- Refresh silencioso ante 401, uniforme para dev (body) y prod (cookie)"
```

---

## Task 3: Dependencias, TanStack Query y Vitest

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/test/setup.ts`

**Interfaces:**
- Consumes: nada nuevo.
- Produces: `QueryClientProvider` envolviendo `<App />`, config de Vitest lista para que las tasks siguientes agreguen `*.test.ts(x)`.

- [ ] **Step 1: Instalar dependencias**

```bash
cd frontend
pnpm add @tanstack/react-query @radix-ui/react-dialog @radix-ui/react-tabs
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

- [ ] **Step 2: Configurar Vitest en `vite.config.ts`**

```typescript
// frontend/vite.config.ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

- [ ] **Step 3: Crear el setup de Vitest**

```typescript
// frontend/src/test/setup.ts
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 4: Agregar script `test` a `package.json`**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "oxlint",
    "preview": "vite preview",
    "test": "vitest run"
  }
}
```

- [ ] **Step 5: Envolver la app con `QueryClientProvider`**

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
```

- [ ] **Step 6: Verificar que todo sigue arrancando**

Run: `cd frontend && pnpm build`
Expected: build sin errores de TypeScript.

Run: `cd frontend && npx vitest run`
Expected: PASS (los tests de `client.test.ts` de la Task 2 siguen pasando bajo la config nueva).

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml frontend/vite.config.ts frontend/src/main.tsx frontend/src/test/setup.ts
git commit -s -m "[chore][frontend] agregar TanStack Query, Radix UI y Vitest" \
  -m "- QueryClientProvider envolviendo la app para estado de servidor" \
  -m "- Vitest + React Testing Library: el frontend no tenía test runner" \
  -m "- Radix UI (dialog, tabs) para accesibilidad de diálogos sin adoptar una librería de componentes"
```

---

## Task 4: `AuthContext` — sesión, login y Google OAuth

**Files:**
- Create: `frontend/src/auth/AuthContext.tsx`
- Create: `frontend/src/auth/google.ts`
- Test: `frontend/src/auth/AuthContext.test.tsx`
- Modify: `frontend/.env.example`

**Interfaces:**
- Consumes: `apiGet`, `apiPost`, `ApiError` de Task 2; `AuthUser`, `LoginResponse` de `api/types.ts`.
- Produces: `AuthProvider`, `useAuth()` devolviendo `{ user: AuthUser | null, status: 'loading' | 'authenticated' | 'unauthenticated', loginWithPassword, loginWithGoogle, logout }`. Task 5 y Task 6 consumen `useAuth()`.

- [ ] **Step 1: Agregar la variable de entorno faltante**

```
# frontend/.env.example
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_OAUTH_CLIENT_ID=
```

- [ ] **Step 2: Escribir el loader de Google Identity Services**

```typescript
// frontend/src/auth/google.ts
declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient(config: {
            client_id: string
            scope: string
            callback: (response: { access_token?: string; error?: string }) => void
          }): { requestAccessToken: () => void }
        }
      }
    }
  }
}

let cargando: Promise<void> | null = null

export function cargarGoogleIdentityServices(): Promise<void> {
  if (window.google?.accounts?.oauth2) return Promise.resolve()
  if (cargando) return cargando

  cargando = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('No se pudo cargar Google Identity Services.'))
    document.head.appendChild(script)
  })
  return cargando
}

export async function solicitarAccessTokenDeGoogle(clientId: string): Promise<string> {
  await cargarGoogleIdentityServices()
  return new Promise((resolve, reject) => {
    const client = window.google!.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: 'email profile',
      callback: (response) => {
        if (response.access_token) resolve(response.access_token)
        else reject(new Error(response.error ?? 'Login con Google cancelado.'))
      },
    })
    client.requestAccessToken()
  })
}
```

- [ ] **Step 3: Escribir el test de `AuthContext` que falla**

```typescript
// frontend/src/auth/AuthContext.test.tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import * as client from '../api/client'

function Sonda() {
  const { status, user } = useAuth()
  return <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
}

describe('AuthProvider', () => {
  afterEach(() => vi.restoreAllMocks())

  it('pasa a unauthenticated si /api/auth/user/ responde 401 al montar', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))

    render(
      <AuthProvider>
        <Sonda />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated:sin-usuario')
    })
  })

  it('pasa a authenticated con el usuario si /api/auth/user/ responde ok', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue({ pk: 1, email: 'asesor@ciencias.unam.mx', first_name: 'Ana' })

    render(
      <AuthProvider>
        <Sonda />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('authenticated:asesor@ciencias.unam.mx')
    })
  })
})
```

- [ ] **Step 4: Correr el test y confirmar que falla**

Run: `cd frontend && npx vitest run src/auth/AuthContext.test.tsx`
Expected: FAIL — `./AuthContext` no existe todavía.

- [ ] **Step 5: Implementar `AuthContext`**

```typescript
// frontend/src/auth/AuthContext.tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiGet, apiPost, ApiError, CLAVE_ACCESS, CLAVE_REFRESH } from '../api/client'
import type { AuthUser, LoginResponse } from '../api/types'
import { solicitarAccessTokenDeGoogle } from './google'

type EstadoSesion = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  user: AuthUser | null
  status: EstadoSesion
  loginWithPassword: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function persistirSesion(data: LoginResponse) {
  if (!import.meta.env.PROD) {
    localStorage.setItem(CLAVE_ACCESS, data.access)
    localStorage.setItem(CLAVE_REFRESH, data.refresh)
  }
}

function limpiarSesion() {
  localStorage.removeItem(CLAVE_ACCESS)
  localStorage.removeItem(CLAVE_REFRESH)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [status, setStatus] = useState<EstadoSesion>('loading')

  useEffect(() => {
    apiGet<AuthUser>('/api/auth/user/')
      .then((data) => {
        setUser(data)
        setStatus('authenticated')
      })
      .catch(() => setStatus('unauthenticated'))
  }, [])

  async function loginWithPassword(email: string, password: string) {
    const data = await apiPost<LoginResponse>('/api/auth/login/', { email, password })
    persistirSesion(data)
    setUser(data.user)
    setStatus('authenticated')
  }

  async function loginWithGoogle() {
    const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID
    const accessToken = await solicitarAccessTokenDeGoogle(clientId)
    const data = await apiPost<LoginResponse>('/api/auth/google/', { access_token: accessToken })
    persistirSesion(data)
    setUser(data.user)
    setStatus('authenticated')
  }

  async function logout() {
    try {
      await apiPost('/api/auth/logout/', {})
    } catch {
      // el logout limpia el lado del cliente igual aunque el request falle
    }
    limpiarSesion()
    setUser(null)
    setStatus('unauthenticated')
  }

  return (
    <AuthContext.Provider value={{ user, status, loginWithPassword, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return context
}
```

`ApiError` queda importado para que las pantallas que usan `useAuth` puedan
distinguir errores de credenciales (`400`) sin duplicar el tipo — se
re-exporta implícitamente vía `api/client`.

- [ ] **Step 6: Correr el test y confirmar que pasa**

Run: `cd frontend && npx vitest run src/auth/AuthContext.test.tsx`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/auth/AuthContext.tsx frontend/src/auth/google.ts frontend/src/auth/AuthContext.test.tsx frontend/.env.example
git commit -s -m "[feat][frontend] implementar AuthContext con login real y Google OAuth" \
  -m "- loginWithPassword/loginWithGoogle/logout contra la API real" \
  -m "- Restaura sesión al montar via GET /api/auth/user/, uniforme para dev y prod" \
  -m "- Loader de Google Identity Services (GIS token client, sin flujo de redirect)"
```

---

## Task 5: Detección de rol y rutas protegidas

**Files:**
- Create: `frontend/src/auth/rol.ts`
- Create: `frontend/src/auth/RutaProtegida.tsx`
- Test: `frontend/src/auth/rol.test.ts`

**Interfaces:**
- Consumes: `useAuth()` de Task 4; `apiGet`, `ApiError` de Task 2.
- Produces: `useEsAsesor()` (hook de React Query, `{ data: boolean | undefined, isPending }`), `RutaDeAsesor` (componente que envuelve rutas). Task 6 consume `RutaDeAsesor` en `App.tsx`.

- [ ] **Step 1: Escribir el test de `useEsAsesor` que falla**

```typescript
// frontend/src/auth/rol.test.ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEsAsesor } from './rol'
import * as client from '../api/client'

function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

describe('useEsAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('resuelve true si GET /api/asesorias/registros/ responde ok', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue([])
    const { result } = renderHook(() => useEsAsesor(), { wrapper: envolver })
    await waitFor(() => expect(result.current.data).toBe(true))
  })

  it('resuelve false si el endpoint responde 403', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(403, { message: 'Se requiere un perfil de asesor académico.' }))
    const { result } = renderHook(() => useEsAsesor(), { wrapper: envolver })
    await waitFor(() => expect(result.current.data).toBe(false))
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `cd frontend && npx vitest run src/auth/rol.test.ts`
Expected: FAIL — `./rol` no existe.

- [ ] **Step 3: Implementar `useEsAsesor`**

```typescript
// frontend/src/auth/rol.ts
import { useQuery } from '@tanstack/react-query'
import { apiGet, ApiError } from '../api/client'
import type { RegistroAsesor } from '../api/types'

// Sondeo interino: no existe endpoint de perfil/rol (deuda técnica 0010).
// GET /api/asesorias/registros/ es exclusivo de EsAsesorAcademico — 200
// significa "es asesor", 403 significa "no lo es".
export function useEsAsesor() {
  return useQuery({
    queryKey: ['rol', 'asesor'],
    queryFn: async () => {
      try {
        await apiGet<RegistroAsesor[]>('/api/asesorias/registros/')
        return true
      } catch (error) {
        if (error instanceof ApiError && error.status === 403) return false
        throw error
      }
    },
    staleTime: 5 * 60 * 1000,
  })
}
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `cd frontend && npx vitest run src/auth/rol.test.ts`
Expected: PASS

- [ ] **Step 5: Implementar `RutaDeAsesor`**

```typescript
// frontend/src/auth/RutaProtegida.tsx
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { useEsAsesor } from './rol'

function PantallaCargando() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="spinner h-6 w-6 text-primary" aria-label="Cargando" />
    </div>
  )
}

export function RutaDeAsesor({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const { data: esAsesor, isPending } = useEsAsesor()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (isPending) return <PantallaCargando />
  if (!esAsesor) return <Navigate to="/home" replace />

  return <>{children}</>
}
```

`.spinner` se define en la Task 7 (motion compartido); este componente ya lo
referencia porque es el primer lugar que necesita feedback de carga a nivel
de ruta completa.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/auth/rol.ts frontend/src/auth/rol.test.ts frontend/src/auth/RutaProtegida.tsx
git commit -s -m "[feat][frontend] detectar rol de asesor y proteger rutas" \
  -m "- useEsAsesor sondea GET /api/asesorias/registros/ (200/403) a falta de endpoint de perfil" \
  -m "- RutaDeAsesor redirige a /login si no hay sesión, a /home si no es asesor"
```

---

## Task 6: Wiring real de `Login.tsx` y rutas en `App.tsx`

**Files:**
- Modify: `frontend/src/screens/Login.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

**Interfaces:**
- Consumes: `useAuth()` (Task 4), `AuthProvider` (Task 4), `RutaDeAsesor` (Task 5).
- Produces: `/asesorias`, `/asesorias/disponibilidad`, `/asesorias/:id` montadas (placeholders hasta Tasks 9/11/12), protegidas.

- [ ] **Step 1: Envolver la app con `AuthProvider`**

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './auth/AuthContext'
import './index.css'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
```

- [ ] **Step 2: Reescribir `Login.tsx` contra la API real**

```typescript
// frontend/src/screens/Login.tsx
import { useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'

interface TextFieldProps {
  label: string
  type: string
  value: string
  autoComplete: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
}

function TextField({ label, type, value, autoComplete, onChange }: TextFieldProps) {
  return (
    <label className="relative block">
      <span className="absolute -top-2 left-3 bg-background px-1 text-xs text-on-surface-variant">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        required
        className="h-14 w-full rounded-md border border-outline bg-transparent px-3.5 text-sm text-on-surface outline-none focus:border-primary"
      />
    </label>
  )
}

export function Login() {
  const navigate = useNavigate()
  const { loginWithPassword, loginWithGoogle } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await loginWithPassword(email, password)
      navigate('/home')
    } catch (err) {
      setError(err instanceof ApiError ? 'Correo o contraseña incorrectos.' : 'No se pudo iniciar sesión. Intenta de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  async function handleGoogleLogin() {
    setError(null)
    setConectandoGoogle(true)
    try {
      await loginWithGoogle()
      navigate('/home')
    } catch {
      setError('No se pudo iniciar sesión con Google.')
    } finally {
      setConectandoGoogle(false)
    }
  }

  return (
    <main className="flex min-h-svh flex-col px-6 py-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        aria-label="Volver"
        className="mb-8 flex h-9 w-9 items-center justify-center text-on-background"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
          <path d="M15 19 L8 12 L15 5" />
        </svg>
      </button>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <TextField label="Correo" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField label="Contraseña" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />

        {error && (
          <p role="alert" className="text-sm text-error">
            {error}
          </p>
        )}

        <button type="button" className="self-end text-xs font-medium text-primary">
          ¿Olvidaste tu contraseña?
        </button>

        <button
          type="submit"
          disabled={enviando}
          className="flex h-11 items-center justify-center gap-2 rounded-full bg-primary text-sm font-semibold text-on-primary disabled:opacity-60"
        >
          {enviando && <span className="spinner h-4 w-4" aria-hidden />}
          Entrar
        </button>

        <div className="flex items-center gap-3 text-xs text-on-surface-variant">
          <span className="h-px flex-1 bg-outline-variant" />
          o
          <span className="h-px flex-1 bg-outline-variant" />
        </div>

        <button
          type="button"
          onClick={handleGoogleLogin}
          disabled={conectandoGoogle}
          className="flex h-11 items-center justify-center gap-2 rounded-full border border-outline text-sm font-semibold text-primary disabled:opacity-60"
        >
          {conectandoGoogle && <span className="spinner h-4 w-4" aria-hidden />}
          Continuar con Correo Ciencias
        </button>
      </form>
    </main>
  )
}
```

- [ ] **Step 3: Agregar rutas de asesoría en `App.tsx`**

```typescript
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './screens/Landing'
import { Login } from './screens/Login'
import { Home } from './screens/Home'
import { HealthCheck } from './screens/HealthCheck'
import { RutaDeAsesor } from './auth/RutaProtegida'
import { SesionesAsesor } from './features/asesorias/screens/SesionesAsesor'
import { DetalleAsesoria } from './features/asesorias/screens/DetalleAsesoria'
import { DisponibilidadAsesor } from './features/asesorias/screens/DisponibilidadAsesor'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/health" element={<HealthCheck />} />
        <Route
          path="/asesorias"
          element={
            <RutaDeAsesor>
              <SesionesAsesor />
            </RutaDeAsesor>
          }
        />
        <Route
          path="/asesorias/disponibilidad"
          element={
            <RutaDeAsesor>
              <DisponibilidadAsesor />
            </RutaDeAsesor>
          }
        />
        <Route
          path="/asesorias/:id"
          element={
            <RutaDeAsesor>
              <DetalleAsesoria />
            </RutaDeAsesor>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

Nota: esta task importa `SesionesAsesor`, `DetalleAsesoria` y
`DisponibilidadAsesor`, que se implementan en las Tasks 11, 12 y 9. Si se
ejecuta esta task antes que esas, crear stubs mínimos (`export function
SesionesAsesor() { return <p>TODO</p> }`) solo para que `tsc -b` no falle —
las tasks correspondientes los reemplazan por completo.

- [ ] **Step 4: Verificar manualmente**

Run: `cd frontend && pnpm dev`

Con Playwright (o el navegador): ir a `/login`, enviar credenciales inválidas
y confirmar que aparece el mensaje de error sin recargar la página; con
credenciales válidas de un usuario con `PerfilAsesorAcademico` en el backend
de dev, confirmar que redirige a `/home` y que `/asesorias` ya no redirige a
`/login`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/screens/Login.tsx frontend/src/App.tsx frontend/src/main.tsx
git commit -s -m "[feat][frontend] conectar Login a la API real y montar rutas de asesor" \
  -m "- Login.tsx llama a loginWithPassword/loginWithGoogle, muestra error y estado de carga" \
  -m "- Rutas /asesorias, /asesorias/disponibilidad, /asesorias/:id protegidas por RutaDeAsesor"
```

---

## Task 7: Sistema de motion compartido y componentes UI base

**Files:**
- Modify: `frontend/src/index.css`
- Create: `frontend/src/components/ui/Skeleton.tsx`
- Create: `frontend/src/components/ui/InsigniaEstado.tsx`
- Create: `frontend/src/components/ui/Boton.tsx`
- Create: `frontend/src/components/ui/Retroalimentacion.tsx`

**Interfaces:**
- Produces: `<Skeleton className?>`, `<InsigniaEstado estado>`, `<Boton cargando? ...props>`, `useRetroalimentacion()` + `<Retroalimentacion mensaje>`. Tasks 9, 11, 12 los consumen.

### Sistema de motion (de la investigación con `ui-ux-pro-max`)

No hay match en la base de datos del skill para "calendar/scheduling grid" — el
patrón de grilla semanal (Task 9) se diseña con heurística UX general, no con
un match de la base de datos. Sí hubo matches para timing de motion, que se
traducen aquí a CSS puro (se descartó GSAP, ver tabla de decisiones):

| Uso | Preset de referencia (GSAP) | Traducción a CSS |
|---|---|---|
| Skeleton de carga | shimmer, 1.4s `sine.inOut`, loop | `@keyframes shimmer` + `background-position`, 1.4s `ease-in-out infinite` |
| Entrada de items en lista | stagger subtle, 250-350ms `power1.out`, y=8px | `@keyframes entrada-lista`, 300ms `ease-out`, `translateY(8px)`, delay por item vía `style` |
| Botón en progreso | loader loop 800-1200ms | `.spinner`: borde girando, 600ms `linear infinite` (más rápido que un loader decorativo porque indica una acción puntual, no una espera larga) |
| Confirmación de éxito | success feedback | `@keyframes pulso-exito`: `scale(1→1.03→1)`, 400ms `ease-out`, una sola vez |
| Salida de items (cancelar/eliminar) | exit-faster-than-enter | reutiliza `entrada-lista` en reversa vía `animation-direction: reverse`, 200ms (más corto que la entrada) |

Regla aplicada de la base de UX (`ux-guidelines.csv`, categoría *Animation*/*Feedback*): mostrar skeleton/spinner solo para operaciones que puedan superar ~300ms, nunca para clics instantáneos — evita el "flash" que el propio skill marca como anti-patrón.

- [ ] **Step 1: Agregar keyframes y utilidades a `index.css`**

```css
/* frontend/src/index.css — agregar al final del archivo existente */

@keyframes shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

@keyframes entrada-lista {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulso-exito {
  0% { transform: scale(1); }
  40% { transform: scale(1.03); }
  100% { transform: scale(1); }
}

@keyframes girar {
  to { transform: rotate(360deg); }
}

.skeleton {
  background-image: linear-gradient(
    90deg,
    var(--color-surface-container) 25%,
    var(--color-surface-container-high) 50%,
    var(--color-surface-container) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

.entrada-lista {
  animation: entrada-lista 300ms ease-out backwards;
}

.salida-lista {
  animation: entrada-lista 200ms ease-in reverse forwards;
}

.pulso-exito {
  animation: pulso-exito 400ms ease-out;
}

.spinner {
  display: inline-block;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 9999px;
  animation: girar 600ms linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .skeleton,
  .entrada-lista,
  .salida-lista,
  .pulso-exito,
  .spinner {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

- [ ] **Step 2: Implementar `Skeleton`**

```typescript
// frontend/src/components/ui/Skeleton.tsx
export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`skeleton rounded-md ${className}`} aria-hidden />
}
```

- [ ] **Step 3: Implementar `InsigniaEstado`**

```typescript
// frontend/src/components/ui/InsigniaEstado.tsx
import type { EstadoAsesoria } from '../../api/types'

const ESTILOS: Record<EstadoAsesoria, string> = {
  agendada: 'bg-primary-container text-on-primary-container',
  realizada: 'bg-tertiary-container text-on-tertiary-container',
  cancelada: 'bg-error-container text-on-error-container',
}

const ETIQUETAS: Record<EstadoAsesoria, string> = {
  agendada: 'Agendada',
  realizada: 'Realizada',
  cancelada: 'Cancelada',
}

export function InsigniaEstado({ estado }: { estado: EstadoAsesoria }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${ESTILOS[estado]}`}>
      {ETIQUETAS[estado]}
    </span>
  )
}
```

- [ ] **Step 4: Implementar `Boton` (con spinner integrado)**

```typescript
// frontend/src/components/ui/Boton.tsx
import type { ButtonHTMLAttributes } from 'react'

interface BotonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  cargando?: boolean
  variante?: 'primario' | 'secundario' | 'peligro'
}

const VARIANTES: Record<NonNullable<BotonProps['variante']>, string> = {
  primario: 'bg-primary text-on-primary',
  secundario: 'border border-outline text-primary',
  peligro: 'bg-error-container text-on-error-container',
}

export function Boton({ cargando = false, variante = 'primario', disabled, children, className = '', ...props }: BotonProps) {
  return (
    <button
      disabled={disabled || cargando}
      className={`flex h-11 items-center justify-center gap-2 rounded-full text-sm font-semibold disabled:opacity-60 ${VARIANTES[variante]} ${className}`}
      {...props}
    >
      {cargando && <span className="spinner h-4 w-4" aria-hidden />}
      {children}
    </button>
  )
}
```

- [ ] **Step 5: Implementar `Retroalimentacion` (banner de éxito/error post-mutación)**

```typescript
// frontend/src/components/ui/Retroalimentacion.tsx
import { useCallback, useState } from 'react'

type TipoMensaje = 'exito' | 'error'
interface Mensaje {
  texto: string
  tipo: TipoMensaje
}

export function useRetroalimentacion() {
  const [mensaje, setMensaje] = useState<Mensaje | null>(null)

  const mostrar = useCallback((texto: string, tipo: TipoMensaje = 'exito') => {
    setMensaje({ texto, tipo })
    setTimeout(() => setMensaje(null), 3000)
  }, [])

  return { mensaje, mostrar }
}

export function Retroalimentacion({ mensaje }: { mensaje: Mensaje | null }) {
  if (!mensaje) return null
  const color = mensaje.tipo === 'exito' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'
  return (
    <div
      role="status"
      className={`entrada-lista fixed inset-x-0 bottom-6 mx-auto w-fit rounded-full px-4 py-2 text-sm font-medium shadow-lg ${color}`}
    >
      {mensaje.texto}
    </div>
  )
}
```

- [ ] **Step 6: Verificar manualmente**

Run: `cd frontend && pnpm build` — confirma que todo compila sin errores de tipos.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/index.css frontend/src/components/ui/
git commit -s -m "[feat][frontend] agregar sistema de motion y componentes UI base" \
  -m "- Skeleton, InsigniaEstado, Boton (con spinner) y Retroalimentacion compartidos" \
  -m "- Keyframes CSS puro para shimmer/entrada-lista/pulso-exito/spinner, respetan prefers-reduced-motion" \
  -m "- Timing basado en presets de ui-ux-pro-max (gsap domain), traducidos a CSS sin adoptar la librería"
```

---

## Task 8: Catálogo (materias/carreras) y hooks de disponibilidad del asesor

**Files:**
- Create: `frontend/src/features/catalogo/api.ts`
- Create: `frontend/src/features/asesorias/api.ts`
- Create: `frontend/src/features/asesorias/logica.ts`
- Test: `frontend/src/features/asesorias/logica.test.ts`

**Interfaces:**
- Consumes: `apiGet/apiPost/apiPatch/apiDelete` (Task 2), tipos de `api/types.ts`.
- Produces: `useMaterias`, `useCarreras`, `useMapaMaterias`, `useMapaCarreras` (catálogo); `useMisRegistros`, `useCrearRegistro`, `useAgregarMateria`, `useMisDisponibilidades`, `useCrearDisponibilidad`, `useActualizarDisponibilidad`, `useEliminarDisponibilidad` (asesorías); `semestreActual`, `claveSlot`, `mapaDisponibilidades` (lógica pura). Task 9 consume todo esto.

- [ ] **Step 1: Escribir el test de lógica pura que falla**

```typescript
// frontend/src/features/asesorias/logica.test.ts
import { describe, it, expect } from 'vitest'
import { semestreActual, claveSlot, mapaDisponibilidades } from './logica'
import type { Disponibilidad } from '../../api/types'

describe('semestreActual', () => {
  it('devuelve año+1 para meses de enero a junio', () => {
    expect(semestreActual(new Date('2026-03-15'))).toBe('20261')
  })

  it('devuelve año+2 para meses de julio a diciembre', () => {
    expect(semestreActual(new Date('2026-08-01'))).toBe('20262')
  })
})

describe('claveSlot', () => {
  it('combina día y hora en una clave estable', () => {
    expect(claveSlot(0, '09:00:00')).toBe('0-09:00:00')
  })
})

describe('mapaDisponibilidades', () => {
  const base: Disponibilidad = {
    id: 1,
    registro: 1,
    dia_semana: 0,
    hora_inicio: '09:00:00',
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: 'https://meet.example/x',
    activa: true,
  }

  it('indexa solo las disponibilidades activas por día+hora', () => {
    const mapa = mapaDisponibilidades([base, { ...base, id: 2, activa: false, dia_semana: 1 }])
    expect(mapa.size).toBe(1)
    expect(mapa.get('0-09:00:00')).toEqual(base)
    expect(mapa.get('1-09:00:00')).toBeUndefined()
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `cd frontend && npx vitest run src/features/asesorias/logica.test.ts`
Expected: FAIL — `./logica` no existe.

- [ ] **Step 3: Implementar `logica.ts` (funciones puras, primera mitad — el resto en Task 10)**

```typescript
// frontend/src/features/asesorias/logica.ts
import type { Disponibilidad } from '../../api/types'

export function semestreActual(hoy: Date = new Date()): string {
  const anio = hoy.getFullYear()
  const numero = hoy.getMonth() < 6 ? '1' : '2'
  return `${anio}${numero}`
}

export function claveSlot(diaSemana: number, horaInicio: string): string {
  return `${diaSemana}-${horaInicio}`
}

export function mapaDisponibilidades(disponibilidades: Disponibilidad[]): Map<string, Disponibilidad> {
  const mapa = new Map<string, Disponibilidad>()
  for (const disponibilidad of disponibilidades) {
    if (disponibilidad.activa) {
      mapa.set(claveSlot(disponibilidad.dia_semana, disponibilidad.hora_inicio), disponibilidad)
    }
  }
  return mapa
}
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `cd frontend && npx vitest run src/features/asesorias/logica.test.ts`
Expected: PASS

- [ ] **Step 5: Implementar hooks de catálogo**

```typescript
// frontend/src/features/catalogo/api.ts
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../../api/client'
import type { Materia, Carrera } from '../../api/types'

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: () => apiGet<Materia[]>('/api/materias/materias/'),
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

- [ ] **Step 6: Implementar hooks de `RegistroAsesor`/`Disponibilidad`**

```typescript
// frontend/src/features/asesorias/api.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPatch, apiDelete } from '../../api/client'
import type { RegistroAsesor, Disponibilidad } from '../../api/types'

export function useMisRegistros() {
  return useQuery({
    queryKey: ['registros'],
    queryFn: () => apiGet<RegistroAsesor[]>('/api/asesorias/registros/'),
  })
}

export function useCrearRegistro() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (semestre: string) => apiPost<RegistroAsesor>('/api/asesorias/registros/', { semestre }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['registros'] }),
  })
}

export function useAgregarMateria(registroId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (materiaId: number) =>
      apiPost<RegistroAsesor>(`/api/asesorias/registros/${registroId}/materias/`, { materia_id: materiaId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['registros'] }),
  })
}

export function useMisDisponibilidades() {
  return useQuery({
    queryKey: ['disponibilidades'],
    queryFn: () => apiGet<Disponibilidad[]>('/api/asesorias/disponibilidades/'),
  })
}

export function useCrearDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: Omit<Disponibilidad, 'id' | 'activa'>) =>
      apiPost<Disponibilidad>('/api/asesorias/disponibilidades/', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['disponibilidades'] }),
  })
}

export function useActualizarDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, activa }: { id: number; activa: boolean }) =>
      apiPatch<Disponibilidad>(`/api/asesorias/disponibilidades/${id}/`, { activa }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['disponibilidades'] }),
  })
}

export function useEliminarDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => apiDelete(`/api/asesorias/disponibilidades/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['disponibilidades'] }),
  })
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/catalogo/api.ts frontend/src/features/asesorias/api.ts frontend/src/features/asesorias/logica.ts frontend/src/features/asesorias/logica.test.ts
git commit -s -m "[feat][frontend] hooks de catálogo y de disponibilidad del asesor" \
  -m "- useMaterias/useCarreras con staleTime infinito (catálogo de solo lectura, casi no cambia)" \
  -m "- CRUD de RegistroAsesor/Disponibilidad sobre TanStack Query con invalidación tras cada mutación" \
  -m "- semestreActual/claveSlot/mapaDisponibilidades como funciones puras y probadas"
```

---

## Task 9: Pantalla de disponibilidad — grilla semanal

**Files:**
- Create: `frontend/src/features/asesorias/screens/DisponibilidadAsesor.tsx`
- Create: `frontend/src/features/asesorias/components/GrillaDisponibilidad.tsx`
- Create: `frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx`
- Create: `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx`

**Interfaces:**
- Consumes: hooks de Task 8, `Skeleton`/`Boton`/`Retroalimentacion` de Task 7.
- Produces: `<DisponibilidadAsesor />`, ruta ya montada en Task 6.

### Diseño de la pantalla

1. Al montar, `useMisRegistros()`. Si no hay un registro para `semestreActual()`, mostrar una tarjeta "Registrar disponibilidad para el semestre {X}" con el semestre pre-llenado y editable (input de texto, patrón `AAAAN`) — no hay endpoint de calendario académico (deuda técnica 0001) así que el semestre por defecto es una heurística de cliente que el asesor puede corregir antes de confirmar.
2. Con el registro creado: sección "Materias" (chips con el nombre resuelto vía `useMapaMaterias`, botón "+ agregar materia" que abre `DialogoAgregarMateria` — lista filtrable de materias con `habilitada_asesorias=true`, error inline si el backend rechaza por "no se imparte este semestre").
3. Grilla semanal: 7 columnas (Lunes–Domingo) × 28 filas (07:00–20:30 en bloques de 30 min). Celda vacía → clic abre `DialogoNuevoBloque` con día/hora ya fijados, pide `formato` + `ubicación`/`liga_virtual` según formato. Celda activa → clic abre un menú con "Desactivar" (PATCH `activa:false`) / "Eliminar" (DELETE).
4. Mientras `useMisDisponibilidades()` está `isPending`, la grilla completa se renderiza con `Skeleton` en vez de celdas.
5. Al crear un bloque, la celda nueva monta con `.entrada-lista` + `.pulso-exito`; al eliminar, la celda sale con `.salida-lista` antes de que TanStack Query refresque la lista (200ms, más corto que la entrada).

- [ ] **Step 1: Implementar `GrillaDisponibilidad`**

```typescript
// frontend/src/features/asesorias/components/GrillaDisponibilidad.tsx
import { useState } from 'react'
import type { Disponibilidad, FormatoAsesoria } from '../../../api/types'
import { claveSlot, mapaDisponibilidades } from '../logica'
import { Skeleton } from '../../../components/ui/Skeleton'

const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

function generarHoras(): string[] {
  const horas: string[] = []
  for (let h = 7; h <= 20; h++) {
    horas.push(`${String(h).padStart(2, '0')}:00:00`)
    horas.push(`${String(h).padStart(2, '0')}:30:00`)
  }
  return horas
}

const HORAS = generarHoras()

interface GrillaDisponibilidadProps {
  disponibilidades: Disponibilidad[]
  cargando: boolean
  onCeldaVacia: (diaSemana: number, horaInicio: string) => void
  onCeldaActiva: (disponibilidad: Disponibilidad) => void
}

export function GrillaDisponibilidad({ disponibilidades, cargando, onCeldaVacia, onCeldaActiva }: GrillaDisponibilidadProps) {
  const [pendientes] = useState<Set<string>>(new Set())
  const mapa = mapaDisponibilidades(disponibilidades)

  if (cargando) {
    return (
      <div className="grid grid-cols-8 gap-1">
        {Array.from({ length: 8 * 12 }).map((_, i) => (
          <Skeleton key={i} className="h-6" />
        ))}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[640px] grid-cols-8 gap-1 text-xs">
        <div />
        {DIAS.map((dia) => (
          <div key={dia} className="pb-1 text-center font-medium text-on-surface-variant">
            {dia}
          </div>
        ))}
        {HORAS.map((hora) => (
          <>
            <div key={`etiqueta-${hora}`} className="pr-2 text-right text-on-surface-variant">
              {hora.slice(0, 5)}
            </div>
            {DIAS.map((_, diaSemana) => {
              const clave = claveSlot(diaSemana, hora)
              const disponibilidad = mapa.get(clave)
              const estaPendiente = pendientes.has(clave)
              return (
                <button
                  key={clave}
                  type="button"
                  onClick={() => (disponibilidad ? onCeldaActiva(disponibilidad) : onCeldaVacia(diaSemana, hora))}
                  className={`h-6 rounded-sm border border-outline-variant transition-colors ${
                    disponibilidad
                      ? 'entrada-lista bg-primary-container hover:bg-primary'
                      : 'hover:bg-surface-container-high'
                  } ${estaPendiente ? 'animate-pulse opacity-60' : ''}`}
                  aria-label={
                    disponibilidad
                      ? `Bloque activo, ${DIAS[diaSemana]} ${hora.slice(0, 5)}, ${disponibilidad.formato}`
                      : `Crear bloque, ${DIAS[diaSemana]} ${hora.slice(0, 5)}`
                  }
                />
              )
            })}
          </>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Implementar `DialogoNuevoBloque` con Radix Dialog**

```typescript
// frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx
import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import type { FormatoAsesoria } from '../../../api/types'
import { Boton } from '../../../components/ui/Boton'

interface DialogoNuevoBloqueProps {
  abierto: boolean
  diaSemana: number | null
  horaInicio: string | null
  nombreDia: string
  cargando: boolean
  error: string | null
  onConfirmar: (datos: { formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }) => void
  onCerrar: () => void
}

export function DialogoNuevoBloque({ abierto, diaSemana, horaInicio, nombreDia, cargando, error, onConfirmar, onCerrar }: DialogoNuevoBloqueProps) {
  const [formato, setFormato] = useState<FormatoAsesoria>('virtual')
  const [ubicacion, setUbicacion] = useState('')
  const [ligaVirtual, setLigaVirtual] = useState('')

  if (diaSemana === null || horaInicio === null) return null

  return (
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-1 text-sm font-semibold text-on-surface">
            Nuevo bloque — {nombreDia} {horaInicio.slice(0, 5)}
          </Dialog.Title>
          <Dialog.Description className="mb-4 text-xs text-on-surface-variant">
            Bloque recurrente de 30 minutos cada semana.
          </Dialog.Description>

          <div className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
              Formato
              <select
                value={formato}
                onChange={(e) => setFormato(e.target.value as FormatoAsesoria)}
                className="h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
              >
                <option value="virtual">Virtual</option>
                <option value="presencial">Presencial</option>
              </select>
            </label>

            {formato === 'virtual' ? (
              <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
                Liga de la sesión
                <input
                  type="url"
                  value={ligaVirtual}
                  onChange={(e) => setLigaVirtual(e.target.value)}
                  required
                  className="h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
                />
              </label>
            ) : (
              <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
                Ubicación
                <input
                  type="text"
                  value={ubicacion}
                  onChange={(e) => setUbicacion(e.target.value)}
                  required
                  className="h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
                />
              </label>
            )}

            {error && <p role="alert" className="text-xs text-error">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Boton variante="secundario" type="button" onClick={onCerrar} className="flex-1">
                Cancelar
              </Boton>
              <Boton
                type="button"
                cargando={cargando}
                onClick={() => onConfirmar({ formato, ubicacion, liga_virtual: ligaVirtual })}
                className="flex-1"
              >
                Crear
              </Boton>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

- [ ] **Step 3: Implementar `DialogoAgregarMateria`**

```typescript
// frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx
import { useMemo, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useMaterias } from '../../catalogo/api'
import { Boton } from '../../../components/ui/Boton'

interface DialogoAgregarMateriaProps {
  abierto: boolean
  cargando: boolean
  error: string | null
  onConfirmar: (materiaId: number) => void
  onCerrar: () => void
}

export function DialogoAgregarMateria({ abierto, cargando, error, onConfirmar, onCerrar }: DialogoAgregarMateriaProps) {
  const { data: materias = [] } = useMaterias()
  const [busqueda, setBusqueda] = useState('')
  const [seleccionada, setSeleccionada] = useState<number | null>(null)

  const filtradas = useMemo(
    () =>
      materias.filter(
        (m) => m.habilitada_asesorias && m.nombre.toLowerCase().includes(busqueda.toLowerCase()),
      ),
    [materias, busqueda],
  )

  return (
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-4 text-sm font-semibold text-on-surface">Agregar materia</Dialog.Title>

          <input
            type="text"
            placeholder="Buscar materia…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="mb-3 h-10 w-full rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          />

          <ul className="mb-3 max-h-48 overflow-y-auto">
            {filtradas.map((materia) => (
              <li key={materia.id}>
                <button
                  type="button"
                  onClick={() => setSeleccionada(materia.id)}
                  className={`w-full rounded-md px-2 py-2 text-left text-sm ${
                    seleccionada === materia.id ? 'bg-primary-container text-on-primary-container' : 'text-on-surface hover:bg-surface-container-high'
                  }`}
                >
                  {materia.nombre}
                </button>
              </li>
            ))}
          </ul>

          {error && <p role="alert" className="mb-3 text-xs text-error">{error}</p>}

          <div className="flex gap-2">
            <Boton variante="secundario" type="button" onClick={onCerrar} className="flex-1">
              Cancelar
            </Boton>
            <Boton
              type="button"
              disabled={seleccionada === null}
              cargando={cargando}
              onClick={() => seleccionada !== null && onConfirmar(seleccionada)}
              className="flex-1"
            >
              Agregar
            </Boton>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

- [ ] **Step 4: Implementar la pantalla `DisponibilidadAsesor`**

```typescript
// frontend/src/features/asesorias/screens/DisponibilidadAsesor.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useMisRegistros,
  useCrearRegistro,
  useAgregarMateria,
  useMisDisponibilidades,
  useCrearDisponibilidad,
  useActualizarDisponibilidad,
  useEliminarDisponibilidad,
} from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { semestreActual } from '../logica'
import { GrillaDisponibilidad } from '../components/GrillaDisponibilidad'
import { DialogoNuevoBloque } from '../components/DialogoNuevoBloque'
import { DialogoAgregarMateria } from '../components/DialogoAgregarMateria'
import { Boton } from '../../../components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { ApiError } from '../../../api/client'
import type { Disponibilidad, FormatoAsesoria } from '../../../api/types'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

function primerMensajeDeError(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: string[] | string } | null
    if (Array.isArray(body?.detail)) return body.detail[0]
    if (typeof body?.detail === 'string') return body.detail
  }
  return 'Ocurrió un error inesperado.'
}

export function DisponibilidadAsesor() {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()

  const { data: registros, isPending: cargandoRegistros } = useMisRegistros()
  const crearRegistro = useCrearRegistro()
  const [semestreEditable, setSemestreEditable] = useState(semestreActual())

  const registroActual = registros?.find((r) => r.semestre === semestreEditable)

  const { data: disponibilidades = [], isPending: cargandoDisponibilidades } = useMisDisponibilidades()
  const crearDisponibilidad = useCrearDisponibilidad()
  const actualizarDisponibilidad = useActualizarDisponibilidad()
  const eliminarDisponibilidad = useEliminarDisponibilidad()
  const agregarMateria = useAgregarMateria(registroActual?.id ?? 0)
  const mapaMaterias = useMapaMaterias()

  const [celdaSeleccionada, setCeldaSeleccionada] = useState<{ dia: number; hora: string } | null>(null)
  const [errorBloque, setErrorBloque] = useState<string | null>(null)
  const [dialogoMateriaAbierto, setDialogoMateriaAbierto] = useState(false)
  const [errorMateria, setErrorMateria] = useState<string | null>(null)

  if (cargandoRegistros) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!registroActual) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <button type="button" onClick={() => navigate(-1)} className="text-sm text-primary">
          ← Volver
        </button>
        <h1 className="text-lg font-semibold text-on-background">Registrar disponibilidad</h1>
        <p className="text-sm text-on-surface-variant">
          Aún no tienes un registro de asesor para este semestre.
        </p>
        <label className="flex flex-col gap-1 text-xs text-on-surface-variant">
          Semestre (AAAAN)
          <input
            type="text"
            value={semestreEditable}
            onChange={(e) => setSemestreEditable(e.target.value)}
            className="h-11 w-32 rounded-md border border-outline bg-transparent px-3 text-sm text-on-surface"
          />
        </label>
        <Boton
          type="button"
          cargando={crearRegistro.isPending}
          onClick={() => crearRegistro.mutate(semestreEditable, { onSuccess: () => mostrar('Registro creado') })}
          className="w-fit px-6"
        >
          Registrar semestre {semestreEditable}
        </Boton>
        <Retroalimentacion mensaje={mensaje} />
      </main>
    )
  }

  function manejarCeldaVacia(dia: number, hora: string) {
    setErrorBloque(null)
    setCeldaSeleccionada({ dia, hora })
  }

  function manejarCeldaActiva(disponibilidad: Disponibilidad) {
    if (window.confirm('¿Eliminar este bloque de disponibilidad?')) {
      eliminarDisponibilidad.mutate(disponibilidad.id, {
        onSuccess: () => mostrar('Bloque eliminado'),
      })
    } else {
      actualizarDisponibilidad.mutate(
        { id: disponibilidad.id, activa: !disponibilidad.activa },
        { onSuccess: () => mostrar('Bloque actualizado') },
      )
    }
  }

  function manejarConfirmarBloque(datos: { formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }) {
    if (!celdaSeleccionada || !registroActual) return
    crearDisponibilidad.mutate(
      {
        registro: registroActual.id,
        dia_semana: celdaSeleccionada.dia,
        hora_inicio: celdaSeleccionada.hora,
        ...datos,
      },
      {
        onSuccess: () => {
          setCeldaSeleccionada(null)
          mostrar('Bloque creado')
        },
        onError: (error) => setErrorBloque(primerMensajeDeError(error)),
      },
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-6 px-6 py-6">
      <button type="button" onClick={() => navigate(-1)} className="w-fit text-sm text-primary">
        ← Volver
      </button>
      <h1 className="text-lg font-semibold text-on-background">Disponibilidad — semestre {registroActual.semestre}</h1>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium text-on-surface">Materias</h2>
          <button type="button" onClick={() => setDialogoMateriaAbierto(true)} className="text-xs font-medium text-primary">
            + Agregar materia
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {registroActual.materias.map((id) => (
            <span key={id} className="rounded-full bg-surface-container-high px-3 py-1 text-xs text-on-surface">
              {mapaMaterias.get(id)?.nombre ?? `Materia #${id}`}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium text-on-surface">Horario semanal</h2>
        <GrillaDisponibilidad
          disponibilidades={disponibilidades}
          cargando={cargandoDisponibilidades}
          onCeldaVacia={manejarCeldaVacia}
          onCeldaActiva={manejarCeldaActiva}
        />
      </section>

      <DialogoNuevoBloque
        abierto={celdaSeleccionada !== null}
        diaSemana={celdaSeleccionada?.dia ?? null}
        horaInicio={celdaSeleccionada?.hora ?? null}
        nombreDia={celdaSeleccionada ? DIAS[celdaSeleccionada.dia] : ''}
        cargando={crearDisponibilidad.isPending}
        error={errorBloque}
        onConfirmar={manejarConfirmarBloque}
        onCerrar={() => setCeldaSeleccionada(null)}
      />

      <DialogoAgregarMateria
        abierto={dialogoMateriaAbierto}
        cargando={agregarMateria.isPending}
        error={errorMateria}
        onConfirmar={(materiaId) =>
          agregarMateria.mutate(materiaId, {
            onSuccess: () => {
              setDialogoMateriaAbierto(false)
              setErrorMateria(null)
              mostrar('Materia agregada')
            },
            onError: (error) => setErrorMateria(primerMensajeDeError(error)),
          })
        }
        onCerrar={() => setDialogoMateriaAbierto(false)}
      />

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
```

- [ ] **Step 5: Verificar manualmente con el backend de dev**

Run: `cd frontend && pnpm dev` (con el backend de dev corriendo, un usuario con
`PerfilAsesorAcademico` y `PerfilAcademico`).

Con Playwright: login como asesor → navegar a `/asesorias/disponibilidad` →
crear el registro del semestre → agregar una materia → hacer clic en una
celda vacía de la grilla → crear un bloque virtual → confirmar que la celda
aparece activa con la animación de entrada → hacer clic en la celda activa →
confirmar el diálogo nativo de eliminación → confirmar que desaparece.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/DisponibilidadAsesor.tsx frontend/src/features/asesorias/components/GrillaDisponibilidad.tsx frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx
git commit -s -m "[feat][frontend] pantalla de disponibilidad semanal del asesor" \
  -m "- Registro de semestre (semestre sugerido editable, sin modelo de calendario académico)" \
  -m "- Grilla semanal 07:00-20:30/30min con creación/desactivación/eliminación de bloques" \
  -m "- Feedback de carga (skeleton) y de acción (pulso al crear, salida al eliminar) en la grilla"
```

---

## Task 10: Hooks de asesorías del asesor y derivaciones puras

**Files:**
- Modify: `frontend/src/features/asesorias/api.ts`
- Modify: `frontend/src/features/asesorias/logica.ts`
- Modify: `frontend/src/features/asesorias/logica.test.ts`

**Interfaces:**
- Consumes: `apiGet/apiPost` (Task 2).
- Produces: `useMisAsesorias`, `useCancelarAsesoria`, `useMarcarAsistencia`, `useGuardarNotas`; `proximas`, `historial`, `sesionesPreviasConNotas`, `sesionYaOcurrio`, `puedeGuardarNotas`. Tasks 11 y 12 consumen todo esto.

- [ ] **Step 1: Agregar los tests que fallan a `logica.test.ts`**

```typescript
// frontend/src/features/asesorias/logica.test.ts — agregar al archivo existente
import { proximas, historial, sesionesPreviasConNotas, sesionYaOcurrio, puedeGuardarNotas } from './logica'
import type { Asesoria } from '../../api/types'

function crearAsesoria(overrides: Partial<Asesoria>): Asesoria {
  return {
    id: 1,
    alumno: 10,
    disponibilidad: 1,
    materia: 1,
    carrera: 1,
    fecha: '2026-08-03',
    hora_inicio: '10:00:00',
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: 'https://meet.example/x',
    estado: 'agendada',
    asistio: null,
    notas: '',
    creado_en: '2026-08-01T10:00:00Z',
    ...overrides,
  }
}

describe('proximas', () => {
  it('incluye solo agendadas, ordenadas por fecha ascendente', () => {
    const a = crearAsesoria({ id: 1, fecha: '2026-08-10', estado: 'agendada' })
    const b = crearAsesoria({ id: 2, fecha: '2026-08-03', estado: 'agendada' })
    const c = crearAsesoria({ id: 3, fecha: '2026-08-01', estado: 'realizada' })
    expect(proximas([a, b, c]).map((x) => x.id)).toEqual([2, 1])
  })
})

describe('historial', () => {
  it('incluye realizadas y canceladas, ordenadas por fecha descendente', () => {
    const a = crearAsesoria({ id: 1, fecha: '2026-07-01', estado: 'realizada' })
    const b = crearAsesoria({ id: 2, fecha: '2026-07-15', estado: 'cancelada' })
    const c = crearAsesoria({ id: 3, fecha: '2026-08-01', estado: 'agendada' })
    expect(historial([a, b, c]).map((x) => x.id)).toEqual([2, 1])
  })
})

describe('sesionesPreviasConNotas', () => {
  it('filtra por mismo alumno, excluye la actual, solo realizadas con notas', () => {
    const actual = crearAsesoria({ id: 1, alumno: 10, estado: 'agendada' })
    const previaConNotas = crearAsesoria({ id: 2, alumno: 10, estado: 'realizada', notas: 'Le costó factorizar', fecha: '2026-07-01' })
    const previaSinNotas = crearAsesoria({ id: 3, alumno: 10, estado: 'realizada', notas: '', fecha: '2026-07-08' })
    const otroAlumno = crearAsesoria({ id: 4, alumno: 99, estado: 'realizada', notas: 'otra cosa', fecha: '2026-07-10' })
    const resultado = sesionesPreviasConNotas([actual, previaConNotas, previaSinNotas, otroAlumno], 10, 1)
    expect(resultado.map((x) => x.id)).toEqual([2])
  })
})

describe('sesionYaOcurrio', () => {
  it('es true si la fecha+hora de inicio ya pasó', () => {
    const asesoria = { fecha: '2026-08-01', hora_inicio: '10:00:00' }
    expect(sesionYaOcurrio(asesoria, new Date('2026-08-01T11:00:00'))).toBe(true)
    expect(sesionYaOcurrio(asesoria, new Date('2026-08-01T09:00:00'))).toBe(false)
  })
})

describe('puedeGuardarNotas', () => {
  it('solo es true si la sesión está realizada y hubo asistencia', () => {
    expect(puedeGuardarNotas({ estado: 'realizada', asistio: true })).toBe(true)
    expect(puedeGuardarNotas({ estado: 'realizada', asistio: false })).toBe(false)
    expect(puedeGuardarNotas({ estado: 'agendada', asistio: null })).toBe(false)
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `cd frontend && npx vitest run src/features/asesorias/logica.test.ts`
Expected: FAIL — `proximas`/`historial`/`sesionesPreviasConNotas`/`sesionYaOcurrio`/`puedeGuardarNotas` no existen.

- [ ] **Step 3: Agregar las funciones a `logica.ts`**

```typescript
// frontend/src/features/asesorias/logica.ts — agregar al archivo existente
import type { Asesoria } from '../../api/types'

function claveOrden(asesoria: Asesoria): string {
  return `${asesoria.fecha}T${asesoria.hora_inicio}`
}

export function proximas(asesorias: Asesoria[]): Asesoria[] {
  return asesorias
    .filter((a) => a.estado === 'agendada')
    .sort((a, b) => claveOrden(a).localeCompare(claveOrden(b)))
}

export function historial(asesorias: Asesoria[]): Asesoria[] {
  return asesorias
    .filter((a) => a.estado !== 'agendada')
    .sort((a, b) => claveOrden(b).localeCompare(claveOrden(a)))
}

export function sesionesPreviasConNotas(asesorias: Asesoria[], alumnoId: number, excluirId: number): Asesoria[] {
  return asesorias
    .filter((a) => a.alumno === alumnoId && a.id !== excluirId && a.estado === 'realizada' && a.notas.trim() !== '')
    .sort((a, b) => claveOrden(b).localeCompare(claveOrden(a)))
}

export function sesionYaOcurrio(asesoria: Pick<Asesoria, 'fecha' | 'hora_inicio'>, ahora: Date): boolean {
  const inicio = new Date(`${asesoria.fecha}T${asesoria.hora_inicio}`)
  return ahora >= inicio
}

export function puedeGuardarNotas(asesoria: Pick<Asesoria, 'estado' | 'asistio'>): boolean {
  return asesoria.estado === 'realizada' && asesoria.asistio === true
}
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `cd frontend && npx vitest run src/features/asesorias/logica.test.ts`
Expected: PASS (todos los `describe` de la Task 8 y esta task)

- [ ] **Step 5: Agregar hooks de `Asesoria` a `api.ts`**

```typescript
// frontend/src/features/asesorias/api.ts — agregar al archivo existente
import type { Asesoria } from '../../api/types'

export function useMisAsesorias() {
  return useQuery({
    queryKey: ['asesorias'],
    queryFn: () => apiGet<Asesoria[]>('/api/asesorias/asesorias/'),
  })
}

export function useCancelarAsesoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) =>
      apiPost<Asesoria>(`/api/asesorias/asesorias/${id}/cancelar/`, { motivo }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}

export function useMarcarAsistencia() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, asistio }: { id: number; asistio: boolean }) =>
      apiPost<Asesoria>(`/api/asesorias/asesorias/${id}/marcar_asistencia/`, { asistio }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}

export function useGuardarNotas() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, texto }: { id: number; texto: string }) =>
      apiPost<Asesoria>(`/api/asesorias/asesorias/${id}/notas/`, { texto }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/api.ts frontend/src/features/asesorias/logica.ts frontend/src/features/asesorias/logica.test.ts
git commit -s -m "[feat][frontend] hooks de asesorías del asesor y derivaciones puras" \
  -m "- useMisAsesorias/useCancelarAsesoria/useMarcarAsistencia/useGuardarNotas" \
  -m "- proximas/historial/sesionesPreviasConNotas/sesionYaOcurrio/puedeGuardarNotas, todas probadas"
```

---

## Task 11: Pantalla de lista — Próximas / Historial

**Files:**
- Create: `frontend/src/features/asesorias/screens/SesionesAsesor.tsx`
- Create: `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`
- Test: `frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx`

**Interfaces:**
- Consumes: `useMisAsesorias` (Task 10), `useMapaMaterias` (Task 8), `proximas`/`historial` (Task 10), `Skeleton`/`InsigniaEstado` (Task 7).
- Produces: `<SesionesAsesor />`, ya montada en la ruta `/asesorias` desde Task 6.

- [ ] **Step 1: Implementar `TarjetaAsesoria`**

```typescript
// frontend/src/features/asesorias/components/TarjetaAsesoria.tsx
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

interface TarjetaAsesoriaProps {
  asesoria: Asesoria
  nombreMateria: string
  indice: number
}

export function TarjetaAsesoria({ asesoria, nombreMateria, indice }: TarjetaAsesoriaProps) {
  const navigate = useNavigate()
  const fecha = FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))

  return (
    <li
      className="entrada-lista"
      style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}
    >
      <button
        type="button"
        onClick={() => navigate(`/asesorias/${asesoria.id}`)}
        className="flex w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
      >
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-on-surface">{nombreMateria}</span>
          <span className="text-xs text-on-surface-variant">
            {fecha} · {asesoria.hora_inicio.slice(0, 5)} · Alumno #{asesoria.alumno}
          </span>
        </div>
        <InsigniaEstado estado={asesoria.estado} />
      </button>
    </li>
  )
}
```

- [ ] **Step 2: Escribir el test de la pantalla que falla**

```typescript
// frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SesionesAsesor } from './SesionesAsesor'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { Asesoria } from '../../../api/types'

function crearAsesoria(overrides: Partial<Asesoria>): Asesoria {
  return {
    id: 1, alumno: 10, disponibilidad: 1, materia: 1, carrera: 1,
    fecha: '2026-08-03', hora_inicio: '10:00:00', formato: 'virtual',
    ubicacion: '', liga_virtual: '', estado: 'agendada', asistio: null,
    notas: '', creado_en: '2026-08-01T10:00:00Z', ...overrides,
  }
}

function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('SesionesAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('la tab Próximas muestra solo agendadas por default', () => {
    vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
      data: [
        crearAsesoria({ id: 1, estado: 'agendada' }),
        crearAsesoria({ id: 2, estado: 'realizada' }),
      ],
      isPending: false,
    } as ReturnType<typeof api.useMisAsesorias>)
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]))

    render(<SesionesAsesor />, { wrapper: envolver })

    expect(screen.getAllByText('Cálculo I')).toHaveLength(1)
  })
})
```

- [ ] **Step 3: Correr el test y confirmar que falla**

Run: `cd frontend && npx vitest run src/features/asesorias/screens/SesionesAsesor.test.tsx`
Expected: FAIL — `./SesionesAsesor` no existe.

- [ ] **Step 4: Implementar `SesionesAsesor` con tabs de Radix**

```typescript
// frontend/src/features/asesorias/screens/SesionesAsesor.tsx
import { useNavigate } from 'react-router-dom'
import * as Tabs from '@radix-ui/react-tabs'
import { useMisAsesorias } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { proximas, historial } from '../logica'
import { TarjetaAsesoria } from '../components/TarjetaAsesoria'
import { Skeleton } from '../../../components/ui/Skeleton'

export function SesionesAsesor() {
  const navigate = useNavigate()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>
        <button
          type="button"
          onClick={() => navigate('/asesorias/disponibilidad')}
          className="text-xs font-medium text-primary"
        >
          Disponibilidad
        </button>
      </div>

      <Tabs.Root defaultValue="proximas">
        <Tabs.List className="mb-4 flex gap-4 border-b border-outline-variant text-sm">
          <Tabs.Trigger
            value="proximas"
            className="px-1 pb-2 text-on-surface-variant data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary"
          >
            Próximas
          </Tabs.Trigger>
          <Tabs.Trigger
            value="historial"
            className="px-1 pb-2 text-on-surface-variant data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary"
          >
            Historial
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="proximas">
          <ListaAsesorias asesorias={proximas(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="No tienes asesorías próximas." />
        </Tabs.Content>
        <Tabs.Content value="historial">
          <ListaAsesorias asesorias={historial(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="Aún no hay historial." />
        </Tabs.Content>
      </Tabs.Root>
    </main>
  )
}

function ListaAsesorias({
  asesorias,
  cargando,
  nombreMateria,
  vacio,
}: {
  asesorias: ReturnType<typeof proximas>
  cargando: boolean
  nombreMateria: (id: number) => string | undefined
  vacio: string
}) {
  if (cargando) {
    return (
      <ul className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-16" />
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
          nombreMateria={nombreMateria(asesoria.materia) ?? `Materia #${asesoria.materia}`}
          indice={indice}
        />
      ))}
    </ul>
  )
}
```

- [ ] **Step 5: Correr el test y confirmar que pasa**

Run: `cd frontend && npx vitest run src/features/asesorias/screens/SesionesAsesor.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/SesionesAsesor.tsx frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx frontend/src/features/asesorias/components/TarjetaAsesoria.tsx
git commit -s -m "[feat][frontend] pantalla de lista de asesorías con tabs Próximas/Historial" \
  -m "- Tabs de Radix UI, tarjetas con InsigniaEstado y entrada escalonada" \
  -m "- Skeleton mientras carga, estado vacío por tab"
```

---

## Task 12: Pantalla de detalle — información y notas de sesiones previas

**Files:**
- Create: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`

**Interfaces:**
- Consumes: `useMisAsesorias` (Task 10), `sesionesPreviasConNotas` (Task 10), `useMapaMaterias`/`useMapaCarreras` (Task 8).
- Produces: `<DetalleAsesoria />`, ya montada en `/asesorias/:id` desde Task 6. Task 13 agrega las acciones de estado sobre este mismo archivo.

- [ ] **Step 1: Implementar la pantalla (solo lectura por ahora, sin acciones)**

```typescript
// frontend/src/features/asesorias/screens/DetalleAsesoria.tsx
import { useParams, useNavigate } from 'react-router-dom'
import { useMisAsesorias } from '../api'
import { useMapaMaterias, useMapaCarreras } from '../../catalogo/api'
import { sesionesPreviasConNotas } from '../logica'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { Skeleton } from '../../../components/ui/Skeleton'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

export function DetalleAsesoria() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()
  const mapaCarreras = useMapaCarreras()

  if (isPending) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24" />
      </main>
    )
  }

  const asesoria = asesorias.find((a) => a.id === Number(id))
  if (!asesoria) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        <p className="text-sm text-on-surface-variant">No se encontró la asesoría.</p>
        <button type="button" onClick={() => navigate('/asesorias')} className="w-fit text-sm text-primary">
          ← Volver a Asesorías
        </button>
      </main>
    )
  }

  const previas = sesionesPreviasConNotas(asesorias, asesoria.alumno, asesoria.id)

  return (
    <main className="flex min-h-svh flex-col gap-6 px-6 py-6">
      <button type="button" onClick={() => navigate('/asesorias')} className="w-fit text-sm text-primary">
        ← Volver a Asesorías
      </button>

      <section className="rounded-lg bg-surface-container p-4">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-base font-semibold text-on-surface">
            {mapaMaterias.get(asesoria.materia)?.nombre ?? `Materia #${asesoria.materia}`}
          </h1>
          <InsigniaEstado estado={asesoria.estado} />
        </div>
        <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
          <dt>Alumno</dt>
          <dd>Alumno #{asesoria.alumno}</dd>
          <dt>Carrera</dt>
          <dd>{mapaCarreras.get(asesoria.carrera)?.nombre ?? `Carrera #${asesoria.carrera}`}</dd>
          <dt>Fecha</dt>
          <dd>{FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))}</dd>
          <dt>Hora</dt>
          <dd>{asesoria.hora_inicio.slice(0, 5)}</dd>
          <dt>Formato</dt>
          <dd>
            {asesoria.formato === 'virtual' ? (
              <a href={asesoria.liga_virtual} target="_blank" rel="noreferrer" className="text-primary underline">
                Liga de la sesión
              </a>
            ) : (
              asesoria.ubicacion
            )}
          </dd>
        </dl>
      </section>

      {/* Sección de acciones (cancelar / marcar asistencia / notas) — Task 13 */}

      <section>
        <h2 className="mb-2 text-sm font-medium text-on-surface">Notas de sesiones anteriores con este alumno</h2>
        {previas.length === 0 ? (
          <p className="text-sm text-on-surface-variant">No hay notas de sesiones anteriores.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {previas.map((previa) => (
              <li key={previa.id} className="rounded-lg bg-surface-container-low p-3 text-sm">
                <p className="mb-1 text-xs text-on-surface-variant">
                  {FORMATEADOR_FECHA.format(new Date(`${previa.fecha}T00:00:00`))}
                </p>
                <p className="text-on-surface">{previa.notas}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
```

- [ ] **Step 2: Verificar manualmente**

Run: `cd frontend && pnpm dev`. Con dos asesorías `realizada` del mismo alumno
en el backend de dev (una con `notas`, otra sin), confirmar que el detalle de
una tercera asesoría de ese alumno lista solo la que tiene notas.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/asesorias/screens/DetalleAsesoria.tsx
git commit -s -m "[feat][frontend] pantalla de detalle con historial de notas del alumno" \
  -m "- Información de la sesión (materia/carrera resueltas vía catálogo, alumno como placeholder por id)" \
  -m "- Panel de notas de sesiones previas realizadas del mismo alumno (sesionesPreviasConNotas)"
```

---

## Task 13: Acciones de cambio de estado — cancelar, marcar asistencia, notas

**Files:**
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`
- Create: `frontend/src/features/asesorias/components/DialogoCancelar.tsx`
- Test: `frontend/src/features/asesorias/logica.test.ts` (ya cubre `sesionYaOcurrio`/`puedeGuardarNotas` de Task 10 — este task los consume en UI, sin lógica pura nueva)

**Interfaces:**
- Consumes: `useCancelarAsesoria`/`useMarcarAsistencia`/`useGuardarNotas` (Task 10), `sesionYaOcurrio`/`puedeGuardarNotas` (Task 10), `Boton`/`Retroalimentacion` (Task 7).
- Produces: flujo de acciones completo sobre `DetalleAsesoria`.

### Diseño del flujo de estados

- `estado === 'agendada'`:
  - Siempre visible: botón "Cancelar asesoría" → abre `DialogoCancelar` (motivo opcional) → `useCancelarAsesoria`.
  - Si `sesionYaOcurrio(asesoria, ahora)`: sección "Marcar asistencia" con dos botones "Asistió" / "No asistió" → `useMarcarAsistencia`. El backend rechaza marcar asistencia antes de la hora de inicio (`ValidationError`), por eso el gating también ocurre en el cliente — evita un viaje de red que sabemos que va a fallar.
  - Si no ha ocurrido: nota informativa con la hora en la que se habilita.
- `estado === 'realizada'`:
  - Insignia de asistencia (`Asistió` / `No asistió`).
  - Si `puedeGuardarNotas(asesoria)`: textarea editable con las notas actuales, botón "Guardar notas" (deshabilitado si el texto no cambió) → `useGuardarNotas`.
  - Si no: leyenda "El alumno no asistió a esta sesión." (el backend bloquea `guardar_notas` en este caso).
- `estado === 'cancelada'`: panel de solo lectura con el motivo de cancelación.

- [ ] **Step 1: Implementar `DialogoCancelar`**

```typescript
// frontend/src/features/asesorias/components/DialogoCancelar.tsx
import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { Boton } from '../../../components/ui/Boton'

interface DialogoCancelarProps {
  abierto: boolean
  cargando: boolean
  onConfirmar: (motivo: string) => void
  onCerrar: () => void
}

export function DialogoCancelar({ abierto, cargando, onConfirmar, onCerrar }: DialogoCancelarProps) {
  const [motivo, setMotivo] = useState('')

  return (
    <Dialog.Root open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-container p-5">
          <Dialog.Title className="mb-1 text-sm font-semibold text-on-surface">Cancelar asesoría</Dialog.Title>
          <Dialog.Description className="mb-4 text-xs text-on-surface-variant">
            Se notificará al alumno por correo. Esta acción no se puede deshacer.
          </Dialog.Description>

          <label className="mb-4 flex flex-col gap-1 text-xs text-on-surface-variant">
            Motivo (opcional)
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={3}
              className="rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
            />
          </label>

          <div className="flex gap-2">
            <Boton variante="secundario" type="button" onClick={onCerrar} className="flex-1">
              Volver
            </Boton>
            <Boton variante="peligro" type="button" cargando={cargando} onClick={() => onConfirmar(motivo)} className="flex-1">
              Confirmar cancelación
            </Boton>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

- [ ] **Step 2: Agregar las acciones a `DetalleAsesoria.tsx`**

```typescript
// frontend/src/features/asesorias/screens/DetalleAsesoria.tsx
// Reemplazar el import list y agregar lo siguiente:

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useMisAsesorias, useCancelarAsesoria, useMarcarAsistencia, useGuardarNotas } from '../api'
import { useMapaMaterias, useMapaCarreras } from '../../catalogo/api'
import { sesionesPreviasConNotas, sesionYaOcurrio, puedeGuardarNotas } from '../logica'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { Skeleton } from '../../../components/ui/Skeleton'
import { Boton } from '../../../components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { DialogoCancelar } from '../components/DialogoCancelar'
import type { Asesoria } from '../../../api/types'

const FORMATEADOR_HORA = new Intl.DateTimeFormat('es-MX', { hour: '2-digit', minute: '2-digit' })

// ... (mismo bloque de carga/no-encontrado de la Task 12) ...

// Dentro del componente, después de calcular `asesoria` y `previas`:
function SeccionAcciones({ asesoria }: { asesoria: Asesoria }) {
  const { mensaje, mostrar } = useRetroalimentacion()
  const cancelar = useCancelarAsesoria()
  const marcarAsistencia = useMarcarAsistencia()
  const guardarNotas = useGuardarNotas()
  const [dialogoCancelarAbierto, setDialogoCancelarAbierto] = useState(false)
  const [notas, setNotas] = useState(asesoria.notas)

  if (asesoria.estado === 'cancelada') {
    return (
      <section className="rounded-lg bg-surface-container-low p-4">
        <p className="text-sm text-on-surface-variant">
          Esta asesoría fue cancelada. El motivo no está disponible todavía en
          la API (ver deuda técnica 0010) — el campo existe en el backend pero
          no se expone en el serializer.
        </p>
      </section>
    )
  }

  if (asesoria.estado === 'realizada') {
    return (
      <section className="flex flex-col gap-3 rounded-lg bg-surface-container-low p-4">
        <p className="text-sm text-on-surface">{asesoria.asistio ? 'El alumno asistió.' : 'El alumno no asistió.'}</p>
        {puedeGuardarNotas(asesoria) ? (
          <>
            <textarea
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              rows={4}
              placeholder="Notas de la sesión…"
              className="rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
            />
            <Boton
              type="button"
              disabled={notas === asesoria.notas}
              cargando={guardarNotas.isPending}
              onClick={() =>
                guardarNotas.mutate(
                  { id: asesoria.id, texto: notas },
                  { onSuccess: () => mostrar('Notas guardadas') },
                )
              }
              className="w-fit px-6"
            >
              Guardar notas
            </Boton>
          </>
        ) : null}
        <Retroalimentacion mensaje={mensaje} />
      </section>
    )
  }

  const yaOcurrio = sesionYaOcurrio(asesoria, new Date())

  return (
    <section className="flex flex-col gap-3 rounded-lg bg-surface-container-low p-4">
      {yaOcurrio ? (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-on-surface">¿El alumno asistió a esta sesión?</p>
          <div className="flex gap-2">
            <Boton
              type="button"
              cargando={marcarAsistencia.isPending}
              onClick={() => marcarAsistencia.mutate({ id: asesoria.id, asistio: true }, { onSuccess: () => mostrar('Asistencia registrada') })}
              className="flex-1"
            >
              Asistió
            </Boton>
            <Boton
              type="button"
              variante="secundario"
              cargando={marcarAsistencia.isPending}
              onClick={() => marcarAsistencia.mutate({ id: asesoria.id, asistio: false }, { onSuccess: () => mostrar('Asistencia registrada') })}
              className="flex-1"
            >
              No asistió
            </Boton>
          </div>
        </div>
      ) : (
        <p className="text-xs text-on-surface-variant">
          Podrás marcar asistencia después de las {FORMATEADOR_HORA.format(new Date(`${asesoria.fecha}T${asesoria.hora_inicio}`))}.
        </p>
      )}

      <Boton variante="peligro" type="button" onClick={() => setDialogoCancelarAbierto(true)} className="w-fit px-6">
        Cancelar asesoría
      </Boton>

      <DialogoCancelar
        abierto={dialogoCancelarAbierto}
        cargando={cancelar.isPending}
        onConfirmar={(motivo) =>
          cancelar.mutate(
            { id: asesoria.id, motivo },
            {
              onSuccess: () => {
                setDialogoCancelarAbierto(false)
                mostrar('Asesoría cancelada')
              },
            },
          )
        }
        onCerrar={() => setDialogoCancelarAbierto(false)}
      />
      <Retroalimentacion mensaje={mensaje} />
    </section>
  )
}
```

Insertar `<SeccionAcciones asesoria={asesoria} />` en `DetalleAsesoria` justo
donde estaba el comentario `{/* Sección de acciones ... — Task 13 */}` de la
Task 12, y mover `SeccionAcciones` a nivel de módulo (fuera de
`DetalleAsesoria`) en el mismo archivo.

Nota sobre `motivo_cancelacion` y `cancelado_por`: confirmado en
`backend/asesorias/serializers.py` que `AsesoriaSerializer.Meta.fields` no los
incluye (ver deuda técnica 0010, Task 1) — por eso el tipo `Asesoria` de
`api/types.ts` (Task 2) tampoco los tiene, y el panel de "cancelada" arriba no
intenta leerlos.

- [ ] **Step 3: Verificar manualmente el ciclo completo**

Run: `cd frontend && pnpm dev`. Con Playwright, sobre una asesoría de prueba:

1. Estado `agendada`, antes de la hora → confirmar que solo aparece "Cancelar asesoría" y la nota de "podrás marcar asistencia después de…".
2. Cancelar con motivo → confirmar que el detalle pasa a mostrar el panel de solo lectura con el motivo.
3. Sobre una asesoría `agendada` cuya hora ya pasó (usar una fecha/hora pasada en el fixture de dev) → confirmar que aparecen "Asistió"/"No asistió".
4. Marcar "Asistió" → confirmar que aparece el textarea de notas, guardar notas → confirmar el mensaje de éxito y que persiste al recargar.
5. Marcar "No asistió" en otra asesoría → confirmar que NO aparece textarea de notas.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/asesorias/screens/DetalleAsesoria.tsx frontend/src/features/asesorias/components/DialogoCancelar.tsx
git commit -s -m "[feat][frontend] flujo de cambio de estado: cancelar, asistencia y notas" \
  -m "- Cancelar con motivo vía diálogo de confirmación (acción destructiva)" \
  -m "- Marcar asistencia gateado client-side por sesionYaOcurrio, espejo de la regla del backend" \
  -m "- Notas editables solo cuando puedeGuardarNotas, con feedback de guardado"
```

---

## Verificación end-to-end del plan completo

1. `cd frontend && pnpm install && pnpm build` — sin errores de TypeScript.
2. `cd frontend && pnpm test` (Vitest) — todos los tests de `logica.ts`, `client.ts`, `AuthContext.tsx`, `rol.ts` y `SesionesAsesor.tsx` en verde.
3. Backend de dev corriendo (`docker-compose.dev.yml` o `uv run manage.py runserver`) con al menos un usuario con `PerfilAsesorAcademico` + `PerfilAcademico`, y un `PerfilAlumno` de prueba.
4. Con Playwright (o manual): login → `/home` → navegar a `/asesorias/disponibilidad` → registrar semestre → agregar materia → crear 2-3 bloques en la grilla → volver a `/asesorias` → confirmar que la pantalla no tiene datos todavía (no hay asesorías agendadas por un alumno de prueba aún — esto requiere la Fase 2 o crear una `Asesoria` directo por Django admin/shell para probar el flujo de detalle).
5. Crear manualmente una `Asesoria` vía Django admin/shell contra uno de los bloques creados, con `fecha` de hoy y `hora_inicio` en el pasado (para poder probar `marcar_asistencia` sin esperar) → confirmar en `/asesorias` que aparece en "Próximas" → entrar al detalle → marcar asistencia → agregar notas → confirmar que pasa a "Historial".
6. Confirmar visualmente que las animaciones (skeleton al cargar, pulso al crear bloque, fade al eliminar, spinner en botones durante mutaciones) se ven y no hay parpadeos para operaciones instantáneas (verificar con throttling de red en devtools para simular latencia).
7. Confirmar `prefers-reduced-motion: reduce` en devtools → las animaciones se reducen a casi instantáneas sin romper la funcionalidad.
