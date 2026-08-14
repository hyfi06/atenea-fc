# Fixes de navegación y sesión del frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar cuatro bugs de navegación y sesión del SPA desplegado: no se puede cerrar sesión, no se puede volver a Inicio desde Asesorías, `/` y `/login` ignoran la sesión existente, y las rutas inexistentes renderizan una página en blanco.

**Architecture:** Un componente nuevo `MenuUsuario` (patrón *disclosure*, sin dependencias) cablea el `logout()` que ya vive en `AuthContext`. `PantallaCargando` sale de `RutaProtegida.tsx` a `components/` para que `Landing` y `Login` lo reusen mientras `status === 'loading'`; ambas redirigen a `/home` con `<Navigate replace />` si ya hay sesión. Las dos pantallas raíz de Asesorías copian el botón "volver" que ya usa `OfertaAsesorias`. Una pantalla `NoEncontrado` nueva cuelga de un `<Route path="*">` al final de `Routes`.

**Tech Stack:** React 19 + TypeScript + Vite, React Router v7, Vitest + Testing Library (jsdom), Tailwind v4 con tokens MD3.

**Spec:** [`2026-08-13-fixes-navegacion-sesion-frontend-design.md`](../specs/2026-08-13-fixes-navegacion-sesion-frontend-design.md)

## Global Constraints

- **Comandos** (siempre desde `frontend/`): test puntual `npx vitest run <ruta>`; suite completa `npm test` (= `vitest run`); build `npm run build` (= `tsc -b && vite build`); lint `npm run lint` (= `oxlint`).
- **Sin dependencias nuevas.** Nada de `@radix-ui/react-dropdown-menu` ni de librerías de menú ([ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)).
- **`@testing-library/user-event` NO está instalado.** Todos los tests usan `fireEvent` de `@testing-library/react`.
- **Tests colocados** junto al archivo (`*.test.tsx`), hooks mockeados con `vi.spyOn(modulo, 'hook')`, factories de `src/test/factories.ts` (`usuarioDePrueba`, `usuarioSAE`), `afterEach(() => vi.restoreAllMocks())`.
- **Imports relativos** en `src/screens/` y `src/components/` (el alias `@/` sólo se usa hoy dentro de `components/ui/`).
- **Accesibilidad/estilo:** toque mínimo `min-h-11` / `h-11` (44 px), `.foco-visible` en **todo** elemento interactivo nuevo, `truncate` + `title` en textos que pueden desbordar, motion sólo con clases ya declaradas en `index.css` (`entrada-dialogo`, `spinner`) — que ya están neutralizadas bajo `@media (prefers-reduced-motion: reduce)`.
- **No se toca la API ni los hooks de datos.** Ningún cambio en `features/*/api.ts`, `api/client.ts` ni `api/types.ts`.
- **Sin ADR ni ítem de deuda nuevos:** son correcciones dentro de decisiones ya tomadas (ver §Contexto de la spec).
- **Commits** atómicos, formato `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>` ([ADR 0007](../../decisions/0007-commit-message-convention.md), [`docs/development/commit-conventions.md`](../../development/commit-conventions.md)).

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `frontend/src/components/PantallaCargando.tsx` | Spinner de página completa mientras se resuelve la sesión | Crear (se mueve desde `RutaProtegida.tsx`) |
| `frontend/src/auth/RutaProtegida.tsx` | Guardas de ruta por rol | Modificar: borra la copia local de `PantallaCargando` y la importa |
| `frontend/src/components/MenuUsuario.tsx` | Menú del header: identidad + cerrar sesión | Crear |
| `frontend/src/components/MenuUsuario.test.tsx` | Tests del menú | Crear |
| `frontend/src/screens/Home.tsx` | Hub de servicios | Modificar: el botón hamburguesa inerte pasa a ser `<MenuUsuario />` |
| `frontend/src/screens/Home.test.tsx` | Tests de Home | Modificar: mockear `useAuth` (obligatorio) + caso del menú |
| `frontend/src/features/asesorias/screens/Asesorias.tsx` | Raíz de `/asesorias` | Modificar: botón "← Inicio" |
| `frontend/src/features/asesorias/screens/Asesorias.test.tsx` | Tests de Asesorias | Modificar: `Routes` con `/home` + caso de regreso |
| `frontend/src/features/asesorias/screens/AdminAsesorias.tsx` | Raíz de `/sae/asesorias` | Modificar: botón "← Inicio" |
| `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx` | Tests de AdminAsesorias | Modificar: ruta `/home` + caso de regreso |
| `frontend/src/screens/Landing.tsx` | Entrada pública `/` | Modificar: spinner en `loading`, redirect a `/home` en `authenticated` |
| `frontend/src/screens/Landing.test.tsx` | Tests de Landing | Modificar: `status` parametrizable + 2 casos |
| `frontend/src/screens/Login.tsx` | Entrada `/login` | Modificar: mismo guard que Landing |
| `frontend/src/screens/Login.test.tsx` | Tests de Login | Modificar: `status` parametrizable + 2 casos |
| `frontend/src/screens/NoEncontrado.tsx` | Pantalla 404 | Crear |
| `frontend/src/screens/NoEncontrado.test.tsx` | Tests del 404 y del comodín | Crear |
| `frontend/src/App.tsx` | Tabla de rutas | Modificar: `<Route path="*" element={<NoEncontrado />} />` al final |

**Orden de dependencias:** Task 1 (extraer `PantallaCargando`) debe ir **antes** de Task 4. Las demás son independientes entre sí y pueden ejecutarse en cualquier orden.

**Decisiones de alcance registradas aquí (resueltas frente a la spec):**

1. **No hay `App.test.tsx`.** `App` monta su propio `BrowserRouter` y arrastra todas las pantallas con sus queries; el comodín se prueba desde `NoEncontrado.test.tsx` con un `Routes` mínimo que incluye `path="*"`.
2. **El componente y su cableado van en un solo commit** (Task 2). Un `MenuUsuario` que nadie monta es código muerto: el deliverable revisable es "desde Home se puede cerrar sesión".
3. **`Landing` y `Login` van en un solo commit** (Task 4): es el mismo cambio de tres líneas en las dos entradas de la misma acción; separarlos daría dos commits que un revisor sólo puede aceptar o rechazar juntos.

---

## Task 1: Extraer `PantallaCargando` a un componente reusable

**Files:**
- Create: `frontend/src/components/PantallaCargando.tsx`
- Modify: `frontend/src/auth/RutaProtegida.tsx:1-12`
- Test: `frontend/src/auth/RutaProtegida.test.tsx` (sin cambios — es la red de seguridad)

**Interfaces:**
- Consumes: nada.
- Produces: `PantallaCargando(): JSX.Element` — spinner centrado a página completa, con `aria-label="Cargando"`. Lo consumirán `RutaDeAsesor`, `RutaDeAsesorias`, `RutaDeSAE` (Task 1) y `Landing`/`Login` (Task 4).

- [ ] **Step 1: Crear el componente**

Crear `frontend/src/components/PantallaCargando.tsx` con el markup movido tal cual desde `RutaProtegida.tsx`:

```tsx
/**
 * Spinner de página completa mientras se resuelve el estado de la sesión.
 *
 * Vivía como función local en `auth/RutaProtegida.tsx`; se extrajo al ganar
 * consumidores fuera de las guardas (`Landing` y `Login` también esperan a
 * que `status` deje de ser 'loading'). Un solo markup para los cinco.
 */
export function PantallaCargando() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="spinner h-6 w-6 text-primary" aria-label="Cargando" />
    </div>
  )
}
```

- [ ] **Step 2: Importarlo desde las guardas**

En `frontend/src/auth/RutaProtegida.tsx`, reemplazar las líneas 1-12 (los imports y la función local `PantallaCargando`) por:

```tsx
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { useEsAsesor, useEsAlumno, useEsMiembroSAE } from './rol'
import { PantallaCargando } from '../components/PantallaCargando'
```

El resto del archivo (`RutaDeAsesor`, `RutaDeAsesorias`, `RutaDeSAE`) no se toca: siguen llamando a `<PantallaCargando />` igual que antes.

- [ ] **Step 3: Verificar que las guardas siguen verdes**

Run: `npx vitest run src/auth/RutaProtegida.test.tsx`
Expected: PASS — todos los casos existentes. Es una extracción mecánica: si algo se rompió, el markup no quedó idéntico.

- [ ] **Step 4: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PantallaCargando.tsx frontend/src/auth/RutaProtegida.tsx
git commit -m "[refactor][frontend] extraer PantallaCargando a components/

- el spinner de sesión pasa de función local de RutaProtegida a componente propio
- lo van a reusar Landing y Login para esperar a que status deje de ser loading

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Menú de usuario con cierre de sesión en `Home`

**Files:**
- Create: `frontend/src/components/MenuUsuario.tsx`
- Create: `frontend/src/components/MenuUsuario.test.tsx`
- Modify: `frontend/src/screens/Home.tsx:1-24`
- Modify: `frontend/src/screens/Home.test.tsx:1-17`

**Interfaces:**
- Consumes: `useAuth()` de `auth/AuthContext` — `user: AuthUser | null`, `status: 'loading' | 'authenticated' | 'unauthenticated'`, `logout(): Promise<void>`. `AuthUser` aporta `nombre_completo` y `email`.
- Produces: `MenuUsuario(): JSX.Element | null` — sin props. Renderiza `null` salvo con `status === 'authenticated'` y `user !== null`. Su disparador tiene nombre accesible `"Menú"`; la acción del panel se llama `"Cerrar sesión"` y navega a `/` tras resolver `logout()`.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/components/MenuUsuario.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { MenuUsuario } from './MenuUsuario'
import * as auth from '../auth/AuthContext'
import { usuarioDePrueba } from '../test/factories'

type Estado = 'loading' | 'authenticated' | 'unauthenticated'

interface Opciones {
  status?: Estado
  logout?: () => Promise<void>
}

function montar({ status = 'authenticated', logout = vi.fn().mockResolvedValue(undefined) }: Opciones = {}) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: status === 'authenticated' ? usuarioDePrueba() : null,
    roles: [],
    status,
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout,
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<MenuUsuario />} />
        <Route path="/" element={<p>pantalla landing</p>} />
      </Routes>
    </MemoryRouter>,
  )
  return logout
}

function disparador() {
  return screen.getByRole('button', { name: 'Menú' })
}

function abrir() {
  fireEvent.click(disparador())
}

describe('MenuUsuario', () => {
  afterEach(() => vi.restoreAllMocks())

  it('arranca cerrado', () => {
    montar()
    expect(disparador()).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('al abrirlo muestra la identidad de la sesión y la opción de cerrarla', () => {
    montar()
    abrir()
    expect(disparador()).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Ana López Ruiz')).toBeInTheDocument()
    expect(screen.getByText('usuaria@ciencias.unam.mx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })

  it('Escape lo cierra y devuelve el foco al disparador', () => {
    montar()
    abrir()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
    expect(disparador()).toHaveFocus()
  })

  it('un click fuera lo cierra', () => {
    montar()
    abrir()
    fireEvent.mouseDown(document.body)
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('cerrar sesión llama a logout una vez y lleva a la landing', async () => {
    const logout = montar()
    abrir()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByText('pantalla landing')).toBeInTheDocument()
    expect(logout).toHaveBeenCalledTimes(1)
  })

  it('sin sesión no dibuja el disparador', () => {
    montar({ status: 'unauthenticated' })
    expect(screen.queryByRole('button', { name: 'Menú' })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx`
Expected: FAIL — no existe el módulo `./MenuUsuario`.

- [ ] **Step 3: Implementar `MenuUsuario`**

Crear `frontend/src/components/MenuUsuario.tsx`:

```tsx
import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

/**
 * Menú de la hamburguesa del header de Home: identidad de la sesión arriba,
 * "Cerrar sesión" abajo.
 *
 * Es un *disclosure* (aria-expanded + aria-controls), no un role="menu": en
 * un menú ARIA todo hijo tendría que ser `menuitem`, y el bloque de
 * identidad no es accionable. Tampoco usa `Dialogo`, que es modal: esto se
 * ancla al disparador y no debe apoderarse del foco de la página.
 */
export function MenuUsuario() {
  const navigate = useNavigate()
  const { user, status, logout } = useAuth()
  const [abierto, setAbierto] = useState(false)
  const [cerrando, setCerrando] = useState(false)
  const contenedorRef = useRef<HTMLDivElement | null>(null)
  const disparadorRef = useRef<HTMLButtonElement | null>(null)
  const idPanel = useId()

  useEffect(() => {
    if (!abierto) return

    function alPresionarTecla(evento: KeyboardEvent) {
      if (evento.key !== 'Escape') return
      setAbierto(false)
      // Escape devuelve el foco al disparador; un click fuera no, porque el
      // foco ya se fue a donde el usuario apuntó.
      disparadorRef.current?.focus()
    }

    // `mousedown` y no `pointerdown`: jsdom no implementa PointerEvent de
    // forma confiable, y el evento de compatibilidad cubre igual el táctil.
    function alApuntarFuera(evento: MouseEvent) {
      if (contenedorRef.current?.contains(evento.target as Node) === true) return
      setAbierto(false)
    }

    document.addEventListener('keydown', alPresionarTecla)
    document.addEventListener('mousedown', alApuntarFuera)
    return () => {
      document.removeEventListener('keydown', alPresionarTecla)
      document.removeEventListener('mousedown', alApuntarFuera)
    }
  }, [abierto])

  async function cerrarSesion() {
    // `logout()` traga el error del POST y limpia el lado del cliente pase lo
    // que pase, así que no hay rama de error que mostrar; `cerrando` sólo
    // evita el doble disparo.
    setCerrando(true)
    await logout()
    navigate('/')
  }

  // /home es ruta pública: sin sesión no hay identidad que mostrar ni sesión
  // que cerrar, y un control que no hace nada es justo el bug que se arregla.
  if (status !== 'authenticated' || user === null) return null

  return (
    <div ref={contenedorRef} className="relative">
      <button
        ref={disparadorRef}
        type="button"
        aria-label="Menú"
        aria-haspopup="true"
        aria-expanded={abierto}
        aria-controls={idPanel}
        onClick={() => setAbierto((previo) => !previo)}
        className="foco-visible flex h-11 w-11 items-center justify-center rounded-full text-on-background"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="h-5 w-5" aria-hidden>
          <line x1="4" y1="7" x2="20" y2="7" />
          <line x1="4" y1="12" x2="20" y2="12" />
          <line x1="4" y1="17" x2="20" y2="17" />
        </svg>
      </button>

      {abierto && (
        <div
          id={idPanel}
          className="entrada-dialogo absolute right-0 top-12 z-10 flex w-60 flex-col gap-1 rounded-2xl bg-surface-container p-3 text-left shadow-lg"
        >
          <span className="truncate text-sm font-medium text-on-surface" title={user.nombre_completo}>
            {user.nombre_completo}
          </span>
          <span className="truncate text-xs text-on-surface-variant" title={user.email}>
            {user.email}
          </span>
          <hr className="my-1 border-outline-variant" />
          <button
            type="button"
            onClick={cerrarSesion}
            disabled={cerrando}
            className="foco-visible flex min-h-11 items-center rounded-lg px-2 text-sm font-medium text-error disabled:opacity-60"
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx`
Expected: PASS (6 casos).

- [ ] **Step 5: Actualizar `Home.test.tsx` — obligatorio**

`Home` va a consumir `useAuth()` a través de `MenuUsuario`, y el test actual no monta `AuthProvider` ni mockea el hook: sin este paso, todos los casos revientan con `useAuth debe usarse dentro de AuthProvider`.

Reemplazar las líneas 1-17 de `frontend/src/screens/Home.test.tsx` por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Home } from './Home'
import * as rol from '../auth/rol'
import * as auth from '../auth/AuthContext'
import { usuarioDePrueba } from '../test/factories'

function montar(esMiembroSAE: boolean) {
  vi.spyOn(rol, 'useEsMiembroSAE').mockReturnValue(esMiembroSAE)
  // Home monta MenuUsuario, que llama a useAuth: sin este doble el hook
  // lanza por falta de AuthProvider.
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: usuarioDePrueba(),
    roles: [],
    status: 'authenticated',
    loginWithPassword: vi.fn(),
    loginWithGoogle: vi.fn(),
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}
```

Y añadir un caso al final del `describe('Home', ...)`, antes de su llave de cierre. Ojo con la aserción: el `<button aria-label="Menú">` inerte **ya existe** hoy, así que un test que sólo lo busque pasaría sin haber arreglado nada. Lo que hay que probar es que el botón del header **abre el menú**:

```tsx
  it('la hamburguesa del header abre el menú de la sesión', () => {
    montar(false)
    fireEvent.click(screen.getByRole('button', { name: 'Menú' }))
    expect(screen.getByText('usuaria@ciencias.unam.mx')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cerrar sesión' })).toBeInTheDocument()
  })
```

- [ ] **Step 6: Correr `Home.test.tsx` y verificar que falla el caso nuevo**

Run: `npx vitest run src/screens/Home.test.tsx`
Expected: FAIL sólo en el caso nuevo — el click sobre la hamburguesa inerte no abre nada, así que no aparece el correo ni "Cerrar sesión". Los cuatro casos previos pasan (ya con el doble de `useAuth` del Step 5).

- [ ] **Step 7: Cablear `MenuUsuario` en `Home`**

Reemplazar el contenido completo de `frontend/src/screens/Home.tsx`:

```tsx
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { MenuUsuario } from '../components/MenuUsuario'
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
        <MenuUsuario />
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

- [ ] **Step 8: Correr los dos tests y verificar que pasan**

Run: `npx vitest run src/screens/Home.test.tsx src/components/MenuUsuario.test.tsx`
Expected: PASS (5 casos de Home + 6 de MenuUsuario).

- [ ] **Step 9: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/components/MenuUsuario.tsx frontend/src/components/MenuUsuario.test.tsx frontend/src/screens/Home.tsx frontend/src/screens/Home.test.tsx
git commit -m "[fix][frontend] menu de usuario con cierre de sesion en el header de Home

- MenuUsuario: disclosure con identidad de la sesion y accion de cerrar sesion
- cierra con Escape (devolviendo el foco) y con click fuera; sin dependencias nuevas
- la hamburguesa inerte de Home ahora monta el menu; toque minimo 44px y foco visible
- Home.test mockea useAuth, que Home pasa a consumir via MenuUsuario

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Botón "← Inicio" en las pantallas raíz de Asesorías

**Files:**
- Modify: `frontend/src/features/asesorias/screens/Asesorias.tsx:35-36`
- Modify: `frontend/src/features/asesorias/screens/Asesorias.test.tsx:1-27`
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorias.tsx:23-24`
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx`

**Interfaces:**
- Consumes: `useNavigate()` — ya está en scope en las dos pantallas (`Asesorias.tsx:13`, `AdminAsesorias.tsx:12`).
- Produces: en `/asesorias` y en `/sae/asesorias`, un botón con nombre accesible `"← Inicio"` que navega a `/home`. Ningún otro componente depende de esto.

- [ ] **Step 1: Escribir el test que falla en `Asesorias.test.tsx`**

El helper `envolver` monta hoy un `MemoryRouter` pelado, así que una navegación no renderiza nada. Reemplazar la línea 2 y el helper `envolver` (líneas 20-27) de `frontend/src/features/asesorias/screens/Asesorias.test.tsx` por:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
```

```tsx
function envolver({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/asesorias']}>
        <Routes>
          <Route path="/asesorias" element={children} />
          <Route path="/home" element={<p>pantalla home</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}
```

Ampliar también el import de router de la línea 3 a:

```tsx
import { MemoryRouter, Route, Routes } from 'react-router-dom'
```

Y añadir un caso al final del `describe('Asesorias (vista unificada)', ...)`, antes de su llave de cierre:

```tsx
  it('ofrece volver a Inicio', () => {
    montar({ esAsesor: false, esAlumno: true })
    fireEvent.click(screen.getByRole('button', { name: '← Inicio' }))
    expect(screen.getByText('pantalla home')).toBeInTheDocument()
  })
```

- [ ] **Step 2: Escribir el test que falla en `AdminAsesorias.test.tsx`**

En `frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx`, añadir la ruta `/home` al `Routes` del helper `montar`, que queda:

```tsx
  render(
    <MemoryRouter initialEntries={['/sae/asesorias']}>
      <Routes>
        <Route path="/sae/asesorias" element={<AdminAsesorias />} />
        <Route path="/sae/asesorias/oferta" element={<p>oferta SAE</p>} />
        <Route path="/home" element={<p>pantalla home</p>} />
      </Routes>
    </MemoryRouter>,
  )
```

Y añadir un caso al final del `describe('AdminAsesorias', ...)`, antes de su llave de cierre:

```tsx
  it('ofrece volver a Inicio', () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: '← Inicio' }))
    expect(screen.getByText('pantalla home')).toBeInTheDocument()
  })
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx src/features/asesorias/screens/AdminAsesorias.test.tsx`
Expected: FAIL — en ambos archivos, `Unable to find an accessible element with the role "button" and name "← Inicio"`. Los demás casos siguen pasando.

- [ ] **Step 4: Añadir el botón en `Asesorias.tsx`**

En `frontend/src/features/asesorias/screens/Asesorias.tsx`, reemplazar las líneas 35-36 por:

```tsx
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={() => navigate('/home')} className="foco-visible w-fit min-h-11 text-sm text-primary">
        ← Inicio
      </button>
      <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>
```

- [ ] **Step 5: Añadir el botón en `AdminAsesorias.tsx`**

En `frontend/src/features/asesorias/screens/AdminAsesorias.tsx`, reemplazar las líneas 23-24 por:

```tsx
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button type="button" onClick={() => navigate('/home')} className="foco-visible w-fit min-h-11 text-sm text-primary">
        ← Inicio
      </button>
      <h1 className="text-lg font-semibold text-on-background">Asesorías · SAE</h1>
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `npx vitest run src/features/asesorias/screens/Asesorias.test.tsx src/features/asesorias/screens/AdminAsesorias.test.tsx`
Expected: PASS — todos los casos existentes más el nuevo de cada archivo.

- [ ] **Step 7: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/asesorias/screens/Asesorias.tsx frontend/src/features/asesorias/screens/Asesorias.test.tsx frontend/src/features/asesorias/screens/AdminAsesorias.tsx frontend/src/features/asesorias/screens/AdminAsesorias.test.tsx
git commit -m "[fix][frontend] enlace de regreso a Inicio en las raices de Asesorias

- boton '← Inicio' en /asesorias y /sae/asesorias, mismo patron que OfertaAsesorias
- destino fijo /home y no navigate(-1): el historial puede venir de un deep link

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: Guard de sesión en `/` y `/login`

**Files:**
- Modify: `frontend/src/screens/Landing.tsx:1-11`
- Modify: `frontend/src/screens/Landing.test.tsx:7-26`
- Modify: `frontend/src/screens/Login.tsx:1-6, 40-47`
- Modify: `frontend/src/screens/Login.test.tsx:8-31`

**Depends on:** Task 1 (`components/PantallaCargando`).

**Interfaces:**
- Consumes: `PantallaCargando` (Task 1); `useAuth().status`; `Navigate` de `react-router-dom`.
- Produces: `Landing` y `Login` renderizan `<PantallaCargando />` con `status === 'loading'` y `<Navigate to="/home" replace />` con `status === 'authenticated'`. Con `'unauthenticated'` su comportamiento es exactamente el de hoy.

- [ ] **Step 1: Escribir los tests que fallan en `Landing.test.tsx`**

Reemplazar el helper `montar` (líneas 7-26) de `frontend/src/screens/Landing.test.tsx` por una versión con `status` parametrizable — el default deja intactos los cuatro casos existentes:

```tsx
type Estado = 'loading' | 'authenticated' | 'unauthenticated'

function montar(loginWithGoogle: () => Promise<void>, status: Estado = 'unauthenticated') {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status,
    loginWithPassword: vi.fn(),
    loginWithGoogle,
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/home" element={<p>pantalla home</p>} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}
```

Y añadir dos casos al final del `describe('Landing', ...)`, antes de su llave de cierre:

```tsx
  it('mientras la sesión se resuelve muestra el spinner y no la landing', () => {
    montar(vi.fn(), 'loading')

    expect(screen.getByLabelText('Cargando')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Continuar con Correo Ciencias' })).not.toBeInTheDocument()
  })

  it('con sesión ya iniciada redirige a Home', () => {
    montar(vi.fn(), 'authenticated')

    expect(screen.getByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Continuar con Correo Ciencias' })).not.toBeInTheDocument()
  })
```

- [ ] **Step 2: Escribir los tests que fallan en `Login.test.tsx`**

Reemplazar la interfaz `Dobles` y el helper `montar` (líneas 8-31) de `frontend/src/screens/Login.test.tsx` por:

```tsx
type Estado = 'loading' | 'authenticated' | 'unauthenticated'

interface Dobles {
  loginWithPassword?: (email: string, password: string) => Promise<void>
  loginWithGoogle?: () => Promise<void>
  status?: Estado
}

function montar({
  loginWithPassword = vi.fn(),
  loginWithGoogle = vi.fn(),
  status = 'unauthenticated',
}: Dobles = {}) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status,
    loginWithPassword,
    loginWithGoogle,
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<p>pantalla home</p>} />
      </Routes>
    </MemoryRouter>,
  )
}
```

Y añadir dos casos al final del `describe('Login', ...)`, antes de su llave de cierre:

```tsx
  it('mientras la sesión se resuelve muestra el spinner y no el formulario', () => {
    montar({ status: 'loading' })

    expect(screen.getByLabelText('Cargando')).toBeInTheDocument()
    expect(screen.queryByLabelText('Correo')).not.toBeInTheDocument()
  })

  it('con sesión ya iniciada redirige a Home', () => {
    montar({ status: 'authenticated' })

    expect(screen.getByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByLabelText('Correo')).not.toBeInTheDocument()
  })
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `npx vitest run src/screens/Landing.test.tsx src/screens/Login.test.tsx`
Expected: FAIL — los 4 casos nuevos: con `'loading'` no hay elemento con `aria-label="Cargando"` (se renderiza la pantalla de auth), y con `'authenticated'` no aparece "pantalla home". Los casos previos siguen pasando.

- [ ] **Step 4: Implementar el guard en `Landing.tsx`**

En `frontend/src/screens/Landing.tsx`, reemplazar las líneas 1-11 por:

```tsx
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Boton } from '../components/ui/Boton'
import { PantallaCargando } from '../components/PantallaCargando'
import { useAuth } from '../auth/AuthContext'

export function Landing() {
  const navigate = useNavigate()
  const { loginWithGoogle, status } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Todos los hooks quedan arriba: las salidas tempranas van después, para no
  // romper el orden de hooks entre renders.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'authenticated') return <Navigate to="/home" replace />
```

El resto del archivo (`handleGoogleLogin` y el JSX) no se toca. El `navigate('/home')` tras un login exitoso se conserva: el guard sólo lo vuelve redundante, no incorrecto.

- [ ] **Step 5: Implementar el guard en `Login.tsx`**

En `frontend/src/screens/Login.tsx`, reemplazar la línea 2 por:

```tsx
import { Navigate, useNavigate } from 'react-router-dom'
```

Añadir tras la línea 5 (el import de `Boton`):

```tsx
import { PantallaCargando } from '../components/PantallaCargando'
```

Y reemplazar las líneas 41-47 (el cuerpo de hooks de `Login`) por:

```tsx
  const navigate = useNavigate()
  const { loginWithPassword, loginWithGoogle, status } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Mismo guard que Landing: son dos entradas a la misma acción.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'authenticated') return <Navigate to="/home" replace />
```

El resto del archivo (`TextField`, `handleSubmit`, `handleGoogleLogin` y el JSX) no se toca.

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `npx vitest run src/screens/Landing.test.tsx src/screens/Login.test.tsx`
Expected: PASS — 6 casos en Landing y 7 en Login.

- [ ] **Step 7: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/screens/Landing.tsx frontend/src/screens/Landing.test.tsx frontend/src/screens/Login.tsx frontend/src/screens/Login.test.tsx
git commit -m "[fix][frontend] / y /login redirigen a Home cuando ya hay sesion

- spinner mientras status es loading, mismo criterio que las guardas de ruta
- Navigate a /home con replace si la sesion ya esta resuelta
- helpers de test parametrizados por status, sin tocar los casos existentes

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: Pantalla 404 y ruta comodín

**Files:**
- Create: `frontend/src/screens/NoEncontrado.tsx`
- Create: `frontend/src/screens/NoEncontrado.test.tsx`
- Modify: `frontend/src/App.tsx:1-17, 120-128`

**Interfaces:**
- Consumes: `Logo` de `components/Logo`; `Boton` de `components/ui/Boton` (`ButtonHTMLAttributes` + `cargando?`, `variante?: 'primario' | 'secundario' | 'peligro'`); `useNavigate()`.
- Produces: `NoEncontrado(): JSX.Element` — muestra "404", el encabezado "Página no encontrada" y un botón "Volver al inicio" que navega a `/`. Se monta desde `<Route path="*">`, el último de `Routes` en `App.tsx`.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/screens/NoEncontrado.test.tsx`. El `Routes` de aquí replica la forma del de `App.tsx` (una ruta real + el comodín), que es lo que hace de este archivo también la prueba del comodín:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { NoEncontrado } from './NoEncontrado'

function montar(ruta: string) {
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <Routes>
        <Route path="/" element={<p>pantalla landing</p>} />
        <Route path="*" element={<NoEncontrado />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('NoEncontrado', () => {
  it('la ruta comodín atrapa cualquier dirección desconocida', () => {
    montar('/ruta-que-no-existe')

    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
  })

  it('no se interpone con las rutas que sí existen', () => {
    montar('/')

    expect(screen.getByText('pantalla landing')).toBeInTheDocument()
    expect(screen.queryByText('404')).not.toBeInTheDocument()
  })

  it('el botón de salida lleva a la raíz', () => {
    montar('/otra-direccion-inventada')

    fireEvent.click(screen.getByRole('button', { name: 'Volver al inicio' }))

    expect(screen.getByText('pantalla landing')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/screens/NoEncontrado.test.tsx`
Expected: FAIL — no existe el módulo `./NoEncontrado`.

- [ ] **Step 3: Implementar la pantalla**

Crear `frontend/src/screens/NoEncontrado.tsx`:

```tsx
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Boton } from '../components/ui/Boton'

/**
 * Pantalla del comodín `path="*"`. La salida apunta a `/` y no a `/home`
 * porque la landing ya resuelve los dos casos: con sesión redirige a /home,
 * sin sesión se muestra a sí misma.
 */
export function NoEncontrado() {
  const navigate = useNavigate()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 px-6 py-12 text-center">
      <Logo className="h-16 w-16 text-primary" />
      <p className="text-5xl font-semibold text-primary">404</p>
      <h1 className="text-lg font-semibold text-on-background">Página no encontrada</h1>
      <p className="max-w-[28ch] text-sm text-on-surface-variant">
        La dirección que abriste no existe o cambió de lugar.
      </p>
      <Boton type="button" onClick={() => navigate('/')} className="px-6">
        Volver al inicio
      </Boton>
    </main>
  )
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/screens/NoEncontrado.test.tsx`
Expected: PASS (3 casos).

- [ ] **Step 5: Registrar el comodín en `App.tsx`**

En `frontend/src/App.tsx`, añadir tras la línea 5 (el import de `HealthCheck`):

```tsx
import { NoEncontrado } from './screens/NoEncontrado'
```

Y añadir la ruta como **último** hijo de `<Routes>`, justo antes de `</Routes>` (después del bloque de `/sae/asesores/:asesorId`):

```tsx
        <Route path="*" element={<NoEncontrado />} />
```

El orden importa: en React Router v7 el ranking de rutas favorece las estáticas sobre el comodín, pero dejarlo al final mantiene la tabla legible y a prueba de futuras rutas.

- [ ] **Step 6: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS — `tsc -b` confirma que `NoEncontrado` existe y está bien tipada donde `App.tsx` la monta.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/screens/NoEncontrado.tsx frontend/src/screens/NoEncontrado.test.tsx frontend/src/App.tsx
git commit -m "[fix][frontend] pantalla 404 y ruta comodin

- NoEncontrado con la estetica de la landing (Logo + Boton) y salida a /
- Route path='*' al final de Routes: una URL desconocida ya no deja pagina en blanco

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Verificación final

- [ ] **Suite completa, build y lint desde `frontend/`**

Run: `npm test && npm run build && npm run lint`
Expected: PASS, sin tests saltados.

- [ ] **Repaso manual del recorrido arreglado** (con `npm run dev`, sesión iniciada):
  1. `/home` → hamburguesa → se ven nombre y correo → "Cerrar sesión" → cae en `/` y la landing se muestra (ya sin sesión).
  2. Volver a entrar → `/` redirige solo a `/home`; `/login` también.
  3. `/home` → tarjeta de Asesorías (o de Asesorías · SAE) → "← Inicio" regresa a `/home`.
  4. `/cualquier-cosa` → 404 → "Volver al inicio" → `/home` si hay sesión, landing si no.

---

## Self-review

**1. Cobertura de la spec**

| Sección de la spec | Task |
|---|---|
| §1 Menú de usuario (`MenuUsuario` + `Home`) | Task 2 |
| §2 Regreso a Inicio (`Asesorias`, `AdminAsesorias`) | Task 3 |
| §3 `PantallaCargando` compartido | Task 1 |
| §4 Guard de sesión en `Landing` y `Login` | Task 4 |
| §5 Pantalla 404 + comodín | Task 5 |
| §Testing — `MenuUsuario.test.tsx` (6 casos) | Task 2, Step 1 |
| §Testing — actualización obligatoria de `Home.test.tsx` | Task 2, Step 5 |
| §Testing — `Asesorias.test.tsx` / `AdminAsesorias.test.tsx` | Task 3, Steps 1-2 |
| §Testing — `Landing.test.tsx` / `Login.test.tsx` parametrizados por `status` | Task 4, Steps 1-2 |
| §Testing — `NoEncontrado.test.tsx` cubre también el comodín | Task 5, Step 1 |
| §Testing — `RutaProtegida.test.tsx` sin cambios, como red de seguridad | Task 1, Step 3 |

Sin huecos: las cinco secciones de "Pantallas y flujos" y las siete entradas de "Testing" tienen tarea.

**2. Sin placeholders**

Cada step que toca código trae el código completo, con rutas de archivo y números de línea del estado actual verificado. No hay "manejo de errores apropiado", "similar a la Task N" ni tests descritos en prosa.

**3. Consistencia de tipos y nombres**

- `PantallaCargando` — creado en Task 1, consumido con ese nombre exacto en Task 1 (guardas) y Task 4 (`Landing`, `Login`).
- `MenuUsuario` — creado en Task 2 Step 3, montado con ese nombre en Task 2 Step 7; sin props en ninguno de los dos.
- `NoEncontrado` — creado en Task 5 Step 3, importado con ese nombre en Step 5.
- `status` — el tipo `'loading' | 'authenticated' | 'unauthenticated'` coincide con `EstadoSesion` de `AuthContext.tsx:7` en los tres helpers de test que lo declaran (`MenuUsuario.test.tsx`, `Landing.test.tsx`, `Login.test.tsx`).
- Nombres accesibles usados en assertions y en implementación: `"Menú"`, `"Cerrar sesión"`, `"← Inicio"`, `"Volver al inicio"`, `"Cargando"` — escritos idénticos en ambos lados de cada tarea.
- `usuarioDePrueba()` produce `nombre_completo: 'Ana López Ruiz'` y `email: 'usuaria@ciencias.unam.mx'`, exactamente los textos que asserta `MenuUsuario.test.tsx`.
