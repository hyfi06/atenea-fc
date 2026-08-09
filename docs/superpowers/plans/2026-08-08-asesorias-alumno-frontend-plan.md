# Vista unificada de Asesorías (frontend) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir la pantalla de asesorías en una vista unificada por rol: el asesor conserva *Mis materias*/*Mi horario*; el alumno gana *Nueva asesoría* → oferta → wizard de agendado. Ambos ven Próximas/Historial; el alumno nunca ve las notas del asesor.

**Architecture:** Una sola ruta `/asesorias` con un componente (`Asesorias.tsx`, renombra `SesionesAsesor.tsx`) que ramifica por rol con `useEsAsesor()`/`useEsAlumno()`. Guard nuevo `RutaDeAsesorias` (alumno **o** asesor). Dos pantallas nuevas sólo-alumno (`OfertaAsesorias`, `AgendarAsesoria` como stepper de una ruta). Hooks nuevos en `features/asesorias/api.ts` sobre los contratos del backend (plan gemelo de API). Lógica pura de agrupación por día en `logica.ts`, testeada aparte.

**Tech Stack:** React + TypeScript + Vite, TanStack Query, React Router v6, Vitest + Testing Library. Componentes compartidos (`Tabs`, `Dialogo`, `Boton`, `Skeleton`, `InsigniaEstado`) y tokens MD3.

**Spec:** [`2026-08-08-asesorias-alumno-frontend-design.md`](../specs/2026-08-08-asesorias-alumno-frontend-design.md) · **ADR:** [0022](../../decisions/0022-asesorias-vista-unificada-frontend.md) · **API gemela:** [`2026-08-08-asesorias-alumno-api-plan.md`](2026-08-08-asesorias-alumno-api-plan.md)

## Global Constraints

- **Depende de la API del plan gemelo:** los endpoints `oferta/`, `oferta/{materia}/asesores/`, `disponibilidad/buscar/?asesor=`, `POST asesorias/` con `carrera` y el ocultamiento de `notas` deben existir (o mockearse en tests). Los tests de este plan **mockean los hooks/`apiGet`**, así que no requieren el backend corriendo.
- **Patrón de estado de servidor:** TanStack Query con `apiGet`/`apiPost` de `src/api/client.ts` y **query keys planas**; mutaciones invalidan con `invalidateQueries`. Igual que `features/asesorias/api.ts`.
- **Patrón de test:** Vitest + Testing Library, test colocado junto al archivo, hooks mockeados con `vi.spyOn(modulo, 'hook')`, `usuarioDePrueba` de `src/test/factories.ts`. Igual que `SesionesAsesor.test.tsx` y `RutaProtegida.test.tsx`.
- **Convención de diálogos** ([ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)): usar el `Dialogo` compartido; 2 acciones (salir + confirmar) → fila. No montar `Dialog.Root` a mano.
- **Accesibilidad/estilo:** toque mínimo `min-h-11` (44px), `.foco-visible` en todo interactivo, truncamiento de materia con `truncate`+`title` en filas, motion sólo con clases CSS existentes (`entrada-lista`, `pulso-exito`) que ya respetan `@media (prefers-reduced-motion)`.
- **Deuda referenciada, no nueva:** selector de carrera autoseleccionado con la única carrera de hoy → [deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md); paginación de oferta → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).
- **Comandos** (desde `frontend/`): test puntual `npx vitest run <ruta>`; suite `npm test`; build `npm run build`; lint `npm run lint`.
- **Commits:** `[type][scope] resumen` + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>`.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `frontend/src/api/types.ts` | Tipos del contrato | Modificar: `Asesoria` (+`alumno_nombre`/`asesor_nombre`); crear `MateriaOferta`, `AsesorDisponible`, `SlotDisponibilidad` |
| `frontend/src/features/asesorias/api.ts` | Hooks de datos | Añadir `useOferta`, `useAsesoresDeMateria`, `useDisponibilidadDeAsesor`, `useAgendarAsesoria`, `useSemestres`, `useAsesoriasDeSemestre` |
| `frontend/src/features/asesorias/logica.ts` | Lógica pura | Añadir `agruparPorDia` + tipo `DiaDisponible` |
| `frontend/src/auth/RutaProtegida.tsx` | Guards de ruta | Añadir `RutaDeAsesorias` (conserva `RutaDeAsesor`) |
| `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx` | Tarjeta por rol | Modificar: contraparte por rol; nunca `notas`; navegación sólo-asesor; `destacar` |
| `frontend/src/features/asesorias/screens/Asesorias.tsx` | Vista unificada | Crear (renombra `SesionesAsesor.tsx`) |
| `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx` | Oferta (alumno) | Crear |
| `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx` | Wizard de agendado (alumno) | Crear |
| `frontend/src/App.tsx` | Ruteo | Modificar: `RutaDeAsesorias` en `/asesorias`; rutas `/asesorias/nueva` y `/asesorias/nueva/:materiaId` |

**Decisión de alcance registrada aquí:** el detalle `/asesorias/:id` (`DetalleAsesoria`) sigue siendo asesor-only (fuera de alcance, spec §Out of scope). Por eso la `TarjetaAsesoria` del alumno **no navega** a detalle — es una tarjeta informativa. Se documenta en Task 4.

---

## Task 1: Tipos y hooks de datos

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/features/asesorias/api.ts`

**Interfaces:**
- Produces (tipos):
  - `Asesoria` gana `alumno_nombre: string` y `asesor_nombre: string`.
  - `MateriaOferta { materia_id: number; nombre: string; carrera_id: number; num_asesores: number }`
  - `AsesorDisponible { registro_id: number; asesor_nombre: string; area_nombre: string; formatos: FormatoAsesoria[] }`
  - `SlotDisponibilidad { registro_id: number; asesor_nombre: string; disponibilidad_id: number; fecha: string; hora_inicio: string; hora_fin: string; formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }`
- Produces (hooks): `useOferta()`, `useAsesoresDeMateria(materiaId)`, `useDisponibilidadDeAsesor(materiaId, registroId)`, `useAgendarAsesoria()`, `useSemestres()`, `useAsesoriasDeSemestre(semestre)`.

Este task se verifica por typecheck/build; los hooks se ejercitan en los tests de pantalla de tasks posteriores (convención del repo: se mockean los hooks, no se testean en aislamiento).

- [ ] **Step 1: Extender `types.ts`**

En `frontend/src/api/types.ts`, añadir a la interfaz `Asesoria` (junto a `alumno`):

```typescript
export interface Asesoria {
  id: number
  alumno: number
  alumno_nombre: string
  asesor_nombre: string
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
  // El backend omite `notas` cuando quien pide no es el asesor dueño
  // (ADR 0021). Ninguna pantalla del alumno la lee; sólo DetalleAsesoria
  // (asesor-only) la consume.
  notas: string
  creado_en: string
}
```

Y al final del archivo, los tres tipos nuevos:

```typescript
export interface MateriaOferta {
  materia_id: number
  nombre: string
  carrera_id: number
  num_asesores: number
}

export interface AsesorDisponible {
  registro_id: number
  asesor_nombre: string
  area_nombre: string
  formatos: FormatoAsesoria[]
}

/** Resultado de GET /disponibilidad/buscar/?asesor=, extendido con la
 *  identidad del asesor (ADR 0021). */
export interface SlotDisponibilidad {
  registro_id: number
  asesor_nombre: string
  disponibilidad_id: number
  fecha: string
  hora_inicio: string
  hora_fin: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
}
```

- [ ] **Step 2: Añadir los hooks en `api.ts`**

En `frontend/src/features/asesorias/api.ts`, ampliar el import de tipos y añadir los hooks al final del archivo:

```typescript
import type {
  RegistroAsesor, Disponibilidad, Asesoria, SesionesFuturas,
  MateriaOferta, AsesorDisponible, SlotDisponibilidad,
} from '../../api/types'
```

```typescript
export function useOferta() {
  return useQuery({
    queryKey: ['oferta'],
    queryFn: () => apiGet<MateriaOferta[]>('/api/asesorias/oferta/'),
  })
}

export function useAsesoresDeMateria(materiaId: number | null) {
  return useQuery({
    queryKey: ['oferta', materiaId, 'asesores'],
    queryFn: () => apiGet<AsesorDisponible[]>(`/api/asesorias/oferta/${materiaId}/asesores/`),
    enabled: materiaId !== null,
  })
}

export function useDisponibilidadDeAsesor(materiaId: number | null, registroId: number | null) {
  return useQuery({
    queryKey: ['disponibilidad', materiaId, registroId],
    queryFn: () =>
      apiGet<SlotDisponibilidad[]>(
        `/api/asesorias/disponibilidad/buscar/?materia=${materiaId}&asesor=${registroId}`,
      ),
    enabled: materiaId !== null && registroId !== null,
  })
}

export interface PayloadAgendar {
  disponibilidad: number
  fecha: string
  materia: number
  carrera: number
}

export function useAgendarAsesoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PayloadAgendar) => apiPost<Asesoria>('/api/asesorias/asesorias/', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['asesorias'] }),
  })
}

export function useSemestres() {
  return useQuery({
    queryKey: ['asesorias', 'semestres'],
    queryFn: () => apiGet<string[]>('/api/asesorias/asesorias/semestres/'),
  })
}

/** Sesiones filtradas por semestre para los subtabs del historial. La key
 *  comparte el prefijo ['asesorias'], así que `useAgendarAsesoria` la
 *  invalida junto con la lista principal. */
export function useAsesoriasDeSemestre(semestre: string | null) {
  return useQuery({
    queryKey: ['asesorias', { semestre }],
    queryFn: () => apiGet<Asesoria[]>(`/api/asesorias/asesorias/?semestre=${semestre}`),
    enabled: semestre !== null,
  })
}
```

- [ ] **Step 3: Verificar typecheck y build**

Run: `npm run build`
Expected: PASS (`tsc -b` sin errores + `vite build`). Nota: aún no hay consumidores nuevos; esto sólo valida que los tipos y hooks compilan.

- [ ] **Step 4: Lint**

Run: `npm run lint`
Expected: sin errores nuevos.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/features/asesorias/api.ts
git commit -m "[feat][frontend] tipos y hooks para oferta, disponibilidad por asesor y agendado

- Asesoria +alumno_nombre/asesor_nombre; MateriaOferta, AsesorDisponible, SlotDisponibilidad
- useOferta, useAsesoresDeMateria, useDisponibilidadDeAsesor, useAgendarAsesoria, useSemestres, useAsesoriasDeSemestre

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Lógica pura `agruparPorDia`

**Files:**
- Modify: `frontend/src/features/asesorias/logica.ts`
- Test: `frontend/src/features/asesorias/logica.test.ts`

**Interfaces:**
- Consumes: `SlotDisponibilidad` (Task 1).
- Produces: `agruparPorDia(slots: SlotDisponibilidad[]): DiaDisponible[]` donde `DiaDisponible = { fecha: string; slots: SlotDisponibilidad[] }`. Días ordenados por `fecha` asc; slots de cada día ordenados por `hora_inicio` asc.

- [ ] **Step 1: Escribir el test que falla**

Añadir al final de `frontend/src/features/asesorias/logica.test.ts`:

```typescript
import { agruparPorDia } from './logica'
import type { SlotDisponibilidad } from '../../api/types'

function slot(overrides: Partial<SlotDisponibilidad>): SlotDisponibilidad {
  return {
    registro_id: 7, asesor_nombre: 'Ana', disponibilidad_id: 1,
    fecha: '2026-08-10', hora_inicio: '10:00:00', hora_fin: '10:30:00',
    formato: 'virtual', ubicacion: '', liga_virtual: 'https://x', ...overrides,
  }
}

describe('agruparPorDia', () => {
  it('agrupa slots por fecha', () => {
    const dias = agruparPorDia([
      slot({ disponibilidad_id: 1, fecha: '2026-08-10' }),
      slot({ disponibilidad_id: 2, fecha: '2026-08-10', hora_inicio: '11:00:00' }),
      slot({ disponibilidad_id: 3, fecha: '2026-08-11' }),
    ])
    expect(dias.map((d) => d.fecha)).toEqual(['2026-08-10', '2026-08-11'])
    expect(dias[0].slots).toHaveLength(2)
    expect(dias[1].slots).toHaveLength(1)
  })

  it('ordena los días por fecha ascendente', () => {
    const dias = agruparPorDia([
      slot({ fecha: '2026-08-12' }),
      slot({ fecha: '2026-08-10' }),
    ])
    expect(dias.map((d) => d.fecha)).toEqual(['2026-08-10', '2026-08-12'])
  })

  it('ordena los slots de cada día por hora_inicio', () => {
    const [dia] = agruparPorDia([
      slot({ disponibilidad_id: 1, hora_inicio: '12:00:00' }),
      slot({ disponibilidad_id: 2, hora_inicio: '09:00:00' }),
    ])
    expect(dia.slots.map((s) => s.hora_inicio)).toEqual(['09:00:00', '12:00:00'])
  })

  it('devuelve lista vacía sin slots', () => {
    expect(agruparPorDia([])).toEqual([])
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/logica.test.ts`
Expected: FAIL — `agruparPorDia is not a function`.

- [ ] **Step 3: Implementar `agruparPorDia`**

En `frontend/src/features/asesorias/logica.ts`, ampliar el import y añadir la función:

```typescript
import type { Disponibilidad, Asesoria, SlotDisponibilidad } from '../../api/types'
```

```typescript
export interface DiaDisponible {
  fecha: string
  slots: SlotDisponibilidad[]
}

/** Agrupa los slots planos de la búsqueda en días (dos semanas), listos para
 *  dibujar el paso "día" → "bloque" del wizard. Días por fecha asc; bloques
 *  de cada día por hora asc. */
export function agruparPorDia(slots: SlotDisponibilidad[]): DiaDisponible[] {
  const porFecha = new Map<string, SlotDisponibilidad[]>()
  for (const slot of slots) {
    const lista = porFecha.get(slot.fecha) ?? []
    lista.push(slot)
    porFecha.set(slot.fecha, lista)
  }
  return [...porFecha.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([fecha, delDia]) => ({
      fecha,
      slots: [...delDia].sort((x, y) => x.hora_inicio.localeCompare(y.hora_inicio)),
    }))
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/logica.test.ts`
Expected: PASS (4 casos nuevos + los existentes de `logica.test.ts`).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/logica.ts frontend/src/features/asesorias/logica.test.ts
git commit -m "[feat][frontend] logica pura agruparPorDia para el wizard de agendado

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Guard `RutaDeAsesorias`

**Files:**
- Modify: `frontend/src/auth/RutaProtegida.tsx`
- Test: `frontend/src/auth/RutaProtegida.test.tsx`

**Interfaces:**
- Consumes: `useAuth().status`, `useEsAsesor()`, `useEsAlumno()`.
- Produces: `RutaDeAsesorias({ children })` — deja pasar a autenticados que sean **alumno o asesor**; externos (ninguno de los dos) → `/home`; no autenticados → `/login`. `RutaDeAsesor` se conserva sin cambios para `/materias`, `/horario`, `/:id`.

- [ ] **Step 1: Escribir el test que falla**

Añadir a `frontend/src/auth/RutaProtegida.test.tsx` un segundo bloque de montaje y `describe`. En los imports, añadir `RutaDeAsesorias`:

```typescript
import { RutaDeAsesor, RutaDeAsesorias } from './RutaProtegida'
```

```typescript
function montarAsesorias() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/asesorias']}>
        <Routes>
          <Route
            path="/asesorias"
            element={
              <RutaDeAsesorias>
                <p>vista de asesorías</p>
              </RutaDeAsesorias>
            }
          />
          <Route path="/home" element={<p>pantalla home</p>} />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaDeAsesorias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar al alumno', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    montarAsesorias()
    expect(await screen.findByText('vista de asesorías')).toBeInTheDocument()
  })

  it('deja pasar al asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ roles: ['academico', 'asesor_academico'] }),
    )
    montarAsesorias()
    expect(await screen.findByText('vista de asesorías')).toBeInTheDocument()
  })

  it('manda a Home a quien no es alumno ni asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['academico'] }))
    montarAsesorias()
    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('vista de asesorías')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    montarAsesorias()
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/auth/RutaProtegida.test.tsx`
Expected: FAIL — `RutaDeAsesorias` no está exportado.

- [ ] **Step 3: Implementar `RutaDeAsesorias`**

En `frontend/src/auth/RutaProtegida.tsx`, ampliar el import de `rol` y añadir la función (deja intacta `RutaDeAsesor`):

```typescript
import { useEsAsesor, useEsAlumno } from './rol'
```

```typescript
export function RutaDeAsesorias({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esAsesor && !esAlumno) return <Navigate to="/home" replace />

  return <>{children}</>
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/auth/RutaProtegida.test.tsx`
Expected: PASS — los 4 casos de `RutaDeAsesorias` y los 4 de `RutaDeAsesor` verdes.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/auth/RutaProtegida.tsx frontend/src/auth/RutaProtegida.test.tsx
git commit -m "[feat][frontend] guard RutaDeAsesorias (alumno o asesor)

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: `TarjetaAsesoria` — contraparte por rol, sin notas, navegación sólo-asesor

**Files:**
- Modify: `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`
- Test: `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx` (crear)

**Interfaces:**
- Consumes: `useEsAsesor()`, `Asesoria.alumno_nombre`/`asesor_nombre`.
- Produces: `TarjetaAsesoria({ asesoria, nombreMateria, indice, destacar? })`. Muestra el nombre del **contraparte** (asesor ve `alumno_nombre`; alumno ve `asesor_nombre`); nunca renderiza `notas`. Para el asesor es un botón que navega a `/asesorias/{id}`; para el alumno es una tarjeta informativa (no navega — detalle asesor-only, fuera de alcance). `destacar` aplica `pulso-exito` y hace `scrollIntoView`+`focus`.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx`:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TarjetaAsesoria } from './TarjetaAsesoria'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

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
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: FAIL — hoy la tarjeta siempre es un botón y muestra `Alumno #{id}`.

- [ ] **Step 3: Reescribir `TarjetaAsesoria`**

Reemplazar el contenido de `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`:

```tsx
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { useEsAsesor } from '../../../auth/rol'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

interface TarjetaAsesoriaProps {
  asesoria: Asesoria
  nombreMateria: string
  indice: number
  /** Resalta y enfoca la tarjeta recién agendada (post-agendado). */
  destacar?: boolean
}

export function TarjetaAsesoria({ asesoria, nombreMateria, indice, destacar = false }: TarjetaAsesoriaProps) {
  const navigate = useNavigate()
  const esAsesor = useEsAsesor()
  const ref = useRef<HTMLElement | null>(null)
  const fecha = FORMATEADOR_FECHA.format(new Date(`${asesoria.fecha}T00:00:00`))

  // El asesor ve al alumno; el alumno ve al asesor. Los dos nombres los
  // expone el serializer (ADR 0021); reemplaza el viejo `Alumno #{id}`.
  const contraparte = esAsesor ? asesoria.alumno_nombre : asesoria.asesor_nombre

  useEffect(() => {
    if (destacar && ref.current) {
      ref.current.scrollIntoView({ block: 'center' })
      ref.current.focus()
    }
  }, [destacar])

  const contenido = (
    <div className="flex w-full items-center justify-between">
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-on-surface">{nombreMateria}</span>
        <span className="text-xs text-on-surface-variant">
          {fecha} · {asesoria.hora_inicio.slice(0, 5)} · {contraparte}
        </span>
      </div>
      <InsigniaEstado estado={asesoria.estado} />
    </div>
  )

  const clasesBase = `flex w-full rounded-lg bg-surface-container px-4 py-3 text-left${destacar ? ' pulso-exito' : ''}`

  return (
    <li className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
      {esAsesor ? (
        <button
          ref={(el) => { ref.current = el }}
          type="button"
          onClick={() => navigate(`/asesorias/${asesoria.id}`)}
          className={`foco-visible ${clasesBase}`}
        >
          {contenido}
        </button>
      ) : (
        // El alumno no navega a detalle: /asesorias/:id es asesor-only
        // (spec §Out of scope). tabIndex=-1 permite el focus programático de
        // `destacar` sin meterla en el orden de tabulación.
        <div ref={(el) => { ref.current = el }} tabIndex={-1} className={clasesBase}>
          {contenido}
        </div>
      )}
    </li>
  )
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: PASS (3 casos).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/components/TarjetaAsesoria.tsx frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx
git commit -m "[feat][frontend] TarjetaAsesoria muestra el contraparte por rol, sin notas

- alumno ve asesor_nombre; asesor ve alumno_nombre y navega a detalle
- prop destacar para resaltar la tarjeta recien agendada

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: Vista unificada `Asesorias.tsx` (renombra `SesionesAsesor.tsx`)

**Files:**
- Create: `frontend/src/features/asesorias/screens/Asesorias.tsx` (renombra `SesionesAsesor.tsx`)
- Create: `frontend/src/features/asesorias/screens/Asesorias.test.tsx` (renombra `SesionesAsesor.test.tsx`)
- Delete: `SesionesAsesor.tsx`, `SesionesAsesor.test.tsx`
- Modify: `frontend/src/App.tsx` (sólo el import/uso `SesionesAsesor` → `Asesorias`; guard y rutas nuevas van en Task 8)

**Interfaces:**
- Consumes: `useMisAsesorias`, `useSemestres`, `useAsesoriasDeSemestre`, `useMapaMaterias`, `proximas`/`historial`, `useEsAsesor`/`useEsAlumno`, `TarjetaAsesoria` (con `destacar`), `useLocation().state.nuevaAsesoriaId`.
- Produces: componente `Asesorias`. Encabezado por rol: asesor → *Mis materias*/*Mi horario*; alumno → *Nueva asesoría* (`/asesorias/nueva`). Tabs Próximas/Historial; Historial con subtabs por semestre. La tab Próximas resalta la tarjeta cuyo `id === nuevaAsesoriaId`.

- [ ] **Step 1: Renombrar los archivos y ajustar el test**

```bash
git mv frontend/src/features/asesorias/screens/SesionesAsesor.tsx frontend/src/features/asesorias/screens/Asesorias.tsx
git mv frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx frontend/src/features/asesorias/screens/Asesorias.test.tsx
```

- [ ] **Step 2: Escribir el test nuevo (falla)**

Reemplazar el contenido de `frontend/src/features/asesorias/screens/Asesorias.test.tsx`:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Asesorias } from './Asesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import * as rol from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

function crearAsesoria(overrides: Partial<Asesoria> = {}): Asesoria {
  return {
    id: 1, alumno: 10, alumno_nombre: 'Beto', asesor_nombre: 'Ana',
    disponibilidad: 1, materia: 1, carrera: 1, fecha: '2026-08-03', hora_inicio: '10:00:00',
    formato: 'virtual', ubicacion: '', liga_virtual: '', estado: 'agendada', asistio: null,
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

function montar({ esAsesor, esAlumno }: { esAsesor: boolean; esAlumno: boolean }) {
  vi.spyOn(rol, 'useEsAsesor').mockReturnValue(esAsesor)
  vi.spyOn(rol, 'useEsAlumno').mockReturnValue(esAlumno)
  vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
    data: [crearAsesoria({ id: 1 })], isPending: false,
  } as ReturnType<typeof api.useMisAsesorias>)
  vi.spyOn(api, 'useSemestres').mockReturnValue({
    data: [], isPending: false,
  } as ReturnType<typeof api.useSemestres>)
  vi.spyOn(api, 'useAsesoriasDeSemestre').mockReturnValue({
    data: [], isPending: false,
  } as ReturnType<typeof api.useAsesoriasDeSemestre>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )
  render(<Asesorias />, { wrapper: envolver })
}

describe('Asesorias (vista unificada)', () => {
  afterEach(() => vi.restoreAllMocks())

  it('el alumno ve Nueva asesoría y no las acciones del asesor', () => {
    montar({ esAsesor: false, esAlumno: true })
    expect(screen.getByRole('button', { name: 'Nueva asesoría' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mis materias' })).not.toBeInTheDocument()
  })

  it('el asesor ve Mis materias / Mi horario y no Nueva asesoría', () => {
    montar({ esAsesor: true, esAlumno: false })
    expect(screen.getByRole('button', { name: 'Mis materias' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mi horario' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Nueva asesoría' })).not.toBeInTheDocument()
  })

  it('muestra las tabs Próximas e Historial para ambos', () => {
    montar({ esAsesor: false, esAlumno: true })
    expect(screen.getByRole('tab', { name: 'Próximas' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Historial' })).toBeInTheDocument()
  })
})
```

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx`
Expected: FAIL — `Asesorias` no existe (el archivo aún exporta `SesionesAsesor`).

- [ ] **Step 3: Reescribir la pantalla**

Reemplazar el contenido de `frontend/src/features/asesorias/screens/Asesorias.tsx`:

```tsx
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import { useMisAsesorias, useSemestres, useAsesoriasDeSemestre } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { proximas, historial } from '../logica'
import { TarjetaAsesoria } from '../components/TarjetaAsesoria'
import { Skeleton } from '../../../components/ui/Skeleton'
import { useEsAsesor, useEsAlumno } from '../../../auth/rol'
import type { Asesoria } from '../../../api/types'

export function Asesorias() {
  const navigate = useNavigate()
  const location = useLocation()
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  const { data: asesorias = [], isPending } = useMisAsesorias()
  const mapaMaterias = useMapaMaterias()
  const nuevaAsesoriaId = (location.state as { nuevaAsesoriaId?: number } | null)?.nuevaAsesoriaId ?? null
  const nombreMateria = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>

      <div className="flex gap-2">
        {esAsesor && (
          <>
            <button
              type="button"
              onClick={() => navigate('/asesorias/materias')}
              className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
            >
              Mis materias
            </button>
            <button
              type="button"
              onClick={() => navigate('/asesorias/horario')}
              className="foco-visible min-h-11 flex-1 rounded-full border border-outline px-3 text-sm font-medium text-primary"
            >
              Mi horario
            </button>
          </>
        )}
        {esAlumno && (
          <button
            type="button"
            onClick={() => navigate('/asesorias/nueva')}
            className="foco-visible min-h-11 flex-1 rounded-full bg-primary px-3 text-sm font-semibold text-on-primary"
          >
            Nueva asesoría
          </button>
        )}
      </div>

      <Tabs defaultValue="proximas">
        <TabsList>
          <TabsTrigger value="proximas">Próximas</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="proximas">
          <ListaAsesorias
            asesorias={proximas(asesorias)}
            cargando={isPending}
            nombreMateria={nombreMateria}
            destacarId={nuevaAsesoriaId}
            vacio="No tienes asesorías próximas."
          />
        </TabsContent>
        <TabsContent value="historial">
          <Historial nombreMateria={nombreMateria} />
        </TabsContent>
      </Tabs>
    </main>
  )
}

function Historial({ nombreMateria }: { nombreMateria: (id: number) => string }) {
  const { data: semestres = [], isPending } = useSemestres()
  const [activo, setActivo] = useState<string | null>(null)
  const semestre = activo ?? semestres[0] ?? null
  const { data: asesorias = [], isPending: cargandoLista } = useAsesoriasDeSemestre(semestre)

  if (isPending) return <Skeleton className="h-8 w-40" />
  if (semestres.length === 0) return <p className="text-sm text-on-surface-variant">Aún no hay historial.</p>

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
      <ListaAsesorias
        asesorias={historial(asesorias)}
        cargando={cargandoLista}
        nombreMateria={nombreMateria}
        destacarId={null}
        vacio="Sin sesiones en este semestre."
      />
    </div>
  )
}

function ListaAsesorias({
  asesorias,
  cargando,
  nombreMateria,
  destacarId,
  vacio,
}: {
  asesorias: Asesoria[]
  cargando: boolean
  nombreMateria: (id: number) => string
  destacarId: number | null
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
          nombreMateria={nombreMateria(asesoria.materia)}
          indice={indice}
          destacar={asesoria.id === destacarId}
        />
      ))}
    </ul>
  )
}
```

- [ ] **Step 4: Ajustar `App.tsx` (sólo el nombre)**

En `frontend/src/App.tsx`, cambiar el import y los 1 uso del componente para que el build siga verde (el guard y las rutas nuevas se cambian en Task 8):

```tsx
import { Asesorias } from './features/asesorias/screens/Asesorias'
```

Y en el `<Route path="/asesorias" ...>` reemplazar `<SesionesAsesor />` por `<Asesorias />` (dejando `RutaDeAsesor` por ahora).

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx`
Expected: PASS (3 casos).

- [ ] **Step 6: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS — sin referencias colgantes a `SesionesAsesor`.

- [ ] **Step 7: Commit**

```bash
git add -A frontend/src/features/asesorias/screens/ frontend/src/App.tsx
git commit -m "[feat][frontend] vista unificada de asesorias por rol con historial por semestre

- renombra SesionesAsesor -> Asesorias; encabezado por rol (asesor/alumno)
- historial con subtabs por semestre; resalta la tarjeta recien agendada

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 6: Pantalla de oferta `OfertaAsesorias.tsx` (alumno)

**Files:**
- Create: `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx`
- Test: `frontend/src/features/asesorias/screens/OfertaAsesorias.test.tsx`

**Interfaces:**
- Consumes: `useOferta()`, `useMapaCarreras()`.
- Produces: componente `OfertaAsesorias`. Lista `MateriaOferta` con `num_asesores`; filtro por carrera (`<select>`) + búsqueda por nombre (input, `useMemo` en cliente, patrón de `DialogoAgregarMateria`). Al elegir una materia navega a `/asesorias/nueva/{materia_id}`.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/OfertaAsesorias.test.tsx`:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { OfertaAsesorias } from './OfertaAsesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { MateriaOferta } from '../../../api/types'

const OFERTA: MateriaOferta[] = [
  { materia_id: 1, nombre: 'Álgebra', carrera_id: 3, num_asesores: 2 },
  { materia_id: 2, nombre: 'Cálculo', carrera_id: 3, num_asesores: 1 },
  { materia_id: 3, nombre: 'Física', carrera_id: 9, num_asesores: 1 },
]

function montar() {
  vi.spyOn(api, 'useOferta').mockReturnValue({
    data: OFERTA, isPending: false,
  } as ReturnType<typeof api.useOferta>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(
    new Map([
      [3, { id: 3, nombre: 'Actuaría' } as never],
      [9, { id: 9, nombre: 'Física' } as never],
    ]),
  )
  render(
    <MemoryRouter initialEntries={['/asesorias/nueva']}>
      <Routes>
        <Route path="/asesorias/nueva" element={<OfertaAsesorias />} />
        <Route path="/asesorias/nueva/:materiaId" element={<p>wizard</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('OfertaAsesorias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista las materias con su número de asesores', () => {
    montar()
    expect(screen.getByText('Álgebra')).toBeInTheDocument()
    expect(screen.getByText('Física')).toBeInTheDocument()
  })

  it('filtra por búsqueda de nombre', async () => {
    montar()
    await userEvent.type(screen.getByLabelText('Buscar materia'), 'álge')
    expect(screen.getByText('Álgebra')).toBeInTheDocument()
    expect(screen.queryByText('Cálculo')).not.toBeInTheDocument()
  })

  it('navega al wizard al elegir una materia', async () => {
    montar()
    await userEvent.click(screen.getByText('Álgebra'))
    expect(screen.getByText('wizard')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/OfertaAsesorias.test.tsx`
Expected: FAIL — `OfertaAsesorias` no existe.

- [ ] **Step 3: Implementar la pantalla**

Crear `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx`:

```tsx
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOferta } from '../api'
import { useMapaCarreras } from '../../catalogo/api'
import { Skeleton } from '../../../components/ui/Skeleton'

export function OfertaAsesorias() {
  const navigate = useNavigate()
  const { data: oferta = [], isPending } = useOferta()
  const mapaCarreras = useMapaCarreras()
  const [carrera, setCarrera] = useState<number | null>(null)
  const [busqueda, setBusqueda] = useState('')

  const filtradas = useMemo(
    () =>
      oferta.filter(
        (m) =>
          (carrera === null || m.carrera_id === carrera) &&
          m.nombre.toLowerCase().includes(busqueda.toLowerCase()),
      ),
    [oferta, carrera, busqueda],
  )

  const carrerasEnOferta = useMemo(() => {
    const ids = [...new Set(oferta.map((m) => m.carrera_id))]
    return ids.map((id) => ({ id, nombre: mapaCarreras.get(id)?.nombre ?? `Carrera #${id}` }))
  }, [oferta, mapaCarreras])

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={() => navigate('/asesorias')} className="w-fit text-sm text-primary">
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">Nueva asesoría</h1>

      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="filtro-carrera" className="text-xs text-on-surface-variant">Carrera</label>
          <select
            id="filtro-carrera"
            value={carrera ?? ''}
            onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
            className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          >
            <option value="">Todas</option>
            {carrerasEnOferta.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="busqueda-oferta" className="text-xs text-on-surface-variant">Buscar materia</label>
          <input
            id="busqueda-oferta"
            type="text"
            placeholder="Escribe para filtrar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
          />
        </div>
      </div>

      {isPending ? (
        <ul className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14" />)}
        </ul>
      ) : filtradas.length === 0 ? (
        <p className="text-sm text-on-surface-variant">No hay materias con asesores disponibles.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {filtradas.map((m) => (
            <li key={m.materia_id}>
              <button
                type="button"
                onClick={() => navigate(`/asesorias/nueva/${m.materia_id}`)}
                className="foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
              >
                <span className="truncate text-sm font-medium text-on-surface" title={m.nombre}>{m.nombre}</span>
                <span className="ml-3 shrink-0 text-xs text-on-surface-variant">
                  {m.num_asesores} asesor{m.num_asesores === 1 ? '' : 'es'}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/OfertaAsesorias.test.tsx`
Expected: PASS (3 casos).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/screens/OfertaAsesorias.tsx frontend/src/features/asesorias/screens/OfertaAsesorias.test.tsx
git commit -m "[feat][frontend] pantalla de oferta de asesorias con filtro por carrera y busqueda

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 7: Wizard de agendado `AgendarAsesoria.tsx` (alumno)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx`
- Test: `frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx`

**Interfaces:**
- Consumes: `useParams().materiaId`, `useAsesoresDeMateria`, `useDisponibilidadDeAsesor`, `agruparPorDia`, `useAgendarAsesoria`, `useAuth().user.perfil_alumno.carrera`, `useMapaCarreras`/`useMapaMaterias`, `Dialogo`, `ApiError`, `primerMensajeDeError`.
- Produces: componente `AgendarAsesoria`. Stepper de una ruta con paso derivado del estado: `asesor → dia → bloque → carrera`. *Atrás* retrocede un paso (o sale a `/asesorias`). Confirmación con `Dialogo` de 2 acciones. `POST` con `{disponibilidad, fecha, materia, carrera}`. `onSuccess` → `navigate('/asesorias', { state: { nuevaAsesoriaId } })`. `409` → mensaje y vuelta al paso de día.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx`:

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AgendarAsesoria } from './AgendarAsesoria'
import * as api from '../api'
import * as auth from '../../../auth/AuthContext'
import * as catalogo from '../../catalogo/api'
import { ApiError } from '../../../api/client'
import type { AsesorDisponible, SlotDisponibilidad } from '../../../api/types'

const ASESORES: AsesorDisponible[] = [
  { registro_id: 7, asesor_nombre: 'Ana López', area_nombre: 'Matemáticas', formatos: ['virtual'] },
]
const SLOTS: SlotDisponibilidad[] = [
  {
    registro_id: 7, asesor_nombre: 'Ana López', disponibilidad_id: 41, fecha: '2026-08-10',
    hora_inicio: '10:00:00', hora_fin: '10:30:00', formato: 'virtual', ubicacion: '', liga_virtual: 'https://x',
  },
]

function mockComun(mutateImpl: ReturnType<typeof vi.fn>) {
  vi.spyOn(api, 'useAsesoresDeMateria').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAsesoresDeMateria>)
  vi.spyOn(api, 'useDisponibilidadDeAsesor').mockReturnValue({
    data: SLOTS, isPending: false,
  } as ReturnType<typeof api.useDisponibilidadDeAsesor>)
  vi.spyOn(api, 'useAgendarAsesoria').mockReturnValue({
    mutate: mutateImpl, isPending: false,
  } as unknown as ReturnType<typeof api.useAgendarAsesoria>)
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: { perfil_alumno: { id: 1, carrera: 3, carrera_nombre: 'Actuaría' } },
    status: 'authenticated',
  } as unknown as ReturnType<typeof auth.useAuth>)
  vi.spyOn(catalogo, 'useMapaCarreras').mockReturnValue(new Map([[3, { id: 3, nombre: 'Actuaría' } as never]]))
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[12, { id: 12, nombre: 'Álgebra' } as never]]))
}

function montar() {
  render(
    <MemoryRouter initialEntries={['/asesorias/nueva/12']}>
      <Routes>
        <Route path="/asesorias/nueva/:materiaId" element={<AgendarAsesoria />} />
        <Route path="/asesorias" element={<p>lista de asesorías</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

async function avanzarHastaConfirmar() {
  await userEvent.click(screen.getByText('Ana López'))
  await userEvent.click(screen.getByText(/10 de agosto/i))
  await userEvent.click(screen.getByText('10:00–10:30'))
  await userEvent.click(screen.getByRole('button', { name: 'Agendar' }))
}

describe('AgendarAsesoria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('elegir asesor avanza al paso de día', async () => {
    mockComun(vi.fn())
    montar()
    await userEvent.click(screen.getByText('Ana López'))
    expect(screen.getByText('Elige un día')).toBeInTheDocument()
  })

  it('confirmar dispara el POST con el payload correcto', async () => {
    const mutate = vi.fn()
    mockComun(mutate)
    montar()
    await avanzarHastaConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Agendar' })) // botón del diálogo
    expect(mutate).toHaveBeenCalledWith(
      { disponibilidad: 41, fecha: '2026-08-10', materia: 12, carrera: 3 },
      expect.anything(),
    )
  })

  it('un 409 regresa al paso de día', async () => {
    const mutate = vi.fn((_payload, { onError }) => onError(new ApiError(409, { detail: 'tomado' })))
    mockComun(mutate)
    montar()
    await avanzarHastaConfirmar()
    await userEvent.click(screen.getByRole('button', { name: 'Agendar' }))
    expect(await screen.findByText('Elige un día')).toBeInTheDocument()
    expect(screen.getByText(/ya fue tomado/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/AgendarAsesoria.test.tsx`
Expected: FAIL — `AgendarAsesoria` no existe.

- [ ] **Step 3: Implementar el wizard**

Crear `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx`:

```tsx
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAsesoresDeMateria, useDisponibilidadDeAsesor, useAgendarAsesoria } from '../api'
import { agruparPorDia } from '../logica'
import { useAuth } from '../../../auth/AuthContext'
import { useMapaCarreras, useMapaMaterias } from '../../catalogo/api'
import { Dialogo } from '../../../components/ui/Dialogo'
import { Skeleton } from '../../../components/ui/Skeleton'
import { primerMensajeDeError } from '../../../api/errores'
import { ApiError } from '../../../api/client'
import type { AsesorDisponible, SlotDisponibilidad } from '../../../api/types'

const FORMATEADOR_DIA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })

export function AgendarAsesoria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const idMateria = Number(materiaId)
  const navigate = useNavigate()
  const { user } = useAuth()
  const mapaCarreras = useMapaCarreras()
  const mapaMaterias = useMapaMaterias()

  const { data: asesores = [], isPending: cargandoAsesores } = useAsesoresDeMateria(idMateria)
  const [registroId, setRegistroId] = useState<number | null>(null)
  const { data: slots = [], isPending: cargandoSlots } = useDisponibilidadDeAsesor(
    registroId !== null ? idMateria : null,
    registroId,
  )
  const dias = useMemo(() => agruparPorDia(slots), [slots])

  const [fecha, setFecha] = useState<string | null>(null)
  const [slot, setSlot] = useState<SlotDisponibilidad | null>(null)
  const carreraAlumno = user?.perfil_alumno?.carrera ?? null
  const [carrera, setCarrera] = useState<number | null>(carreraAlumno)
  const [confirmando, setConfirmando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const agendar = useAgendarAsesoria()

  const paso = registroId === null ? 'asesor' : fecha === null ? 'dia' : slot === null ? 'bloque' : 'carrera'

  function volver() {
    setError(null)
    if (slot !== null) return setSlot(null)
    if (fecha !== null) return setFecha(null)
    if (registroId !== null) return setRegistroId(null)
    navigate('/asesorias')
  }

  function confirmar() {
    if (slot === null || carrera === null || fecha === null) return
    agendar.mutate(
      { disponibilidad: slot.disponibilidad_id, fecha, materia: idMateria, carrera },
      {
        onSuccess: (asesoria) => {
          setConfirmando(false)
          navigate('/asesorias', { state: { nuevaAsesoriaId: asesoria.id } })
        },
        onError: (err) => {
          setConfirmando(false)
          if (err instanceof ApiError && err.status === 409) {
            setError('Ese horario ya fue tomado. Elige otro día.')
            setSlot(null)
            setFecha(null)
          } else {
            setError(primerMensajeDeError(err))
          }
        },
      },
    )
  }

  const slotsDelDia = dias.find((d) => d.fecha === fecha)?.slots ?? []

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={volver} className="w-fit text-sm text-primary">← Atrás</button>
      <h1 className="text-lg font-semibold text-on-background">
        {mapaMaterias.get(idMateria)?.nombre ?? `Materia #${idMateria}`}
      </h1>

      {error && <p role="alert" className="text-xs text-error">{error}</p>}

      {paso === 'asesor' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un asesor</h2>
          {cargandoAsesores ? (
            <Skeleton className="h-14" />
          ) : asesores.length === 0 ? (
            <p className="text-sm text-on-surface-variant">Esta materia no tiene asesores disponibles.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {asesores.map((a) => (
                <li key={a.registro_id}>
                  <BotonAsesor asesor={a} onClick={() => setRegistroId(a.registro_id)} />
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {paso === 'dia' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un día</h2>
          {cargandoSlots ? (
            <Skeleton className="h-14" />
          ) : dias.length === 0 ? (
            <p className="text-sm text-on-surface-variant">Este asesor no tiene horarios en las próximas dos semanas.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {dias.map((d) => (
                <li key={d.fecha}>
                  <button
                    type="button"
                    onClick={() => setFecha(d.fecha)}
                    className="foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
                  >
                    <span className="text-sm text-on-surface">
                      {FORMATEADOR_DIA.format(new Date(`${d.fecha}T00:00:00`))}
                    </span>
                    <span className="text-xs text-on-surface-variant">
                      {d.slots.length} bloque{d.slots.length === 1 ? '' : 's'}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {paso === 'bloque' && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Elige un bloque</h2>
          <ul className="flex flex-col gap-2">
            {slotsDelDia.map((s) => (
              <li key={s.disponibilidad_id}>
                <button
                  type="button"
                  onClick={() => setSlot(s)}
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
                >
                  <span className="text-sm text-on-surface">
                    {s.hora_inicio.slice(0, 5)}–{s.hora_fin.slice(0, 5)}
                  </span>
                  <span className="text-xs text-on-surface-variant">
                    {s.formato === 'virtual' ? 'Virtual' : s.ubicacion || 'Presencial'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {paso === 'carrera' && slot !== null && fecha !== null && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-on-surface">Confirma tu asesoría</h2>
          <dl className="grid grid-cols-2 gap-y-1 text-sm text-on-surface-variant">
            <dt>Día</dt>
            <dd>{FORMATEADOR_DIA.format(new Date(`${fecha}T00:00:00`))}</dd>
            <dt>Hora</dt>
            <dd>{slot.hora_inicio.slice(0, 5)}</dd>
            <dt>Asesor</dt>
            <dd>{slot.asesor_nombre}</dd>
          </dl>

          <div className="flex flex-col gap-1">
            <label htmlFor="carrera-agendar" className="text-xs text-on-surface-variant">Carrera</label>
            <select
              id="carrera-agendar"
              value={carrera ?? ''}
              onChange={(e) => setCarrera(e.target.value === '' ? null : Number(e.target.value))}
              className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
            >
              {carreraAlumno !== null && (
                <option value={carreraAlumno}>
                  {mapaCarreras.get(carreraAlumno)?.nombre ?? `Carrera #${carreraAlumno}`}
                </option>
              )}
            </select>
          </div>

          <button
            type="button"
            onClick={() => setConfirmando(true)}
            disabled={carrera === null}
            className="foco-visible flex min-h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-on-primary disabled:opacity-60"
          >
            Agendar
          </button>

          <Dialogo
            abierto={confirmando}
            titulo="Confirmar asesoría"
            descripcion={`${FORMATEADOR_DIA.format(new Date(`${fecha}T00:00:00`))} · ${slot.hora_inicio.slice(0, 5)}`}
            onCerrar={() => setConfirmando(false)}
            acciones={[{ etiqueta: 'Agendar', cargando: agendar.isPending, onClick: confirmar }]}
          />
        </section>
      )}
    </main>
  )
}

function BotonAsesor({ asesor, onClick }: { asesor: AsesorDisponible; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg bg-surface-container px-4 py-3 text-left"
    >
      <span className="text-sm font-medium text-on-surface">{asesor.asesor_nombre}</span>
      <span className="text-xs text-on-surface-variant">
        {asesor.area_nombre} · {asesor.formatos.map((f) => (f === 'virtual' ? 'Virtual' : 'Presencial')).join(' / ')}
      </span>
    </button>
  )
}
```

> **Nota para el implementador:** el test confía en que el `Dialogo` muestre un botón "Agendar" al abrirse; hay **dos** botones "Agendar" en el paso carrera cuando el diálogo está abierto (el que lo abre y el del diálogo). El test hace click en `getByRole('button', { name: 'Agendar' })` **antes** de abrir el diálogo (para abrirlo) y luego otra vez; si `getByRole` se queja de múltiples coincidencias, cambia el botón que abre el diálogo a la etiqueta "Agendar…" o usa `getAllByRole(...).at(-1)`. Verifica el comportamiento real al correr el test y ajusta la etiqueta si hace falta (mantén "Agendar" como acción del diálogo, que es la que dispara el `POST`).

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/AgendarAsesoria.test.tsx`
Expected: PASS (3 casos). Si hay ambigüedad de botón "Agendar", aplica el ajuste de la nota y vuelve a correr.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/asesorias/screens/AgendarAsesoria.tsx frontend/src/features/asesorias/screens/AgendarAsesoria.test.tsx
git commit -m "[feat][frontend] wizard de agendado de asesoria (asesor -> dia -> bloque -> carrera)

- stepper de una ruta; carrera autoseleccionada (deuda 0008)
- 409 regresa al paso de dia; post-agendado navega con nuevaAsesoriaId

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 8: Ruteo en `App.tsx`

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `RutaDeAsesorias` (Task 3), `Asesorias` (Task 5), `OfertaAsesorias` (Task 6), `AgendarAsesoria` (Task 7), `RutaDeAsesor` (existente).
- Produces: `/asesorias` bajo `RutaDeAsesorias`; nuevas rutas `/asesorias/nueva` y `/asesorias/nueva/:materiaId` bajo `RutaDeAsesorias`; `/asesorias/materias`, `/asesorias/horario`, `/asesorias/:id` siguen bajo `RutaDeAsesor`.

- [ ] **Step 1: Actualizar imports y rutas**

En `frontend/src/App.tsx`:

1. Imports (añadir/ajustar):

```tsx
import { RutaDeAsesor, RutaDeAsesorias } from './auth/RutaProtegida'
import { Asesorias } from './features/asesorias/screens/Asesorias'
import { OfertaAsesorias } from './features/asesorias/screens/OfertaAsesorias'
import { AgendarAsesoria } from './features/asesorias/screens/AgendarAsesoria'
```

2. Reemplazar el bloque de rutas de asesorías por:

```tsx
        <Route
          path="/asesorias"
          element={
            <RutaDeAsesorias>
              <Asesorias />
            </RutaDeAsesorias>
          }
        />
        <Route
          path="/asesorias/nueva"
          element={
            <RutaDeAsesorias>
              <OfertaAsesorias />
            </RutaDeAsesorias>
          }
        />
        <Route
          path="/asesorias/nueva/:materiaId"
          element={
            <RutaDeAsesorias>
              <AgendarAsesoria />
            </RutaDeAsesorias>
          }
        />
        <Route
          path="/asesorias/materias"
          element={
            <RutaDeAsesor>
              <MisMaterias />
            </RutaDeAsesor>
          }
        />
        <Route
          path="/asesorias/horario"
          element={
            <RutaDeAsesor>
              <MiHorario />
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
```

(React Router v6 rankea por especificidad: la estática `/asesorias/nueva` gana sobre `/asesorias/:id`, sin importar el orden.)

- [ ] **Step 2: Build**

Run: `npm run build`
Expected: PASS — todas las importaciones resuelven.

- [ ] **Step 3: Correr toda la suite y lint**

Run: `npm test && npm run lint`
Expected: PASS — sin regresiones; los tests de `MisMaterias`, `MiHorario`, `RutaProtegida`, `Asesorias`, `OfertaAsesorias`, `AgendarAsesoria`, `TarjetaAsesoria` y `logica` verdes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "[feat][frontend] rutear la vista unificada bajo RutaDeAsesorias y agregar oferta/wizard

- /asesorias -> RutaDeAsesorias; nuevas rutas /asesorias/nueva y /asesorias/nueva/:materiaId
- subrutas asesor-only (/materias, /horario, /:id) conservan RutaDeAsesor

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Self-Review

**Spec coverage** (contra `2026-08-08-asesorias-alumno-frontend-design.md`):
- Pantalla 1 (vista unificada, encabezado por rol, historial por semestre) → Task 5. Pantalla 2 (oferta con filtro+búsqueda) → Task 6. Pantalla 3 (wizard stepper una-ruta con 4 pasos, `Dialogo` 2 acciones, `409`→día) → Task 7. Post-agendado (invalida `['asesorias']`, navega a Próximas, foco+`pulso-exito`) → `useAgendarAsesoria` (Task 1) + `destacar` (Task 4) + navegación con `state` (Task 7) + lectura de `nuevaAsesoriaId` (Task 5).
- Guard `RutaDeAsesorias` → Task 3. Tarjeta contraparte por rol + sin notas → Task 4. Hooks nuevos y tipos → Task 1. Lógica pura `agruparPorDia` → Task 2. Rutas en `App.tsx` → Task 8.
- Sección *Testing* del spec: vista unificada por rol (Task 5), guard (Task 3), tarjeta (Task 4), oferta filtro/búsqueda/navegación (Task 6), wizard avance/confirm/`409` (Task 7), `agruparPorDia` (Task 2). Cubiertos.

**Desviaciones documentadas:**
- Filtrado de oferta en **cliente** (`useMemo`, patrón `DialogoAgregarMateria`) en vez de servidor — explícitamente permitido por el spec (§ tabla de arquitectura, "servidor o cliente según volumen"). Por eso `useOferta()` no toma `filtros`.
- La tarjeta del **alumno no navega** a detalle: `/asesorias/:id`/`DetalleAsesoria` sigue asesor-only (spec §Out of scope: DetalleAsesoria no se rediseña). Documentado en File Structure y Task 4.

**Placeholder scan:** ningún paso usa "TBD/manejo apropiado/similar a Task N". Todo el código de componentes y tests está completo. La única nota de juicio (ambigüedad del botón "Agendar" del diálogo) está marcada explícitamente con la instrucción de verificar al correr el test.

**Type/nombre consistency:** `MateriaOferta`/`AsesorDisponible`/`SlotDisponibilidad`/`DiaDisponible`, `useOferta`/`useAsesoresDeMateria`/`useDisponibilidadDeAsesor`/`useAgendarAsesoria`/`useSemestres`/`useAsesoriasDeSemestre`, `RutaDeAsesorias`, `Asesorias`, `OfertaAsesorias`, `AgendarAsesoria`, `agruparPorDia`, `nuevaAsesoriaId`, `destacar` y `PayloadAgendar` (`{disponibilidad, fecha, materia, carrera}`) se usan idénticos entre tasks. Los nombres de campo (`registro_id`, `asesor_nombre`, `area_nombre`, `formatos`, `disponibilidad_id`, `hora_fin`) coinciden con el plan de API gemelo.
