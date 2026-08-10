# Vista de administración SAE de Asesorías (frontend, solo lectura) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Área SAE de solo lectura bajo `/sae/*`: supervisar asesorías agendadas e históricas de todo el sistema, consultar la oferta sin agendar, y navegar un directorio de asesores con su detalle de materias/horario reusando las pantallas del asesor en modo solo-lectura.

**Architecture:** Rol `'sae'` + guarda `RutaDeSAE` (espejo de `RutaDeAsesor`). Árbol propio `/sae/*` en `App.tsx`. Hooks admin nuevos en `features/asesorias/api.ts` sobre `/api/asesorias/admin/*`. Pantallas nuevas `AdminAsesorias`, `AdminOfertaMateria`, `AdminAsesores`, `AdminAsesorDetalle`. Componentes existentes se parametrizan: `TarjetaAsesoria` gana `admin`, `OfertaAsesorias` gana destino configurable, `MisMaterias`/`MiHorario` ganan `soloLectura` + fuente de datos externa.

**Tech Stack:** React 19 + TypeScript + Vite, TanStack Query v5, React Router v7, Vitest + Testing Library (jsdom), Tailwind v4 + tokens MD3.

**Spec:** [`2026-08-09-asesorias-sae-admin-frontend-design.md`](../specs/2026-08-09-asesorias-sae-admin-frontend-design.md) · **ADR:** [0024](../../decisions/0024-asesorias-sae-admin-frontend.md) · **API gemela:** [`2026-08-09-asesorias-sae-admin-api-design.md`](../specs/2026-08-09-asesorias-sae-admin-api-design.md) / [ADR 0023](../../decisions/0023-asesorias-sae-admin-api.md)

## Global Constraints

- **Comandos** (siempre desde `frontend/`): test puntual `npx vitest run <ruta>`; suite `npm test`; build `npm run build`; lint `npm run lint`.
- **`@testing-library/user-event` NO está instalado.** Los tests usan `fireEvent` de `@testing-library/react`. No agregarlo.
- **Sin dependencias nuevas** ([ADR 0014](../../decisions/0014-tokens-logo-iconos-frontend.md) / [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)): TanStack Query, CSS puro, componentes de `components/ui/` existentes.
- **Estado de servidor:** TanStack Query con `apiGet` de `src/api/client.ts` y **query keys planas** (`['admin', 'asesorias', filtros]`). Todos los endpoints de este plan son `GET`; no hay mutaciones.
- **Tests:** Vitest + Testing Library, test colocado junto al archivo, hooks mockeados con `vi.spyOn(modulo, 'hook')`, factories de `src/test/factories.ts`. En jsdom los imports de componentes son **relativos** (`../../../components/ui/...`), no el alias `@/`.
- **Accesibilidad/estilo:** toque mínimo `min-h-11` (44×44), `.foco-visible` en todo interactivo, `truncate`+`title` en nombres de materia, motion sólo con clases CSS existentes (`entrada-lista`, `pulso-exito`) que ya respetan `@media (prefers-reduced-motion)`.
- **Sólo lectura:** ninguna pantalla `/sae/*` monta mutaciones, diálogos de escritura ni botones de agendar/cancelar/editar.
- **Deuda referenciada, no nueva:** paginación de listados admin → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md); alta de `PerfilSAE` sólo por Django admin → [deuda 0014](../../technical-debt/0014-alta-perfil-sae-solo-admin.md).
- **Commits:** `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>`.

## Nota de proceso OBLIGATORIA — gate de mockup

La spec y el ADR 0024 exigen **flujo de aprobación por artefactos (mockups) antes de implementar** toda pantalla/componente nuevo.

**Tasks con gate (arrancan con un paso de mockup + aprobación del usuario, y NO se escribe código antes de la aprobación):** Task 6 (`AdminAsesorias`), Task 8 (`AdminOfertaMateria`), Task 10 (`AdminAsesores`), Task 11 (`AdminAsesorDetalle`).

**Tasks sin gate (modifican componentes existentes):** Task 1 (`rol.ts`, `RutaProtegida.tsx`, `types.ts`, `factories.ts`), Task 2 (`Home.tsx`), Task 3 (`types.ts`, `api.ts`), Task 4 (`logica.ts`), Task 5 (`TarjetaAsesoria.tsx`), Task 7 (`OfertaAsesorias.tsx`), Task 9 (`MisMaterias.tsx` / `MiHorario.tsx`), Task 12 (`App.tsx`).

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `frontend/src/api/types.ts` | Tipos del contrato | Modificar: `'sae'` en `RolUsuario`, `Disponibilidad.registro` opcional; crear `MateriaResumen`, `AsesoriaAdmin`, `AsesorDirectorio`, `AsesorDetalle`, `AlumnoBusqueda` |
| `frontend/src/auth/rol.ts` | Hooks de rol | Añadir `useEsMiembroSAE` |
| `frontend/src/auth/RutaProtegida.tsx` | Guardas de ruta | Añadir `RutaDeSAE` |
| `frontend/src/test/factories.ts` | Factories de test | Añadir `usuarioSAE` |
| `frontend/src/screens/Home.tsx` | Hub de servicios | Modificar: tarjeta condicional SAE → `/sae/asesorias` |
| `frontend/src/features/asesorias/api.ts` | Hooks de datos | Añadir `rutaAdminAsesorias`, `useAdminAsesorias`, `useAdminSemestres`, `useAdminAsesores`, `useAdminAsesor`, `useBuscarAlumnos`; parámetro `habilitado` en `useMisRegistros`/`useRegistroDelSemestre`/`useMisDisponibilidades` |
| `frontend/src/features/asesorias/logica.ts` | Lógica pura | Modificar: `proximas`/`historial` genéricos sobre la forma mínima |
| `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx` | Tarjeta de sesión | Modificar: prop `admin` (ambos nombres + `notas`, no interactiva) |
| `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx` | Oferta | Modificar: `titulo`, `rutaVolver`, `etiquetaVolver`, `baseRutaMateria` |
| `frontend/src/features/asesorias/screens/MisMaterias.tsx` | Materias del asesor | Modificar: `soloLectura`, `materias`, `semestre` |
| `frontend/src/features/asesorias/screens/MiHorario.tsx` | Horario del asesor | Modificar: `soloLectura`, `disponibilidades` |
| `frontend/src/features/asesorias/screens/AdminAsesorias.tsx` | Agendadas + histórico SAE | Crear |
| `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx` | Detalle de materia (consulta) | Crear |
| `frontend/src/features/asesorias/screens/AdminAsesores.tsx` | Directorio de asesores | Crear |
| `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx` | Detalle de asesor | Crear |
| `frontend/src/App.tsx` | Ruteo | Modificar: 5 rutas `/sae/*` bajo `RutaDeSAE` |

**Decisiones de alcance registradas aquí (divergencias resueltas frente a la spec):**

1. **No se crea `AdminOferta.tsx`.** La spec lo deja opcional ("*+ `AdminOferta.tsx` si se prefiere wrapper*"). Se usa `OfertaAsesorias` con props directamente en la ruta de `App.tsx` — un archivo menos, cero lógica duplicada.
2. **El chip `activo` del directorio NO usa `InsigniaEstado`.** `InsigniaEstado` está tipado a `EstadoAsesoria` (`agendada`/`realizada`/`cancelada`); no admite un booleano. Se usa el mismo chip de píldora que ya emplea la leyenda de `MiHorario`.
3. **`AsesorDetalle.disponibilidades` se tipa como `Disponibilidad[]`.** El endpoint admin no devuelve `registro` (y sí devuelve `hora_fin`, que el frontend ignora), así que `Disponibilidad.registro` pasa a opcional. Nadie lee ese campo hoy (verificado repo-wide).
4. **`AdminAsesorias` reusa `proximas`/`historial` de `logica.ts`**, que por eso se vuelven genéricos: `AsesoriaAdmin` no es asignable a `Asesoria` (le faltan `alumno`, `disponibilidad`, `creado_en`).

---

## Task 1: Rol `'sae'`, `useEsMiembroSAE`, `RutaDeSAE` y factory `usuarioSAE`

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/auth/rol.ts`
- Modify: `frontend/src/auth/RutaProtegida.tsx`
- Modify: `frontend/src/test/factories.ts`
- Test: `frontend/src/auth/rol.test.tsx`, `frontend/src/auth/RutaProtegida.test.tsx`

**Interfaces:**
- Consumes: `useAuth().roles`, `useAuth().status`.
- Produces: `RolUsuario` incluye `'sae'`; `useEsMiembroSAE(): boolean`; `RutaDeSAE({ children }: { children: ReactNode })` — autenticado + `sae` pasa; autenticado sin `sae` → `/home`; sin sesión → `/login`. `usuarioSAE(overrides?: Partial<AuthUser>): AuthUser`.

- [ ] **Step 1: Añadir la factory `usuarioSAE`**

Añadir al final de `frontend/src/test/factories.ts`:

```typescript
/** Usuario con el rol de miembro de la SAE (ADR 0023/0024). */
export function usuarioSAE(overrides: Partial<AuthUser> = {}): AuthUser {
  return usuarioDePrueba({ roles: ['sae'], ...overrides })
}
```

- [ ] **Step 2: Escribir los tests que fallan (rol)**

En `frontend/src/auth/rol.test.tsx`, cambiar la línea de import de `./rol` y la de factories a:

```typescript
import { useEsAlumno, useEsAsesor, useEsMiembroSAE } from './rol'
```

```typescript
import { usuarioDePrueba, usuarioSAE } from '../test/factories'
```

Y añadir al final del archivo:

```tsx
function SondaSAE() {
  const esSAE = useEsMiembroSAE()
  return <div data-testid="sae">{`sae=${esSAE}`}</div>
}

describe('useEsMiembroSAE', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reconoce al miembro de la SAE por el rol del contexto', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioSAE())
    render(
      <AuthProvider>
        <SondaSAE />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('sae')).toHaveTextContent('sae=true')
    })
  })

  it('no reconoce como SAE a quien no tiene el rol', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))
    render(
      <AuthProvider>
        <SondaSAE />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('sae')).toHaveTextContent('sae=false')
    })
  })
})
```

- [ ] **Step 3: Escribir los tests que fallan (guarda)**

En `frontend/src/auth/RutaProtegida.test.tsx`, cambiar las líneas de import a:

```typescript
import { RutaDeAsesor, RutaDeAsesorias, RutaDeSAE } from './RutaProtegida'
```

```typescript
import { usuarioDePrueba, usuarioSAE } from '../test/factories'
```

Y añadir al final del archivo:

```tsx
function montarSAE() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/sae/asesorias']}>
        <Routes>
          <Route
            path="/sae/asesorias"
            element={
              <RutaDeSAE>
                <p>área SAE</p>
              </RutaDeSAE>
            }
          />
          <Route path="/home" element={<p>pantalla home</p>} />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaDeSAE', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar al miembro de la SAE', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioSAE())
    montarSAE()
    expect(await screen.findByText('área SAE')).toBeInTheDocument()
  })

  it('manda a Home a quien tiene sesión pero no es SAE', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ roles: ['alumno', 'asesor_academico'] }),
    )
    montarSAE()
    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('área SAE')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    montarSAE()
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

Run: `npx vitest run src/auth/rol.test.tsx src/auth/RutaProtegida.test.tsx`
Expected: FAIL — `useEsMiembroSAE` y `RutaDeSAE` no están exportados.

- [ ] **Step 5: Añadir `'sae'` a `RolUsuario`**

En `frontend/src/api/types.ts`, reemplazar la línea 4 por:

```typescript
export type RolUsuario = 'alumno' | 'academico' | 'asesor_academico' | 'sae'
```

- [ ] **Step 6: Implementar `useEsMiembroSAE`**

Añadir al final de `frontend/src/auth/rol.ts`:

```typescript
/**
 * Miembro de la SAE (ADR 0023): el backend deriva el rol de la existencia de
 * `PerfilSAE`, igual que los demás roles. Habilita el área `/sae/*`.
 */
export function useEsMiembroSAE(): boolean {
  return useAuth().roles.includes('sae')
}
```

- [ ] **Step 7: Implementar `RutaDeSAE`**

En `frontend/src/auth/RutaProtegida.tsx`, cambiar la línea 4 por:

```typescript
import { useEsAsesor, useEsAlumno, useEsMiembroSAE } from './rol'
```

Y añadir al final del archivo:

```tsx
export function RutaDeSAE({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esMiembroSAE = useEsMiembroSAE()
  const location = useLocation()

  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esMiembroSAE) return <Navigate to="/home" replace />

  return <>{children}</>
}
```

- [ ] **Step 8: Correr los tests y verificar que pasan**

Run: `npx vitest run src/auth/rol.test.tsx src/auth/RutaProtegida.test.tsx`
Expected: PASS (6 casos de `rol` + 11 de `RutaProtegida`).

- [ ] **Step 9: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/auth/rol.ts frontend/src/auth/rol.test.tsx frontend/src/auth/RutaProtegida.tsx frontend/src/auth/RutaProtegida.test.tsx frontend/src/test/factories.ts
git commit -m "[feat][frontend] rol sae, useEsMiembroSAE y guarda RutaDeSAE

- 'sae' en RolUsuario; hook de rol espejo de useEsAsesor/useEsAlumno
- RutaDeSAE: no autenticado -> /login, autenticado sin sae -> /home
- factory usuarioSAE para los tests

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Tarjeta de servicio SAE en `Home`

**Files:**
- Modify: `frontend/src/screens/Home.tsx`
- Test: `frontend/src/screens/Home.test.tsx` (crear)

**Interfaces:**
- Consumes: `useEsMiembroSAE()` (Task 1), `services` de `data/services.ts`, `IconTutorias` de `components/icons/ServiceIcons`.
- Produces: `Home` renderiza una tarjeta extra "Asesorías · SAE" que navega a `/sae/asesorias`, **sólo** cuando `useEsMiembroSAE()` es `true`.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/screens/Home.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Home } from './Home'
import * as rol from '../auth/rol'

function montar(esMiembroSAE: boolean) {
  vi.spyOn(rol, 'useEsMiembroSAE').mockReturnValue(esMiembroSAE)
  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Home', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra la tarjeta de la SAE al miembro de la SAE', () => {
    montar(true)
    expect(screen.getByRole('button', { name: 'Asesorías · SAE' })).toBeInTheDocument()
  })

  it('no muestra la tarjeta de la SAE a quien no tiene el rol', () => {
    montar(false)
    expect(screen.queryByRole('button', { name: 'Asesorías · SAE' })).not.toBeInTheDocument()
  })

  it('la tarjeta de la SAE navega al área SAE', () => {
    montar(true)
    fireEvent.click(screen.getByRole('button', { name: 'Asesorías · SAE' }))
    expect(screen.getByText('área SAE')).toBeInTheDocument()
  })

  it('sigue mostrando el resto de servicios', () => {
    montar(false)
    expect(screen.getByText('Becas')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/screens/Home.test.tsx`
Expected: FAIL — no existe la tarjeta "Asesorías · SAE".

- [ ] **Step 3: Implementar la tarjeta condicional**

Reemplazar el contenido completo de `frontend/src/screens/Home.tsx`:

```tsx
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { IconTutorias } from '../components/icons/ServiceIcons'
import { services } from '../data/services'
import { useEsMiembroSAE } from '../auth/rol'

export function Home() {
  const navigate = useNavigate()
  const esMiembroSAE = useEsMiembroSAE()

  return (
    <main className="min-h-svh px-4 pb-8">
      <header className="flex items-center gap-2 py-4">
        <Logo className="h-7 w-7 text-primary" />
        <span className="text-base font-semibold">Atenea</span>
        <span className="flex-1" />
        <button type="button" aria-label="Menú" className="flex h-9 w-9 items-center justify-center text-on-background">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="h-5 w-5">
            <line x1="4" y1="7" x2="20" y2="7" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="17" x2="20" y2="17" />
          </svg>
        </button>
      </header>

      <p className="pb-4 text-sm text-on-surface-variant">Hola</p>

      <div className="grid grid-cols-3 gap-3">
        {esMiembroSAE && (
          <button
            type="button"
            onClick={() => navigate('/sae/asesorias')}
            className="foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl bg-secondary-container p-3 text-center text-on-secondary-container"
          >
            <IconTutorias className="h-6 w-6" />
            <span className="text-xs font-semibold leading-tight">Asesorías · SAE</span>
          </button>
        )}
        {services.map(({ id, label, Icon, containerClassName, onContainerClassName }) => (
          <div
            key={id}
            className={`flex flex-col items-center gap-2 rounded-2xl p-3 text-center ${containerClassName} ${onContainerClassName}`}
          >
            <Icon className="h-6 w-6" />
            <span className="text-xs font-semibold leading-tight">{label}</span>
          </div>
        ))}
      </div>
    </main>
  )
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/screens/Home.test.tsx`
Expected: PASS (4 casos).

- [ ] **Step 5: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/Home.tsx frontend/src/screens/Home.test.tsx
git commit -m "[feat][frontend] tarjeta de servicio SAE condicional en Home

- solo con rol sae; navega a /sae/asesorias

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Tipos admin y hooks de datos

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/features/asesorias/api.ts`
- Test: `frontend/src/features/asesorias/api.test.ts` (crear)

**Interfaces:**
- Produces (tipos): `MateriaResumen { id: number; clave: string; nombre: string }`; `AsesoriaAdmin`; `AsesorDirectorio { perfil_id, nombre, area_nombre, activo, num_materias_semestre_vigente }`; `AsesorDetalle { perfil_id, nombre, area_nombre, activo, semestre, materias: MateriaResumen[], disponibilidades: Disponibilidad[] }`; `AlumnoBusqueda { perfil_id, nombre, numero_cuenta }`. `Disponibilidad.registro` pasa a opcional.
- Produces (api): `FiltrosAdminAsesorias { asesor?, alumno?, semestre?, estado? }`; `rutaAdminAsesorias(filtros?): string`; `useAdminAsesorias(filtros?)`; `useAdminSemestres()`; `useAdminAsesores()`; `useAdminAsesor(perfilId, semestre)`; `useBuscarAlumnos(buscar)`; `useMisRegistros(habilitado?)`, `useRegistroDelSemestre(semestre?, habilitado?)`, `useMisDisponibilidades(habilitado?)`.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/features/asesorias/api.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { rutaAdminAsesorias } from './api'

describe('rutaAdminAsesorias', () => {
  it('sin filtros pide el listado por defecto (próximas agendadas)', () => {
    expect(rutaAdminAsesorias()).toBe('/api/asesorias/admin/asesorias/')
  })

  it('traduce el filtro de asesor a ?asesor=', () => {
    expect(rutaAdminAsesorias({ asesor: 7 })).toBe('/api/asesorias/admin/asesorias/?asesor=7')
  })

  it('traduce el filtro de alumno a ?alumno=', () => {
    expect(rutaAdminAsesorias({ alumno: 15 })).toBe('/api/asesorias/admin/asesorias/?alumno=15')
  })

  it('traduce el semestre a ?semestre=', () => {
    expect(rutaAdminAsesorias({ semestre: '20262' })).toBe('/api/asesorias/admin/asesorias/?semestre=20262')
  })

  it('traduce el estado a ?estado=', () => {
    expect(rutaAdminAsesorias({ estado: 'cancelada' })).toBe('/api/asesorias/admin/asesorias/?estado=cancelada')
  })

  it('combina filtros y omite los nulos', () => {
    expect(rutaAdminAsesorias({ asesor: 7, alumno: null, semestre: '20261' })).toBe(
      '/api/asesorias/admin/asesorias/?asesor=7&semestre=20261',
    )
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/api.test.ts`
Expected: FAIL — `rutaAdminAsesorias` no está exportado.

- [ ] **Step 3: Ampliar `types.ts`**

En `frontend/src/api/types.ts`, reemplazar la interfaz `Disponibilidad` completa por:

```typescript
export interface Disponibilidad {
  id: number
  // Opcional: el detalle admin (GET /admin/asesores/{id}/) no expone el
  // registro al que pertenece el bloque. Ninguna pantalla lee este campo;
  // sólo `useCrearDisponibilidad` lo envía.
  registro?: number
  dia_semana: number
  hora_inicio: string
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  activa: boolean
}
```

Y añadir al final del archivo:

```typescript
/** Materia resuelta que devuelve el detalle admin de un asesor. */
export interface MateriaResumen {
  id: number
  clave: string
  nombre: string
}

/**
 * GET /api/asesorias/admin/asesorias/ — vista admin de una sesión.
 * A diferencia de `Asesoria`, expone ambos nombres y `notas` (el SAE sí las
 * ve, ADR 0023), y omite `alumno`, `disponibilidad` y `creado_en`.
 */
export interface AsesoriaAdmin {
  id: number
  estado: EstadoAsesoria
  fecha: string
  hora_inicio: string
  materia: number
  carrera: number
  formato: FormatoAsesoria
  ubicacion: string
  liga_virtual: string
  alumno_nombre: string
  asesor_nombre: string
  asistio: boolean | null
  notas: string
}

/** GET /api/asesorias/admin/asesores/ */
export interface AsesorDirectorio {
  perfil_id: number
  nombre: string
  area_nombre: string
  activo: boolean
  num_materias_semestre_vigente: number
}

/** GET /api/asesorias/admin/asesores/{perfil_id}/?semestre= */
export interface AsesorDetalle {
  perfil_id: number
  nombre: string
  area_nombre: string
  activo: boolean
  semestre: string
  materias: MateriaResumen[]
  // El endpoint manda además `hora_fin`, que el frontend no usa.
  disponibilidades: Disponibilidad[]
}

/** GET /api/asesorias/admin/alumnos/?buscar= */
export interface AlumnoBusqueda {
  perfil_id: number
  nombre: string
  numero_cuenta: string
}
```

- [ ] **Step 4: Ampliar el import de tipos en `api.ts`**

En `frontend/src/features/asesorias/api.ts`, reemplazar el bloque de import de tipos (líneas 3-6) por:

```typescript
import type {
  RegistroAsesor, Disponibilidad, Asesoria, SesionesFuturas,
  MateriaOferta, AsesorDisponible, SlotDisponibilidad, EstadoAsesoria,
  AsesoriaAdmin, AsesorDirectorio, AsesorDetalle, AlumnoBusqueda,
} from '../../api/types'
```

- [ ] **Step 5: Hacer apagables las queries del asesor**

En `frontend/src/features/asesorias/api.ts`, reemplazar `useMisRegistros` y `useRegistroDelSemestre` (líneas 9-27) por:

```typescript
/**
 * `habilitado` permite montar las pantallas del asesor en modo consulta
 * (SAE) sin disparar GET /registros/, que para un no-asesor sería 403.
 */
export function useMisRegistros(habilitado: boolean = true) {
  return useQuery({
    queryKey: ['registros'],
    queryFn: () => apiGet<RegistroAsesor[]>('/api/asesorias/registros/'),
    enabled: habilitado,
  })
}

/**
 * El registro de asesor del semestre pedido (el en curso por default).
 * Las dos pantallas de disponibilidad ("Mis materias" y "Mi horario") lo
 * necesitan igual, así que la búsqueda vive aquí y no en cada una.
 */
export function useRegistroDelSemestre(semestre: string = semestreActual(), habilitado: boolean = true) {
  const { data: registros, isPending } = useMisRegistros(habilitado)
  return {
    registro: registros?.find((r) => r.semestre === semestre) ?? null,
    // Con `enabled: false` TanStack Query reporta `isPending` para siempre;
    // apagada, la query no está cargando nada.
    cargando: habilitado && isPending,
  }
}
```

Y reemplazar `useMisDisponibilidades` (líneas 65-70) por:

```typescript
export function useMisDisponibilidades(habilitado: boolean = true) {
  return useQuery({
    queryKey: ['disponibilidades'],
    queryFn: () => apiGet<Disponibilidad[]>('/api/asesorias/disponibilidades/'),
    enabled: habilitado,
  })
}
```

- [ ] **Step 6: Añadir los hooks admin**

Añadir al final de `frontend/src/features/asesorias/api.ts`:

```typescript
export interface FiltrosAdminAsesorias {
  asesor?: number | null
  alumno?: number | null
  semestre?: string | null
  estado?: EstadoAsesoria | null
}

/**
 * URL del listado admin. Los filtros nulos se omiten; sin ninguno, el
 * backend devuelve las próximas agendadas (ADR 0023).
 */
export function rutaAdminAsesorias(filtros: FiltrosAdminAsesorias = {}): string {
  const params = new URLSearchParams()
  if (filtros.asesor != null) params.set('asesor', String(filtros.asesor))
  if (filtros.alumno != null) params.set('alumno', String(filtros.alumno))
  if (filtros.semestre != null) params.set('semestre', filtros.semestre)
  if (filtros.estado != null) params.set('estado', filtros.estado)
  const query = params.toString()
  return query ? `/api/asesorias/admin/asesorias/?${query}` : '/api/asesorias/admin/asesorias/'
}

export function useAdminAsesorias(filtros: FiltrosAdminAsesorias = {}) {
  return useQuery({
    queryKey: ['admin', 'asesorias', filtros],
    queryFn: () => apiGet<AsesoriaAdmin[]>(rutaAdminAsesorias(filtros)),
  })
}

/** Todos los semestres del sistema con asesorías (distinto de `useSemestres`,
 *  que es por-usuario). Alimenta los subtabs del histórico admin. */
export function useAdminSemestres() {
  return useQuery({
    queryKey: ['admin', 'semestres'],
    queryFn: () => apiGet<string[]>('/api/asesorias/admin/semestres/'),
  })
}

export function useAdminAsesores() {
  return useQuery({
    queryKey: ['admin', 'asesores'],
    queryFn: () => apiGet<AsesorDirectorio[]>('/api/asesorias/admin/asesores/'),
  })
}

/** Detalle read-only de un asesor. `semestre` nulo → el vigente (default del backend). */
export function useAdminAsesor(perfilId: number | null, semestre: string | null = null) {
  return useQuery({
    queryKey: ['admin', 'asesor', perfilId, semestre],
    queryFn: () =>
      apiGet<AsesorDetalle>(
        semestre === null
          ? `/api/asesorias/admin/asesores/${perfilId}/`
          : `/api/asesorias/admin/asesores/${perfilId}/?semestre=${semestre}`,
      ),
    enabled: perfilId !== null,
  })
}

/** Autocompletar de alumno para el filtro de `AdminAsesorias`. */
export function useBuscarAlumnos(buscar: string) {
  return useQuery({
    queryKey: ['admin', 'alumnos', buscar],
    queryFn: () =>
      apiGet<AlumnoBusqueda[]>(`/api/asesorias/admin/alumnos/?buscar=${encodeURIComponent(buscar)}`),
    enabled: buscar.length >= 2,
  })
}
```

- [ ] **Step 7: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/api.test.ts`
Expected: PASS (6 casos).

- [ ] **Step 8: Correr la suite y verificar que no hay regresiones**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/features/asesorias/api.ts frontend/src/features/asesorias/api.test.ts
git commit -m "[feat][frontend] tipos y hooks de la superficie admin SAE

- AsesoriaAdmin, AsesorDirectorio, AsesorDetalle, AlumnoBusqueda, MateriaResumen
- rutaAdminAsesorias + useAdminAsesorias/Semestres/Asesores/Asesor y useBuscarAlumnos
- parametro habilitado en las queries del asesor para reusarlas en modo consulta

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: `proximas`/`historial` genéricos

**Files:**
- Modify: `frontend/src/features/asesorias/logica.ts`
- Test: `frontend/src/features/asesorias/logica.test.ts`

**Interfaces:**
- Produces: `proximas<A extends AsesoriaOrdenable>(asesorias: A[]): A[]` y `historial<A extends AsesoriaOrdenable>(asesorias: A[]): A[]`, donde `AsesoriaOrdenable = Pick<Asesoria, 'estado' | 'fecha' | 'hora_inicio'>`. Aceptan tanto `Asesoria[]` como `AsesoriaAdmin[]` y devuelven el mismo tipo que reciben.

- [ ] **Step 1: Escribir el test que falla**

En `frontend/src/features/asesorias/logica.test.ts`, reemplazar la línea 3 por:

```typescript
import type { Disponibilidad, Asesoria, SlotDisponibilidad, AsesoriaAdmin } from '../../api/types'
```

Y añadir al final del archivo:

```typescript
function crearAsesoriaAdmin(overrides: Partial<AsesoriaAdmin> = {}): AsesoriaAdmin {
  return {
    id: 1,
    estado: 'agendada',
    fecha: '2026-08-03',
    hora_inicio: '10:00:00',
    materia: 1,
    carrera: 1,
    formato: 'virtual',
    ubicacion: '',
    liga_virtual: '',
    alumno_nombre: 'Beto Alumno',
    asesor_nombre: 'Ana Asesora',
    asistio: null,
    notas: '',
    ...overrides,
  }
}

describe('proximas / historial sobre la forma admin', () => {
  it('acepta AsesoriaAdmin y separa agendadas de no agendadas', () => {
    const lista = [
      crearAsesoriaAdmin({ id: 1, estado: 'realizada', fecha: '2026-07-01' }),
      crearAsesoriaAdmin({ id: 2, estado: 'agendada', fecha: '2026-08-20' }),
      crearAsesoriaAdmin({ id: 3, estado: 'cancelada', fecha: '2026-07-15' }),
    ]

    expect(proximas(lista).map((a) => a.id)).toEqual([2])
    expect(historial(lista).map((a) => a.id)).toEqual([3, 1])
  })

  it('conserva los campos exclusivos de la forma admin', () => {
    const [primera] = proximas([crearAsesoriaAdmin({ notas: 'llegó tarde' })])
    expect(primera.notas).toBe('llegó tarde')
    expect(primera.asesor_nombre).toBe('Ana Asesora')
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/logica.test.ts`
Expected: FAIL — error de tipo: `AsesoriaAdmin[]` no es asignable a `Asesoria[]` (falta `alumno`, `disponibilidad`, `creado_en`). En runtime el segundo caso falla al leer `.notas` tipado.

> Si Vitest no reporta el error de tipo (los tests no pasan por `tsc`), confirma el fallo con `npm run build` — no compila hasta aplicar el Step 3.

- [ ] **Step 3: Volver genéricos `proximas` e `historial`**

En `frontend/src/features/asesorias/logica.ts`, reemplazar las líneas 13-27 (`claveOrden`, `proximas`, `historial`) por:

```typescript
/** Lo mínimo que hace falta para ordenar y clasificar una sesión: lo cumplen
 *  tanto `Asesoria` (alumno/asesor) como `AsesoriaAdmin` (SAE). */
type AsesoriaOrdenable = Pick<Asesoria, 'estado' | 'fecha' | 'hora_inicio'>

function claveOrden(asesoria: AsesoriaOrdenable): string {
  return `${asesoria.fecha}T${asesoria.hora_inicio}`
}

export function proximas<A extends AsesoriaOrdenable>(asesorias: A[]): A[] {
  return asesorias
    .filter((a) => a.estado === 'agendada')
    .sort((a, b) => claveOrden(a).localeCompare(claveOrden(b)))
}

export function historial<A extends AsesoriaOrdenable>(asesorias: A[]): A[] {
  return asesorias
    .filter((a) => a.estado !== 'agendada')
    .sort((a, b) => claveOrden(b).localeCompare(claveOrden(a)))
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/logica.test.ts`
Expected: PASS (todos los casos existentes + los 2 nuevos).

- [ ] **Step 5: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/logica.ts frontend/src/features/asesorias/logica.test.ts
git commit -m "[refactor][frontend] proximas/historial genericos sobre la forma minima de sesion

- permiten reusar la clasificacion con AsesoriaAdmin sin duplicar logica

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: `TarjetaAsesoria` en modo admin

**Files:**
- Modify: `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`
- Test: `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx`

**Interfaces:**
- Consumes: `useEsAsesor()`, `InsigniaEstado`.
- Produces: `AsesoriaEnTarjeta = Pick<Asesoria, 'id' | 'estado' | 'fecha' | 'hora_inicio' | 'alumno_nombre' | 'asesor_nombre' | 'notas'>`; `TarjetaAsesoria({ asesoria: AsesoriaEnTarjeta, nombreMateria: string, indice: number, destacar?: boolean, admin?: boolean })`. Con `admin` muestra **ambos** nombres, muestra `notas` si no están vacías y **nunca** navega (no es botón), sin importar `useEsAsesor()`.

- [ ] **Step 1: Escribir los tests que fallan**

Añadir al final del `describe('TarjetaAsesoria', ...)` de `frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx` (antes de la llave de cierre del `describe`):

```tsx
  it('en modo admin muestra ambos nombres y las notas', () => {
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
    expect(screen.getByText(/Beto Alumno/)).toBeInTheDocument()
    expect(screen.getByText(/Ana Asesora/)).toBeInTheDocument()
    expect(screen.getByText(/el alumno llegó tarde/)).toBeInTheDocument()
  })

  it('en modo admin no navega aunque quien mire sea asesor', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(true)
    render(
      <TarjetaAsesoria asesoria={crearAsesoria()} nombreMateria="Cálculo I" indice={0} admin />,
      { wrapper: MemoryRouter },
    )
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('en modo admin sin notas no imprime la etiqueta Notas', () => {
    vi.spyOn(rol, 'useEsAsesor').mockReturnValue(false)
    render(
      <TarjetaAsesoria asesoria={crearAsesoria({ notas: '   ' })} nombreMateria="Cálculo I" indice={0} admin />,
      { wrapper: MemoryRouter },
    )
    expect(screen.queryByText(/^Notas:/)).not.toBeInTheDocument()
  })
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: FAIL — la prop `admin` no existe.

- [ ] **Step 3: Reescribir `TarjetaAsesoria`**

Reemplazar el contenido completo de `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx`:

```tsx
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Asesoria } from '../../../api/types'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import { useEsAsesor } from '../../../auth/rol'

const FORMATEADOR_FECHA = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'short' })

/** Lo mínimo que la tarjeta necesita: lo cumplen `Asesoria` y `AsesoriaAdmin`. */
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
  /** Modo SAE: ambos nombres + `notas`, y nunca navega a detalle. */
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
  const notas = admin ? asesoria.notas.trim() : ''

  // El detalle /asesorias/:id es asesor-only; en modo admin no hay ruta de
  // detalle en esta fase (spec §Out of scope), así que la tarjeta es estática.
  const interactiva = esAsesor && !admin

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
        {notas !== '' && <span className="text-xs text-on-surface-variant">Notas: {notas}</span>}
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
          onClick={() => navigate(`/asesorias/${asesoria.id}`)}
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

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/components/TarjetaAsesoria.test.tsx`
Expected: PASS (6 casos: 3 existentes + 3 nuevos).

- [ ] **Step 5: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS — `Asesorias.test.tsx` sigue verde.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/components/TarjetaAsesoria.tsx frontend/src/features/asesorias/components/TarjetaAsesoria.test.tsx
git commit -m "[feat][frontend] modo admin en TarjetaAsesoria para la vista SAE

- prop admin: ambos nombres + notas, tarjeta no interactiva
- prop tipada a la forma minima, acepta Asesoria y AsesoriaAdmin

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 6: Pantalla `AdminAsesorias` (`/sae/asesorias`)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AdminAsesorias.tsx`
- Test: `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx`

**Interfaces:**
- Consumes: `useAdminAsesorias`, `useAdminSemestres`, `useAdminAsesores`, `useBuscarAlumnos` (Task 3); `proximas`/`historial` (Task 4); `TarjetaAsesoria` con `admin` (Task 5); `useMapaMaterias`; `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent`; `Skeleton`.
- Produces: componente `AdminAsesorias`. Tabs Próximas/Historial; el Historial trae subtabs (`role="tab"`) por semestre. Filtros de asesor (`<select>` con label "Asesor") y alumno (`<input>` con label "Alumno" + resultados clicables), que se traducen a los filtros `{ asesor, alumno }` de `useAdminAsesorias`. Enlace "Consultar oferta" → `/sae/asesorias/oferta`.

- [ ] **Step 1: GATE — mockup y aprobación del usuario**

Generar un artefacto HTML (herramienta `Artifact`) con el layout propuesto de `/sae/asesorias`, mostrando: encabezado "Asesorías · SAE", botón "Consultar oferta", el bloque de filtros (select de asesor + búsqueda de alumno con lista de resultados y chip del alumno elegido), los tabs Próximas/Historial, los subtabs de semestre del Historial, y 3 tarjetas de ejemplo en modo admin (ambos nombres + notas + insignia de estado).

**DETENERSE AQUÍ.** Esperar aprobación explícita del usuario antes de escribir cualquier código de esta pantalla. Si el usuario pide cambios, actualizar el artefacto y volver a esperar.

- [ ] **Step 2: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesorias } from './AdminAsesorias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import * as rol from '../../../auth/rol'
import type { AlumnoBusqueda, AsesorDirectorio, AsesoriaAdmin } from '../../../api/types'

const ASESORES: AsesorDirectorio[] = [
  { perfil_id: 7, nombre: 'Ana López', area_nombre: 'Matemáticas', activo: true, num_materias_semestre_vigente: 3 },
  { perfil_id: 9, nombre: 'Luis Ruiz', area_nombre: 'Física', activo: false, num_materias_semestre_vigente: 1 },
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
  vi.spyOn(api, 'useAdminAsesores').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAdminAsesores>)
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

  it('lista las sesiones con ambos nombres y las notas', () => {
    montar()
    expect(screen.getByText(/Juan Pérez · Ana López/)).toBeInTheDocument()
    expect(screen.getByText(/trae dudas del examen/)).toBeInTheDocument()
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

  it('el filtro de asesor dispara la consulta con ese asesor', () => {
    const adminAsesorias = montar()
    fireEvent.change(screen.getByLabelText('Asesor'), { target: { value: '7' } })
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: 7, alumno: null })
  })

  it('el filtro de alumno dispara la consulta con ese alumno', () => {
    const adminAsesorias = montar()
    fireEvent.change(screen.getByLabelText('Alumno'), { target: { value: 'jua' } })
    fireEvent.click(screen.getByRole('button', { name: /Juan Pérez/ }))
    expect(adminAsesorias).toHaveBeenCalledWith({ asesor: null, alumno: 15 })
  })

  it('navega a la consulta de oferta', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Consultar oferta' }))
    expect(screen.getByText('oferta SAE')).toBeInTheDocument()
  })
})
```

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
import { useAdminAsesorias, useAdminAsesores, useAdminSemestres, useBuscarAlumnos } from '../api'
import { useMapaMaterias } from '../../catalogo/api'
import { historial, proximas } from '../logica'
import type { AlumnoBusqueda, AsesoriaAdmin } from '../../../api/types'

export function AdminAsesorias() {
  const navigate = useNavigate()
  const mapaMaterias = useMapaMaterias()
  const [asesor, setAsesor] = useState<number | null>(null)
  const [alumno, setAlumno] = useState<AlumnoBusqueda | null>(null)
  const idAlumno = alumno?.perfil_id ?? null

  const { data: asesorias = [], isPending } = useAdminAsesorias({ asesor, alumno: idAlumno })
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
          <Historial asesor={asesor} alumno={idAlumno} nombreMateria={nombreMateria} />
        </TabsContent>
      </Tabs>
    </main>
  )
}

function FiltroAsesor({ valor, onCambiar }: { valor: number | null; onCambiar: (v: number | null) => void }) {
  const { data: asesores = [] } = useAdminAsesores()
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="filtro-asesor" className="text-xs text-on-surface-variant">Asesor</label>
      <select
        id="filtro-asesor"
        value={valor ?? ''}
        onChange={(e) => onCambiar(e.target.value === '' ? null : Number(e.target.value))}
        className="foco-visible min-h-11 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
      >
        <option value="">Todos</option>
        {asesores.map((a) => (
          <option key={a.perfil_id} value={a.perfil_id}>{a.nombre}</option>
        ))}
      </select>
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
          <ul className="flex flex-col gap-1">
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
- filtros por asesor (select) y alumno (busqueda) traducidos a ?asesor=/?alumno=
- tarjetas en modo admin: ambos nombres + notas, no interactivas

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 7: `OfertaAsesorias` en modo consulta

**Files:**
- Modify: `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx`
- Test: `frontend/src/features/asesorias/screens/OfertaAsesorias.test.tsx`

**Interfaces:**
- Produces: `OfertaAsesorias({ titulo?, rutaVolver?, etiquetaVolver?, baseRutaMateria? })`. Defaults: `titulo = 'Nueva asesoría'`, `rutaVolver = '/asesorias'`, `etiquetaVolver = '← Volver a Asesorías'`, `baseRutaMateria = '/asesorias/nueva'`. Al elegir una materia navega a `` `${baseRutaMateria}/${materia_id}` ``. El filtro por carrera y la búsqueda no cambian.

- [ ] **Step 1: Escribir el test que falla**

En `frontend/src/features/asesorias/screens/OfertaAsesorias.test.tsx`, añadir al final del archivo (fuera del `describe` existente):

```tsx
function montarConsultaSAE() {
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
    <MemoryRouter initialEntries={['/sae/asesorias/oferta']}>
      <Routes>
        <Route
          path="/sae/asesorias/oferta"
          element={
            <OfertaAsesorias
              titulo="Consulta de oferta"
              rutaVolver="/sae/asesorias"
              etiquetaVolver="← Volver a Asesorías SAE"
              baseRutaMateria="/sae/asesorias/oferta"
            />
          }
        />
        <Route path="/sae/asesorias/oferta/:materiaId" element={<p>detalle SAE</p>} />
        <Route path="/sae/asesorias" element={<p>asesorías SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('OfertaAsesorias en modo consulta (SAE)', () => {
  afterEach(() => vi.restoreAllMocks())

  it('usa el título y la etiqueta de regreso configurados', () => {
    montarConsultaSAE()
    expect(screen.getByRole('heading', { name: 'Consulta de oferta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '← Volver a Asesorías SAE' })).toBeInTheDocument()
  })

  it('sigue filtrando por búsqueda de materia', () => {
    montarConsultaSAE()
    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'álge' } })
    expect(screen.getByRole('button', { name: /Álgebra/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Cálculo/ })).not.toBeInTheDocument()
  })

  it('navega al detalle SAE de la materia, no al wizard del alumno', () => {
    montarConsultaSAE()
    fireEvent.click(screen.getByRole('button', { name: /Álgebra/ }))
    expect(screen.getByText('detalle SAE')).toBeInTheDocument()
  })

  it('el botón de regreso lleva a la ruta configurada', () => {
    montarConsultaSAE()
    fireEvent.click(screen.getByRole('button', { name: '← Volver a Asesorías SAE' }))
    expect(screen.getByText('asesorías SAE')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/OfertaAsesorias.test.tsx`
Expected: FAIL — `OfertaAsesorias` no acepta props.

- [ ] **Step 3: Parametrizar la pantalla**

En `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx`, reemplazar la firma del componente (líneas 7-9) por:

```tsx
interface OfertaAsesoriasProps {
  /** Encabezado de la pantalla. */
  titulo?: string
  /** Destino del botón de regreso. */
  rutaVolver?: string
  /** Texto del botón de regreso. */
  etiquetaVolver?: string
  /** Prefijo del destino al elegir materia: `${baseRutaMateria}/${materia_id}`. */
  baseRutaMateria?: string
}

/**
 * Listado de la oferta. El alumno lo usa como paso 1 del agendado; el SAE lo
 * reusa en modo consulta cambiando título y destinos (ADR 0024) — la pantalla
 * no agenda nada por sí misma.
 */
export function OfertaAsesorias({
  titulo = 'Nueva asesoría',
  rutaVolver = '/asesorias',
  etiquetaVolver = '← Volver a Asesorías',
  baseRutaMateria = '/asesorias/nueva',
}: OfertaAsesoriasProps) {
  const navigate = useNavigate()
  const { data: oferta = [], isPending } = useOferta()
```

Reemplazar el botón de regreso y el `<h1>` (líneas 31-34 del archivo original) por:

```tsx
      <button type="button" onClick={() => navigate(rutaVolver)} className="foco-visible w-fit min-h-11 text-sm text-primary">
        {etiquetaVolver}
      </button>
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>
```

Y reemplazar el `onClick` de la fila de materia (línea 82 del archivo original) por:

```tsx
                onClick={() => navigate(`${baseRutaMateria}/${m.materia_id}`)}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/OfertaAsesorias.test.tsx`
Expected: PASS (7 casos: 3 existentes + 4 nuevos).

- [ ] **Step 5: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/OfertaAsesorias.tsx frontend/src/features/asesorias/screens/OfertaAsesorias.test.tsx
git commit -m "[feat][frontend] destino y copy configurables en OfertaAsesorias

- permite reusarla como consulta de oferta del SAE sin duplicar la pantalla

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 8: Pantalla `AdminOfertaMateria` (`/sae/asesorias/oferta/:materiaId`)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx`
- Test: `frontend/src/features/asesorias/screens/AdminOfertaMateria.test.tsx`

**Interfaces:**
- Consumes: `useParams().materiaId`, `useAsesoresDeMateria`, `useDisponibilidadDeAsesor`, `agruparPorDia`, `useMapaMaterias`, `Skeleton`.
- Produces: componente `AdminOfertaMateria`. Lista los asesores de la materia; al elegir uno muestra su disponibilidad agrupada por día, **todo read-only**: sin botón de agendar, sin selector de carrera, sin `Dialogo`, sin `useAgendarAsesoria`.

- [ ] **Step 1: GATE — mockup y aprobación del usuario**

Generar un artefacto HTML (herramienta `Artifact`) con el layout propuesto de `/sae/asesorias/oferta/:materiaId`: botón "← Volver a la oferta", nombre de la materia, aviso de solo lectura, lista de asesores seleccionable (nombre + área + formatos), y la disponibilidad del asesor elegido agrupada por día con chips de bloque (hora inicio–fin · formato/ubicación). Sin ningún control de agendado.

**DETENERSE AQUÍ.** Esperar aprobación explícita del usuario antes de escribir código. Si pide cambios, actualizar el artefacto y volver a esperar.

- [ ] **Step 2: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AdminOfertaMateria.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminOfertaMateria } from './AdminOfertaMateria'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
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

function montar() {
  vi.spyOn(api, 'useAsesoresDeMateria').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAsesoresDeMateria>)
  vi.spyOn(api, 'useDisponibilidadDeAsesor').mockReturnValue({
    data: SLOTS, isPending: false,
  } as ReturnType<typeof api.useDisponibilidadDeAsesor>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[12, { id: 12, nombre: 'Álgebra' } as never]]),
  )

  render(
    <MemoryRouter initialEntries={['/sae/asesorias/oferta/12']}>
      <Routes>
        <Route path="/sae/asesorias/oferta/:materiaId" element={<AdminOfertaMateria />} />
        <Route path="/sae/asesorias/oferta" element={<p>oferta SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminOfertaMateria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra la materia y sus asesores', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Álgebra' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ana López/ })).toBeInTheDocument()
  })

  it('al elegir un asesor muestra su disponibilidad por día', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.getByText('Disponibilidad')).toBeInTheDocument()
    expect(screen.getByText(/10:00–10:30/)).toBeInTheDocument()
  })

  it('no ofrece agendar ni selector de carrera', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.queryByRole('button', { name: /Agendar/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Carrera')).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('los bloques de disponibilidad no son interactivos', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.queryByRole('button', { name: /10:00–10:30/ })).not.toBeInTheDocument()
  })

  it('vuelve a la oferta', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Volver a la oferta' }))
    expect(screen.getByText('oferta SAE')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/AdminOfertaMateria.test.tsx`
Expected: FAIL — `AdminOfertaMateria` no existe.

- [ ] **Step 4: Implementar la pantalla**

Crear `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx`:

```tsx
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAsesoresDeMateria, useDisponibilidadDeAsesor } from '../api'
import { agruparPorDia } from '../logica'
import { useMapaMaterias } from '../../catalogo/api'
import { Skeleton } from '../../../components/ui/Skeleton'
import type { AsesorDisponible } from '../../../api/types'

const FORMATEADOR_DIA = new Intl.DateTimeFormat('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })

/**
 * Consulta de oferta del SAE: materia → asesores → disponibilidad, sin
 * agendar. Reusa los mismos endpoints que el wizard del alumno (ampliados a
 * `EsAlumnoOMiembroSAE`, ADR 0023) y termina en visualización.
 */
export function AdminOfertaMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const idMateria = Number(materiaId)
  const navigate = useNavigate()
  const mapaMaterias = useMapaMaterias()

  const { data: asesores = [], isPending: cargandoAsesores } = useAsesoresDeMateria(
    Number.isInteger(idMateria) ? idMateria : null,
  )
  const [registroId, setRegistroId] = useState<number | null>(null)
  const { data: slots = [], isPending: cargandoSlots } = useDisponibilidadDeAsesor(
    registroId !== null ? idMateria : null,
    registroId,
  )
  const dias = useMemo(() => agruparPorDia(slots), [slots])

  const volver = (
    <button
      type="button"
      onClick={() => navigate('/sae/asesorias/oferta')}
      className="foco-visible w-fit min-h-11 text-sm text-primary"
    >
      ← Volver a la oferta
    </button>
  )

  if (!Number.isInteger(idMateria)) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        {volver}
        <p className="text-sm text-on-surface-variant">Materia inválida.</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      {volver}
      <h1 className="text-lg font-semibold text-on-background">
        {mapaMaterias.get(idMateria)?.nombre ?? `Materia #${idMateria}`}
      </h1>
      <p className="text-xs text-on-surface-variant">
        Consulta de solo lectura: desde esta vista no se agendan asesorías.
      </p>

      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium text-on-surface">Asesores</h2>
        {cargandoAsesores ? (
          <Skeleton className="h-14" />
        ) : asesores.length === 0 ? (
          <p className="text-sm text-on-surface-variant">Esta materia no tiene asesores disponibles.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {asesores.map((a) => (
              <li key={a.registro_id}>
                <BotonAsesor
                  asesor={a}
                  seleccionado={registroId === a.registro_id}
                  onClick={() => setRegistroId(a.registro_id)}
                />
              </li>
            ))}
          </ul>
        )}
      </section>

      {registroId !== null && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-on-surface">Disponibilidad</h2>
          {cargandoSlots ? (
            <Skeleton className="h-14" />
          ) : dias.length === 0 ? (
            <p className="text-sm text-on-surface-variant">
              Este asesor no tiene horarios en las próximas dos semanas.
            </p>
          ) : (
            <ul className="flex flex-col gap-3">
              {dias.map((d) => (
                <li key={d.fecha} className="flex flex-col gap-1">
                  <span className="text-sm text-on-surface">
                    {FORMATEADOR_DIA.format(new Date(`${d.fecha}T00:00:00`))}
                  </span>
                  <ul className="flex flex-wrap gap-2">
                    {d.slots.map((s) => (
                      <li
                        key={s.disponibilidad_id}
                        className="flex min-h-11 items-center rounded-full bg-surface-container px-3 text-xs text-on-surface-variant"
                      >
                        {s.hora_inicio.slice(0, 5)}–{s.hora_fin.slice(0, 5)} ·{' '}
                        {s.formato === 'virtual' ? 'Virtual' : s.ubicacion || 'Presencial'}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  )
}

function BotonAsesor({
  asesor,
  seleccionado,
  onClick,
}: {
  asesor: AsesorDisponible
  seleccionado: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-pressed={seleccionado}
      onClick={onClick}
      className={`foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg px-4 py-3 text-left ${
        seleccionado ? 'bg-primary-container text-on-primary-container' : 'bg-surface-container'
      }`}
    >
      <span className="text-sm font-medium">{asesor.asesor_nombre}</span>
      <span className="text-xs text-on-surface-variant">
        {asesor.area_nombre} · {asesor.formatos.map((f) => (f === 'virtual' ? 'Virtual' : 'Presencial')).join(' / ')}
      </span>
    </button>
  )
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/AdminOfertaMateria.test.tsx`
Expected: PASS (5 casos).

- [ ] **Step 6: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx frontend/src/features/asesorias/screens/AdminOfertaMateria.test.tsx
git commit -m "[feat][frontend] detalle de materia de solo lectura para la consulta de oferta SAE

- asesores + disponibilidad por dia reusando agruparPorDia
- sin agendar, sin selector de carrera y sin dialogos

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 9: `soloLectura` en `MisMaterias` y `MiHorario`

**Files:**
- Modify: `frontend/src/features/asesorias/screens/MisMaterias.tsx`
- Modify: `frontend/src/features/asesorias/screens/MiHorario.tsx`
- Test: `frontend/src/features/asesorias/screens/MisMaterias.test.tsx`, `frontend/src/features/asesorias/screens/MiHorario.test.tsx`

**Interfaces:**
- Consumes: `useRegistroDelSemestre(semestre?, habilitado?)` y `useMisDisponibilidades(habilitado?)` (Task 3).
- Produces:
  - `MisMaterias({ soloLectura?: boolean, materias?: number[] | null, semestre?: string | null })` — con `soloLectura` renderiza un `<section>` (no `<main>`, sin botón de regreso, sin "+ Agregar", sin botón de quitar, sin diálogos), toma los ids de `materias` y etiqueta el semestre con `semestre`, y **no** dispara `GET /registros/`.
  - `MiHorario({ soloLectura?: boolean, disponibilidades?: Disponibilidad[] | null })` — con `soloLectura` renderiza un `<section>` con los 7 tabs de día y filas **no interactivas** (`<div>`, no `<button>`), sin diálogos ni `Retroalimentacion`, y **no** dispara `GET /registros/` ni `GET /disponibilidades/`.
  - En ambos, el nombre de la prop de modo es exactamente `soloLectura`.

- [ ] **Step 1: Escribir los tests que fallan (`MisMaterias`)**

Añadir al final del `describe('MisMaterias', ...)` de `frontend/src/features/asesorias/screens/MisMaterias.test.tsx` (antes de su llave de cierre):

```tsx
  it('en solo lectura muestra las materias recibidas y el semestre pedido', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[2, materia(2, 'Física')]]))
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias soloLectura materias={[2]} semestre="20261" />, { wrapper: envolver })

    expect(screen.getByRole('button', { name: 'Física' })).toBeInTheDocument()
    expect(screen.getByText('Semestre 20261')).toBeInTheDocument()
  })

  it('en solo lectura no ofrece agregar ni quitar', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map([[2, materia(2, 'Física')]]))
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias soloLectura materias={[2]} semestre="20261" />, { wrapper: envolver })

    expect(screen.queryByRole('button', { name: '+ Agregar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar Física' })).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('en solo lectura sin materias muestra el vacío del asesor consultado', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map())
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(<MisMaterias soloLectura materias={[]} semestre="20261" />, { wrapper: envolver })

    expect(
      screen.getByText('Este asesor no imparte materias en el semestre seleccionado.'),
    ).toBeInTheDocument()
  })
```

- [ ] **Step 2: Escribir los tests que fallan (`MiHorario`)**

Añadir al final del `describe('MiHorario', ...)` de `frontend/src/features/asesorias/screens/MiHorario.test.tsx` (antes de su llave de cierre):

```tsx
  function montarSoloLectura(disponibilidades: Disponibilidad[]) {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
    vi.spyOn(api, 'useMisDisponibilidades').mockReturnValue({
      data: [], isPending: false,
    } as ReturnType<typeof api.useMisDisponibilidades>)
    vi.spyOn(api, 'useSesionesFuturas').mockReturnValue({
      data: { total: 0, sesiones: [] }, isPending: false,
    } as ReturnType<typeof api.useSesionesFuturas>)
    vi.spyOn(api, 'useDesactivarDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useDesactivarDisponibilidad>)
    vi.spyOn(api, 'useActualizarDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useActualizarDisponibilidad>)
    vi.spyOn(api, 'useCrearDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useCrearDisponibilidad>)
    vi.spyOn(api, 'useEliminarDisponibilidad').mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof api.useEliminarDisponibilidad>)

    render(
      <MemoryRouter>
        <MiHorario soloLectura disponibilidades={disponibilidades} />
      </MemoryRouter>,
    )
  }

  it('en solo lectura pinta los bloques recibidos y conserva los 7 días', () => {
    montarSoloLectura([BLOQUE_LUNES])

    expect(screen.getAllByRole('tab')).toHaveLength(7)
    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })

  it('en solo lectura las celdas no son interactivas ni abren diálogos', () => {
    montarSoloLectura([BLOQUE_LUNES])

    expect(screen.queryAllByRole('button', { name: /^Horario/ })).toHaveLength(0)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `npx vitest run src/features/asesorias/screens/MisMaterias.test.tsx src/features/asesorias/screens/MiHorario.test.tsx`
Expected: FAIL — ninguna de las dos pantallas acepta props.

- [ ] **Step 4: Reescribir `MisMaterias`**

Reemplazar el contenido completo de `frontend/src/features/asesorias/screens/MisMaterias.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { primerMensajeDeError } from '../../../api/errores'
import { IconBasura } from '../../../components/icons/UiIcons'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { useMapaMaterias } from '../../catalogo/api'
import { useAgregarMateria, useQuitarMateria, useRegistroDelSemestre } from '../api'
import { DialogoAgregarMateria } from '../components/DialogoAgregarMateria'
import { DialogoQuitarMateria } from '../components/DialogoQuitarMateria'
import { SinRegistroAsesor } from '../components/SinRegistroAsesor'

interface MisMateriasProps {
  /** Modo consulta (SAE): sin agregar/quitar, sin diálogos y sin `<main>` propio. */
  soloLectura?: boolean
  /** Ids de materias a mostrar. `null` → las del registro propio del asesor. */
  materias?: number[] | null
  /** Semestre a etiquetar cuando `materias` viene de fuera. */
  semestre?: string | null
}

export function MisMaterias({ soloLectura = false, materias = null, semestre = null }: MisMateriasProps) {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()
  // En modo consulta quien mira es SAE: GET /registros/ le daría 403, así que
  // la query se apaga y los datos llegan por props.
  const { registro, cargando } = useRegistroDelSemestre(undefined, !soloLectura)
  const mapaMaterias = useMapaMaterias()

  const agregarMateria = useAgregarMateria(registro?.id ?? 0)
  const quitarMateria = useQuitarMateria(registro?.id ?? 0)

  const [dialogoAgregarAbierto, setDialogoAgregarAbierto] = useState(false)
  const [errorAgregar, setErrorAgregar] = useState<string | null>(null)
  const [materiaAQuitar, setMateriaAQuitar] = useState<number | null>(null)
  const [errorQuitar, setErrorQuitar] = useState<string | null>(null)
  const [expandida, setExpandida] = useState<number | null>(null)

  const nombreDe = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`
  const ids = soloLectura ? (materias ?? []) : (registro?.materias ?? [])
  const etiquetaSemestre = soloLectura ? semestre : (registro?.semestre ?? null)

  if (!soloLectura && cargando) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }

  const lista =
    ids.length === 0 ? (
      <p className="text-sm text-on-surface-variant">
        {soloLectura
          ? 'Este asesor no imparte materias en el semestre seleccionado.'
          : 'Todavía no impartes ninguna materia este semestre.'}
      </p>
    ) : (
      <ul className="flex flex-col">
        {ids.map((id) => (
          <li key={id} className="flex items-center gap-2 border-b border-outline-variant">
            <button
              type="button"
              title={nombreDe(id)}
              onClick={() => setExpandida((previa) => (previa === id ? null : id))}
              className={`foco-visible min-h-11 min-w-0 flex-1 rounded-md px-2 py-2 text-left text-sm text-on-surface ${
                expandida === id ? '' : 'truncate'
              }`}
            >
              {nombreDe(id)}
            </button>
            {!soloLectura && (
              <button
                type="button"
                aria-label={`Quitar ${nombreDe(id)}`}
                onClick={() => {
                  setErrorQuitar(null)
                  setMateriaAQuitar(id)
                }}
                className="foco-visible flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-high"
              >
                <IconBasura className="h-5 w-5" />
              </button>
            )}
          </li>
        ))}
      </ul>
    )

  if (soloLectura) {
    return (
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-on-background">Materias</h2>
        {etiquetaSemestre !== null && (
          <p className="text-xs text-on-surface-variant">Semestre {etiquetaSemestre}</p>
        )}
        {lista}
      </section>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>

      <div className="flex items-center justify-between gap-2">
        <h1 className="text-lg font-semibold text-on-background">Mis materias</h1>
        <button
          type="button"
          onClick={() => {
            setErrorAgregar(null)
            setDialogoAgregarAbierto(true)
          }}
          className="foco-visible min-h-11 rounded-full px-2 text-sm font-medium text-primary"
        >
          + Agregar
        </button>
      </div>

      <p className="text-xs text-on-surface-variant">Semestre {etiquetaSemestre}</p>

      {lista}

      <DialogoAgregarMateria
        abierto={dialogoAgregarAbierto}
        cargando={agregarMateria.isPending}
        error={errorAgregar}
        onConfirmar={(materiaId) =>
          agregarMateria.mutate(materiaId, {
            onSuccess: () => {
              setDialogoAgregarAbierto(false)
              mostrar('Materia agregada')
            },
            onError: (error) => setErrorAgregar(primerMensajeDeError(error)),
          })
        }
        onCerrar={() => setDialogoAgregarAbierto(false)}
      />

      <DialogoQuitarMateria
        abierto={materiaAQuitar !== null}
        nombreMateria={materiaAQuitar !== null ? nombreDe(materiaAQuitar) : ''}
        cargando={quitarMateria.isPending}
        error={errorQuitar}
        onConfirmar={() => {
          if (materiaAQuitar === null) return
          quitarMateria.mutate(materiaAQuitar, {
            onSuccess: () => {
              setMateriaAQuitar(null)
              mostrar('Materia quitada')
            },
            onError: (error) => setErrorQuitar(primerMensajeDeError(error)),
          })
        }}
        onCerrar={() => setMateriaAQuitar(null)}
      />

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
```

- [ ] **Step 5: Reescribir `MiHorario`**

Reemplazar el contenido completo de `frontend/src/features/asesorias/screens/MiHorario.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { primerMensajeDeError } from '../../../api/errores'
import type { Disponibilidad, FormatoAsesoria } from '../../../api/types'
import { IconPresencial, IconVirtual } from '../../../components/icons/UiIcons'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { Skeleton } from '../../../components/ui/Skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import {
  useActualizarDisponibilidad,
  useCrearDisponibilidad,
  useDesactivarDisponibilidad,
  useEliminarDisponibilidad,
  useMisDisponibilidades,
  useRegistroDelSemestre,
  useSesionesFuturas,
} from '../api'
import { DialogoBloqueActivo } from '../components/DialogoBloqueActivo'
import { DialogoDesactivarConSesiones } from '../components/DialogoDesactivarConSesiones'
import { DialogoNuevoBloque } from '../components/DialogoNuevoBloque'
import { SinRegistroAsesor } from '../components/SinRegistroAsesor'
import { diaSemanaHoy, slotsDelDia } from '../logica'

const DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const INSTRUCCION =
  'Cada celda es un horario disponible: toca para activarlo o editarlo. Para cambiar de día, usa las pestañas. Los cambios se autoguardan.'

const INSTRUCCION_LECTURA =
  'Horario del asesor en modo consulta. Para cambiar de día, usa las pestañas.'

function Leyenda() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant">
      <span className="rounded-full bg-primary-container px-2 py-0.5 text-on-primary-container">Activo</span>
      <span className="rounded-full bg-surface-variant px-2 py-0.5 text-on-surface-variant">Inactivo</span>
      <span className="flex items-center gap-1">
        <IconVirtual className="h-4 w-4" /> Virtual
      </span>
      <span className="flex items-center gap-1">
        <IconPresencial className="h-4 w-4" /> Presencial
      </span>
    </div>
  )
}

/** Contenido visual de una fila de horario, idéntico en modo edición y consulta. */
function ContenidoSlot({ hora, activo, disponibilidad }: {
  hora: string
  activo: boolean
  disponibilidad: Disponibilidad | null
}) {
  return (
    <>
      <span className="w-12 shrink-0 text-on-surface-variant">{hora.slice(0, 5)}</span>

      {activo && disponibilidad !== null && (
        <span className="flex min-w-0 flex-1 items-center gap-2">
          {disponibilidad.formato === 'virtual' ? (
            <IconVirtual className="h-4 w-4 shrink-0" />
          ) : (
            <IconPresencial className="h-4 w-4 shrink-0" />
          )}
          {disponibilidad.formato === 'presencial' && (
            <span className="truncate">{disponibilidad.ubicacion}</span>
          )}
        </span>
      )}

      <span
        className={`ml-auto shrink-0 rounded-full px-2 py-0.5 text-xs ${
          activo ? 'bg-primary-container text-on-primary-container' : 'bg-surface-variant text-on-surface-variant'
        }`}
      >
        {activo ? 'Activo' : 'Inactivo'}
      </span>
    </>
  )
}

interface MiHorarioProps {
  /** Modo consulta (SAE): celdas no interactivas, sin diálogos ni `<main>` propio. */
  soloLectura?: boolean
  /** Bloques a mostrar. `null` → los propios del asesor autenticado. */
  disponibilidades?: Disponibilidad[] | null
}

export function MiHorario({ soloLectura = false, disponibilidades = null }: MiHorarioProps) {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()

  // En modo consulta quien mira es SAE: sus GET propios darían 403.
  const { registro, cargando: cargandoRegistro } = useRegistroDelSemestre(undefined, !soloLectura)
  const { data: propias = [], isPending: cargandoPropias } = useMisDisponibilidades(!soloLectura)

  const crearDisponibilidad = useCrearDisponibilidad()
  const actualizarDisponibilidad = useActualizarDisponibilidad()
  const eliminarDisponibilidad = useEliminarDisponibilidad()
  const desactivarDisponibilidad = useDesactivarDisponibilidad()

  const [bloqueSeleccionado, setBloqueSeleccionado] = useState<Disponibilidad | null>(null)
  const [celdaVacia, setCeldaVacia] = useState<{ dia: number; hora: string } | null>(null)
  const [advertenciaAbierta, setAdvertenciaAbierta] = useState(false)
  const [errorBloque, setErrorBloque] = useState<string | null>(null)
  const [errorAdvertencia, setErrorAdvertencia] = useState<string | null>(null)

  const sesionesFuturas = useSesionesFuturas(bloqueSeleccionado?.id ?? null)

  const bloques = soloLectura ? (disponibilidades ?? []) : propias
  const cargandoBloques = soloLectura ? false : cargandoPropias

  if (!soloLectura && cargandoRegistro) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!soloLectura && !registro) {
    return <SinRegistroAsesor titulo="Mi horario" />
  }

  function tocarSlot(dia: number, hora: string, disponibilidad: Disponibilidad | null) {
    if (disponibilidad === null) {
      setErrorBloque(null)
      setCeldaVacia({ dia, hora })
      return
    }
    if (!disponibilidad.activa) {
      // Autoguardado: reactivar no destruye nada, no necesita confirmación.
      actualizarDisponibilidad.mutate(
        { id: disponibilidad.id, activa: true },
        { onSuccess: () => mostrar('Bloque activado') },
      )
      return
    }
    setBloqueSeleccionado(disponibilidad)
  }

  function desactivar(cancelarSesiones: boolean) {
    if (!bloqueSeleccionado) return
    desactivarDisponibilidad.mutate(
      { id: bloqueSeleccionado.id, cancelarSesiones },
      {
        onSuccess: () => {
          setAdvertenciaAbierta(false)
          setBloqueSeleccionado(null)
          mostrar(cancelarSesiones ? 'Bloque desactivado y sesiones canceladas' : 'Bloque desactivado')
        },
        onError: (error) => setErrorAdvertencia(primerMensajeDeError(error)),
      },
    )
  }

  function manejarDesactivar() {
    if ((sesionesFuturas.data?.total ?? 0) > 0) {
      setErrorAdvertencia(null)
      setAdvertenciaAbierta(true)
      return
    }
    desactivar(false)
  }

  function manejarEliminar() {
    if (!bloqueSeleccionado) return
    const id = bloqueSeleccionado.id
    setBloqueSeleccionado(null)
    eliminarDisponibilidad.mutate(id, { onSuccess: () => mostrar('Bloque eliminado') })
  }

  function manejarCrear(datos: { formato: FormatoAsesoria; ubicacion: string; liga_virtual: string }) {
    if (!celdaVacia || !registro) return
    crearDisponibilidad.mutate(
      {
        registro: registro.id,
        dia_semana: celdaVacia.dia,
        hora_inicio: celdaVacia.hora,
        ...datos,
      },
      {
        onSuccess: () => {
          setCeldaVacia(null)
          mostrar('Bloque creado')
        },
        onError: (error) => setErrorBloque(primerMensajeDeError(error)),
      },
    )
  }

  const rejilla = (
    <Tabs defaultValue={String(diaSemanaHoy())}>
      <TabsList className="gap-2 overflow-x-auto">
        {DIAS_CORTOS.map((dia, indice) => (
          <TabsTrigger key={dia} value={String(indice)}>
            {dia}
          </TabsTrigger>
        ))}
      </TabsList>

      {DIAS_CORTOS.map((_, indice) => (
        <TabsContent key={indice} value={String(indice)}>
          {cargandoBloques ? (
            <ul className="flex flex-col gap-1">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-11" />
              ))}
            </ul>
          ) : (
            <ul className="flex flex-col">
              {slotsDelDia(indice, bloques).map((slot) => (
                <li key={slot.clave}>
                  {soloLectura ? (
                    <div className="flex min-h-11 w-full items-center gap-2 border-b border-outline-variant px-2 text-sm text-on-surface">
                      <ContenidoSlot hora={slot.hora} activo={slot.activo} disponibilidad={slot.disponibilidad} />
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => tocarSlot(indice, slot.hora, slot.disponibilidad)}
                      aria-label={`Horario ${slot.hora.slice(0, 5)}, ${slot.activo ? 'activo' : 'inactivo'}`}
                      className="foco-visible flex min-h-11 w-full items-center gap-2 border-b border-outline-variant px-2 text-sm text-on-surface hover:bg-surface-container-high"
                    >
                      <ContenidoSlot hora={slot.hora} activo={slot.activo} disponibilidad={slot.disponibilidad} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </TabsContent>
      ))}
    </Tabs>
  )

  if (soloLectura) {
    return (
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold text-on-background">Horario</h2>
        <p className="text-xs text-on-surface-variant">{INSTRUCCION_LECTURA}</p>
        <Leyenda />
        {rejilla}
      </section>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>

      <h1 className="text-lg font-semibold text-on-background">Mi horario</h1>
      <p className="text-xs text-on-surface-variant">{INSTRUCCION}</p>
      <Leyenda />

      {rejilla}

      <DialogoBloqueActivo
        abierto={bloqueSeleccionado !== null && !advertenciaAbierta}
        disponibilidad={bloqueSeleccionado}
        cargando={desactivarDisponibilidad.isPending || sesionesFuturas.isPending}
        onDesactivar={manejarDesactivar}
        onEliminar={manejarEliminar}
        onCerrar={() => setBloqueSeleccionado(null)}
      />

      <DialogoDesactivarConSesiones
        abierto={advertenciaAbierta}
        total={sesionesFuturas.data?.total ?? 0}
        cargando={desactivarDisponibilidad.isPending}
        error={errorAdvertencia}
        onSoloNuevas={() => desactivar(false)}
        onCancelarYDesactivar={() => desactivar(true)}
        onCerrar={() => setAdvertenciaAbierta(false)}
      />

      <DialogoNuevoBloque
        abierto={celdaVacia !== null}
        diaSemana={celdaVacia?.dia ?? null}
        horaInicio={celdaVacia?.hora ?? null}
        nombreDia={celdaVacia ? DIAS[celdaVacia.dia] : ''}
        cargando={crearDisponibilidad.isPending}
        error={errorBloque}
        onConfirmar={manejarCrear}
        onCerrar={() => setCeldaVacia(null)}
      />

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/screens/MisMaterias.test.tsx src/features/asesorias/screens/MiHorario.test.tsx`
Expected: PASS (7 casos de `MisMaterias`, 9 de `MiHorario`).

- [ ] **Step 7: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/asesorias/screens/MisMaterias.tsx frontend/src/features/asesorias/screens/MisMaterias.test.tsx frontend/src/features/asesorias/screens/MiHorario.tsx frontend/src/features/asesorias/screens/MiHorario.test.tsx
git commit -m "[feat][frontend] modo soloLectura con fuente de datos externa en MisMaterias y MiHorario

- sin diálogos, sin acciones de escritura y sin queries propias (SAE daria 403)
- celdas de horario no interactivas en consulta; mismo layout que el asesor

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 10: Pantalla `AdminAsesores` (`/sae/asesores`)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AdminAsesores.tsx`
- Test: `frontend/src/features/asesorias/screens/AdminAsesores.test.tsx`

**Interfaces:**
- Consumes: `useAdminAsesores()` (Task 3), `Skeleton`.
- Produces: componente `AdminAsesores`. Lista `AsesorDirectorio` con nombre, área, chip `Activo`/`Inactivo` y nº de materias del semestre vigente; buscador por nombre en cliente (`<input>` con label "Buscar asesor"). Al elegir navega a `/sae/asesores/{perfil_id}`.

- [ ] **Step 1: GATE — mockup y aprobación del usuario**

Generar un artefacto HTML (herramienta `Artifact`) con el layout propuesto de `/sae/asesores`: botón "← Volver a Asesorías SAE", encabezado "Asesores", campo de búsqueda por nombre, y una lista de tarjetas de asesor (nombre, área, chip Activo/Inactivo, "N materias").

**DETENERSE AQUÍ.** Esperar aprobación explícita del usuario antes de escribir código. Si pide cambios, actualizar el artefacto y volver a esperar.

- [ ] **Step 2: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AdminAsesores.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesores } from './AdminAsesores'
import * as api from '../api'
import type { AsesorDirectorio } from '../../../api/types'

const ASESORES: AsesorDirectorio[] = [
  { perfil_id: 7, nombre: 'Ana López', area_nombre: 'Matemáticas', activo: true, num_materias_semestre_vigente: 3 },
  { perfil_id: 9, nombre: 'Luis Ruiz', area_nombre: 'Física', activo: false, num_materias_semestre_vigente: 1 },
]

function montar() {
  vi.spyOn(api, 'useAdminAsesores').mockReturnValue({
    data: ASESORES, isPending: false,
  } as ReturnType<typeof api.useAdminAsesores>)

  render(
    <MemoryRouter initialEntries={['/sae/asesores']}>
      <Routes>
        <Route path="/sae/asesores" element={<AdminAsesores />} />
        <Route path="/sae/asesores/:asesorId" element={<p>detalle de asesor</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AdminAsesores', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista los asesores con área, estado y número de materias', () => {
    montar()
    expect(screen.getByRole('button', { name: /Ana López/ })).toBeInTheDocument()
    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    expect(screen.getByText('Activo')).toBeInTheDocument()
    expect(screen.getByText('Inactivo')).toBeInTheDocument()
    expect(screen.getByText('3 materias')).toBeInTheDocument()
    expect(screen.getByText('1 materia')).toBeInTheDocument()
  })

  it('filtra por nombre en el cliente', () => {
    montar()
    fireEvent.change(screen.getByLabelText('Buscar asesor'), { target: { value: 'luis' } })
    expect(screen.getByRole('button', { name: /Luis Ruiz/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Ana López/ })).not.toBeInTheDocument()
  })

  it('navega al detalle del asesor elegido', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: /Ana López/ }))
    expect(screen.getByText('detalle de asesor')).toBeInTheDocument()
  })

  it('sin coincidencias muestra el estado vacío de la búsqueda', () => {
    montar()
    fireEvent.change(screen.getByLabelText('Buscar asesor'), { target: { value: 'zzz' } })
    expect(screen.getByText('Ningún asesor coincide con tu búsqueda.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesores.test.tsx`
Expected: FAIL — `AdminAsesores` no existe.

- [ ] **Step 4: Implementar la pantalla**

Crear `frontend/src/features/asesorias/screens/AdminAsesores.tsx`:

```tsx
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAdminAsesores } from '../api'
import { Skeleton } from '../../../components/ui/Skeleton'

/**
 * Directorio de asesores para la SAE. El filtro es en cliente: el listado
 * completo ya viene en una sola petición (sin paginación, deuda 0006).
 */
export function AdminAsesores() {
  const navigate = useNavigate()
  const { data: asesores = [], isPending } = useAdminAsesores()
  const [busqueda, setBusqueda] = useState('')

  const filtrados = useMemo(
    () => asesores.filter((a) => a.nombre.toLowerCase().includes(busqueda.toLowerCase())),
    [asesores, busqueda],
  )

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/sae/asesorias')}
        className="foco-visible w-fit min-h-11 text-sm text-primary"
      >
        ← Volver a Asesorías SAE
      </button>
      <h1 className="text-lg font-semibold text-on-background">Asesores</h1>

      <div className="flex flex-col gap-1">
        <label htmlFor="busqueda-asesor" className="text-xs text-on-surface-variant">Buscar asesor</label>
        <input
          id="busqueda-asesor"
          type="text"
          placeholder="Escribe para filtrar…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
        />
      </div>

      {isPending ? (
        <ul className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <li key={i}><Skeleton className="h-16" /></li>
          ))}
        </ul>
      ) : filtrados.length === 0 ? (
        <p className="text-sm text-on-surface-variant">
          {asesores.length === 0
            ? 'No hay asesores registrados.'
            : 'Ningún asesor coincide con tu búsqueda.'}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {filtrados.map((a, indice) => (
            <li key={a.perfil_id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
              <button
                type="button"
                onClick={() => navigate(`/sae/asesores/${a.perfil_id}`)}
                className="foco-visible flex min-h-11 w-full items-center justify-between gap-3 rounded-lg bg-surface-container px-4 py-3 text-left"
              >
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="truncate text-sm font-medium text-on-surface" title={a.nombre}>{a.nombre}</span>
                  <span className="truncate text-xs text-on-surface-variant">{a.area_nombre}</span>
                </span>
                <span className="flex shrink-0 flex-col items-end gap-1">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      a.activo
                        ? 'bg-primary-container text-on-primary-container'
                        : 'bg-surface-variant text-on-surface-variant'
                    }`}
                  >
                    {a.activo ? 'Activo' : 'Inactivo'}
                  </span>
                  <span className="text-xs text-on-surface-variant">
                    {a.num_materias_semestre_vigente} materia{a.num_materias_semestre_vigente === 1 ? '' : 's'}
                  </span>
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

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesores.test.tsx`
Expected: PASS (4 casos).

- [ ] **Step 6: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminAsesores.tsx frontend/src/features/asesorias/screens/AdminAsesores.test.tsx
git commit -m "[feat][frontend] directorio de asesores para la SAE

- nombre, area, estado activo y materias del semestre vigente
- busqueda por nombre en cliente; navega al detalle del asesor

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 11: Pantalla `AdminAsesorDetalle` (`/sae/asesores/:asesorId`)

**Files:**
- Create: `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx`
- Test: `frontend/src/features/asesorias/screens/AdminAsesorDetalle.test.tsx`

**Interfaces:**
- Consumes: `useParams().asesorId`, `useAdminAsesor(perfilId, semestre)` y `useAdminSemestres()` (Task 3), `MisMaterias` y `MiHorario` con `soloLectura` (Task 9), `Skeleton`.
- Produces: componente `AdminAsesorDetalle`. Encabezado con nombre, área y chip `Activo`/`Inactivo`; `<select>` de semestre (label "Semestre") que recarga el detalle; `MisMaterias soloLectura` con `materias={detalle.materias.map(m => m.id)}` y `semestre={detalle.semestre}`; `MiHorario soloLectura` con `disponibilidades={detalle.disponibilidades}`.

- [ ] **Step 1: GATE — mockup y aprobación del usuario**

Generar un artefacto HTML (herramienta `Artifact`) con el layout propuesto de `/sae/asesores/:asesorId`: botón "← Volver al directorio", nombre + área + chip Activo/Inactivo, selector de semestre, bloque "Materias" (lista read-only) y bloque "Horario" (rejilla de 7 días con filas no interactivas). Sin ningún botón de acción.

**DETENERSE AQUÍ.** Esperar aprobación explícita del usuario antes de escribir código. Si pide cambios, actualizar el artefacto y volver a esperar.

- [ ] **Step 2: Escribir el test que falla**

Crear `frontend/src/features/asesorias/screens/AdminAsesorDetalle.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminAsesorDetalle } from './AdminAsesorDetalle'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { AsesorDetalle } from '../../../api/types'

const DETALLE: AsesorDetalle = {
  perfil_id: 7,
  nombre: 'Ana López',
  area_nombre: 'Matemáticas',
  activo: true,
  semestre: '20262',
  materias: [{ id: 12, clave: '1234', nombre: 'Cálculo III' }],
  disponibilidades: [
    {
      id: 41,
      dia_semana: 0,
      hora_inicio: '09:00:00',
      formato: 'presencial',
      ubicacion: 'Salón O-221',
      liga_virtual: '',
      activa: true,
    },
  ],
}

function montar() {
  const adminAsesor = vi.spyOn(api, 'useAdminAsesor').mockReturnValue({
    data: DETALLE, isPending: false,
  } as ReturnType<typeof api.useAdminAsesor>)
  vi.spyOn(api, 'useAdminSemestres').mockReturnValue({
    data: ['20262', '20261'], isPending: false,
  } as ReturnType<typeof api.useAdminSemestres>)
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: null, cargando: false })
  vi.spyOn(api, 'useMisDisponibilidades').mockReturnValue({
    data: [], isPending: false,
  } as ReturnType<typeof api.useMisDisponibilidades>)
  vi.spyOn(api, 'useSesionesFuturas').mockReturnValue({
    data: { total: 0, sesiones: [] }, isPending: false,
  } as ReturnType<typeof api.useSesionesFuturas>)
  vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useAgregarMateria>)
  vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useQuitarMateria>)
  vi.spyOn(api, 'useCrearDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useCrearDisponibilidad>)
  vi.spyOn(api, 'useActualizarDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useActualizarDisponibilidad>)
  vi.spyOn(api, 'useEliminarDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useEliminarDisponibilidad>)
  vi.spyOn(api, 'useDesactivarDisponibilidad').mockReturnValue({
    mutate: vi.fn(), isPending: false,
  } as unknown as ReturnType<typeof api.useDesactivarDisponibilidad>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[12, { id: 12, nombre: 'Cálculo III' } as never]]),
  )

  render(
    <MemoryRouter initialEntries={['/sae/asesores/7']}>
      <Routes>
        <Route path="/sae/asesores/:asesorId" element={<AdminAsesorDetalle />} />
        <Route path="/sae/asesores" element={<p>directorio</p>} />
      </Routes>
    </MemoryRouter>,
  )
  return adminAsesor
}

describe('AdminAsesorDetalle', () => {
  beforeEach(() => {
    // Lunes: la pestaña por default del horario es la del bloque de prueba.
    vi.setSystemTime(new Date('2026-08-03T10:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('muestra la identidad del asesor', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Ana López' })).toBeInTheDocument()
    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    // aria-label propio: el texto "Activo" también aparece en la leyenda y en
    // los chips de la rejilla de horario.
    expect(screen.getByLabelText('Asesor activo')).toBeInTheDocument()
  })

  it('reusa materias y horario en modo solo lectura', () => {
    montar()
    expect(screen.getByRole('button', { name: 'Cálculo III' })).toBeInTheDocument()
    expect(screen.getByText('Semestre 20262')).toBeInTheDocument()
    expect(screen.getByText('Salón O-221')).toBeInTheDocument()
  })

  it('no ofrece ninguna acción de escritura', () => {
    montar()
    expect(screen.queryByRole('button', { name: '+ Agregar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar Cálculo III' })).not.toBeInTheDocument()
    expect(screen.queryAllByRole('button', { name: /^Horario/ })).toHaveLength(0)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cambiar de semestre recarga el detalle con ese semestre', () => {
    const adminAsesor = montar()
    fireEvent.change(screen.getByLabelText('Semestre'), { target: { value: '20261' } })
    expect(adminAsesor).toHaveBeenCalledWith(7, '20261')
  })

  it('vuelve al directorio', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Volver al directorio' }))
    expect(screen.getByText('directorio')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Correr el test y verificar que falla**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesorDetalle.test.tsx`
Expected: FAIL — `AdminAsesorDetalle` no existe.

- [ ] **Step 4: Implementar la pantalla**

Crear `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAdminAsesor, useAdminSemestres } from '../api'
import { Skeleton } from '../../../components/ui/Skeleton'
import { MisMaterias } from './MisMaterias'
import { MiHorario } from './MiHorario'

/**
 * Detalle read-only de un asesor para la SAE. Reutiliza "Mis materias" y
 * "Mi horario" en modo `soloLectura` con los datos de
 * GET /admin/asesores/{id}/ (ADR 0024), en vez de duplicar el layout.
 */
export function AdminAsesorDetalle() {
  const { asesorId } = useParams<{ asesorId: string }>()
  const perfilId = Number(asesorId)
  const navigate = useNavigate()
  const [semestre, setSemestre] = useState<string | null>(null)
  const { data: semestres = [] } = useAdminSemestres()
  const { data: detalle, isPending } = useAdminAsesor(
    Number.isInteger(perfilId) ? perfilId : null,
    semestre,
  )

  const volver = (
    <button
      type="button"
      onClick={() => navigate('/sae/asesores')}
      className="foco-visible w-fit min-h-11 text-sm text-primary"
    >
      ← Volver al directorio
    </button>
  )

  if (!Number.isInteger(perfilId)) {
    return (
      <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
        {volver}
        <p className="text-sm text-on-surface-variant">Asesor inválido.</p>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      {volver}

      {isPending || !detalle ? (
        <Skeleton className="h-16" />
      ) : (
        <>
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 flex-col gap-1">
              <h1 className="truncate text-lg font-semibold text-on-background" title={detalle.nombre}>
                {detalle.nombre}
              </h1>
              <span className="truncate text-xs text-on-surface-variant">{detalle.area_nombre}</span>
            </div>
            <span
              aria-label={detalle.activo ? 'Asesor activo' : 'Asesor inactivo'}
              className={`shrink-0 rounded-full px-2 py-0.5 text-xs ${
                detalle.activo
                  ? 'bg-primary-container text-on-primary-container'
                  : 'bg-surface-variant text-on-surface-variant'
              }`}
            >
              {detalle.activo ? 'Activo' : 'Inactivo'}
            </span>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="semestre-asesor" className="text-xs text-on-surface-variant">Semestre</label>
            <select
              id="semestre-asesor"
              value={semestre ?? ''}
              onChange={(e) => setSemestre(e.target.value === '' ? null : e.target.value)}
              className="foco-visible min-h-11 w-fit rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface"
            >
              <option value="">Semestre vigente</option>
              {semestres.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <MisMaterias
            soloLectura
            materias={detalle.materias.map((m) => m.id)}
            semestre={detalle.semestre}
          />

          <MiHorario soloLectura disponibilidades={detalle.disponibilidades} />
        </>
      )}
    </main>
  )
}
```

- [ ] **Step 5: Correr el test y verificar que pasa**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesorDetalle.test.tsx`
Expected: PASS (5 casos).

- [ ] **Step 6: Build + lint**

Run: `npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx frontend/src/features/asesorias/screens/AdminAsesorDetalle.test.tsx
git commit -m "[feat][frontend] detalle de asesor read-only para la SAE

- reusa MisMaterias y MiHorario en soloLectura con datos de /admin/asesores/{id}/
- selector de semestre para consultar registros pasados

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 12: Rutas `/sae/*` en `App.tsx`

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `RutaDeSAE` (Task 1), `AdminAsesorias` (Task 6), `OfertaAsesorias` con props (Task 7), `AdminOfertaMateria` (Task 8), `AdminAsesores` (Task 10), `AdminAsesorDetalle` (Task 11).
- Produces: rutas `/sae/asesorias`, `/sae/asesorias/oferta`, `/sae/asesorias/oferta/:materiaId`, `/sae/asesores`, `/sae/asesores/:asesorId`, todas envueltas en `RutaDeSAE`. Las rutas `/asesorias*` no cambian.

- [ ] **Step 1: Actualizar imports**

En `frontend/src/App.tsx`, reemplazar la línea 6 por:

```tsx
import { RutaDeAsesor, RutaDeAsesorias, RutaDeSAE } from './auth/RutaProtegida'
```

Y añadir después de la línea 12 (`import { MiHorario } ...`):

```tsx
import { AdminAsesorias } from './features/asesorias/screens/AdminAsesorias'
import { AdminOfertaMateria } from './features/asesorias/screens/AdminOfertaMateria'
import { AdminAsesores } from './features/asesorias/screens/AdminAsesores'
import { AdminAsesorDetalle } from './features/asesorias/screens/AdminAsesorDetalle'
```

- [ ] **Step 2: Añadir las rutas `/sae/*`**

En `frontend/src/App.tsx`, insertar justo antes de `</Routes>` (después de la ruta `/asesorias/:id`):

```tsx
        <Route
          path="/sae/asesorias"
          element={
            <RutaDeSAE>
              <AdminAsesorias />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesorias/oferta"
          element={
            <RutaDeSAE>
              <OfertaAsesorias
                titulo="Consulta de oferta"
                rutaVolver="/sae/asesorias"
                etiquetaVolver="← Volver a Asesorías SAE"
                baseRutaMateria="/sae/asesorias/oferta"
              />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesorias/oferta/:materiaId"
          element={
            <RutaDeSAE>
              <AdminOfertaMateria />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesores"
          element={
            <RutaDeSAE>
              <AdminAsesores />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesores/:asesorId"
          element={
            <RutaDeSAE>
              <AdminAsesorDetalle />
            </RutaDeSAE>
          }
        />
```

- [ ] **Step 3: Build**

Run: `npm run build`
Expected: PASS — todas las importaciones resuelven.

- [ ] **Step 4: Suite completa + lint**

Run: `npm test && npm run lint`
Expected: PASS — sin regresiones. Verdes: `rol`, `RutaProtegida`, `Home`, `api`, `logica`, `TarjetaAsesoria`, `Asesorias`, `OfertaAsesorias`, `AgendarAsesoria`, `MisMaterias`, `MiHorario`, `AdminAsesorias`, `AdminOfertaMateria`, `AdminAsesores`, `AdminAsesorDetalle`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "[feat][frontend] rutear el area SAE bajo RutaDeSAE

- /sae/asesorias, /sae/asesorias/oferta(/:materiaId), /sae/asesores(/:asesorId)
- la consulta de oferta reusa OfertaAsesorias con destinos SAE

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Self-Review

**Spec coverage** (contra `2026-08-09-asesorias-sae-admin-frontend-design.md`):

| Sección de la spec | Task |
|---|---|
| §0 Entrada — `'sae'` en `RolUsuario`, `useEsMiembroSAE`, `RutaDeSAE` | Task 1 |
| §0 Entrada — tarjeta de servicio SAE en `Home` | Task 2 |
| §0 Entrada — rutas `/sae/*` en `App.tsx` | Task 12 |
| §API frontend — hooks admin + tipos nuevos | Task 3 |
| §1 `AdminAsesorias` (tabs, subtabs, filtros asesor/alumno, enlace a oferta) | Task 6 |
| §1 Tarjeta admin (ambos nombres + `notas`, no interactiva) | Task 5 (+ Task 4 para el tipado genérico) |
| §2 Consulta de oferta (`OfertaAsesorias` en modo consulta) | Task 7 + ruta en Task 12 |
| §2 `AdminOfertaMateria` read-only | Task 8 |
| §3 `AdminAsesores` (directorio + buscador cliente) | Task 10 |
| §4 `AdminAsesorDetalle` (reuso `soloLectura` + selector de semestre) | Task 11 (+ Task 9 para las props) |
| §Componentes — `MisMaterias`/`MiHorario` con `soloLectura` + fuente parametrizable | Task 9 |
| §Testing — factory `usuarioSAE` | Task 1 |
| §Testing — guarda por rol (`sae` entra, sin rol → `/home`, sin sesión → `/login`) | Task 1 |
| §Testing — tabs Próximas/Historial, subtabs por semestre | Task 6 |
| §Testing — filtro asesor/alumno disparan la query con `?asesor=`/`?alumno=` | Task 3 (`rutaAdminAsesorias`, URL literal) + Task 6 (los filtros llegan al hook) |
| §Testing — tarjeta admin muestra ambos nombres y notas, y no navega | Task 5 |
| §Testing — oferta filtra por carrera y búsqueda; detalle sin botón de agendar ni selector de carrera | Task 7 + Task 8 |
| §Testing — directorio lista asesores; detalle `soloLectura` sin diálogos y con chips no interactivos; cambio de semestre recarga | Task 10 + Task 11 |
| §Testing — la tarjeta de Home aparece sólo con rol `sae` | Task 2 |
| §Out of scope — sin `/sae/asesorias/:id`, sin escritura, deudas 0006/0014 referenciadas | Global Constraints + Task 5 (tarjeta no interactiva) |

Sin huecos.

**Gate de mockup:** presente y bloqueante en las 4 pantallas nuevas (Tasks 6, 8, 10, 11), como paso 1 de cada una. Las 8 tareas restantes tocan sólo archivos existentes y no lo requieren.

**Placeholder scan:** ningún paso contiene "TBD", "similar a Task N", "…", ni descripciones sin código. Todos los componentes, tests, tipos y factories aparecen completos y verbatim.

**Consistencia de nombres entre tareas:**
- Prop de modo lectura: `soloLectura` idéntico en `MisMaterias` (Task 9), `MiHorario` (Task 9) y sus consumos en `AdminAsesorDetalle` (Task 11).
- Props de datos externos: `materias` + `semestre` (`MisMaterias`), `disponibilidades` (`MiHorario`) — usados con esos nombres exactos en Task 11.
- Hooks: `useAdminAsesorias`, `useAdminSemestres`, `useAdminAsesores`, `useAdminAsesor`, `useBuscarAlumnos`, `rutaAdminAsesorias` idénticos entre Task 3, 6, 10 y 11.
- Tipos: `AsesoriaAdmin`, `AsesorDirectorio`, `AsesorDetalle`, `AlumnoBusqueda`, `MateriaResumen`, `AsesoriaEnTarjeta` — declarados en Task 3/5 y consumidos con la misma forma en 6, 8, 10, 11.
- Guarda/hook de rol: `RutaDeSAE` y `useEsMiembroSAE` idénticos entre Task 1, 2 y 12.
- Props de `OfertaAsesorias`: `titulo`, `rutaVolver`, `etiquetaVolver`, `baseRutaMateria` idénticos entre Task 7 y Task 12.
- Firma `useAdminAsesor(perfilId, semestre)` — el test de Task 11 asegura `toHaveBeenCalledWith(7, '20261')`, consistente con la declaración de Task 3.

**Divergencias spec ↔ código resueltas** (detalladas en *File Structure*): no se crea `AdminOferta.tsx`; el chip `activo` no usa `InsigniaEstado` (tipado a `EstadoAsesoria`); `Disponibilidad.registro` pasa a opcional para admitir la forma del detalle admin; `proximas`/`historial` se vuelven genéricos porque `AsesoriaAdmin` no es asignable a `Asesoria`; las queries del asesor ganan un flag `habilitado` para poder montarlas en modo consulta sin provocar `403`.
