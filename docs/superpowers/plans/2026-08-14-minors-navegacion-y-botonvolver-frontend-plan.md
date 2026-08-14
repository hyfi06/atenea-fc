# Minors de navegación/sesión + `BotonVolver` compartido — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar los cinco hallazgos Minor de la revisión del branch `fixes de navegación y sesión` (logout no terminal, redirección post-login duplicada, `state.from` ignorado, `aria-haspopup` contradictorio) y extraer el botón de regreso duplicado en 15 sitios a un componente `BotonVolver`.

**Architecture:** El cierre de sesión pasa a `navigate('/', { replace: true })` para que el sign-out sea terminal, y el disparador del menú deja de anunciarse como `menu`. La redirección post-autenticación se colapsa en un solo dueño: el guard de `Landing`/`Login`, que ahora lee `location.state.from` a través de un helper puro nuevo (`auth/destinoPostLogin.ts`) con fallback a `/home`; las pantallas dejan de llamar `navigate('/home')` a mano. Por último, un `BotonVolver` en `components/` — con dos modos, destino (`a`) o handler (`onClick`) — reemplaza las 15 copias del mismo `<button className="foco-visible w-fit min-h-11 text-sm text-primary">`, preservando literalmente cada nombre accesible.

**Tech Stack:** React 19 + TypeScript + Vite, React Router v7, Vitest + Testing Library (jsdom), Tailwind v4 con tokens MD3.

**Spec:** Este plan no tiene spec propia: es el follow-up de revisión de [`2026-08-13-fixes-navegacion-sesion-frontend-design.md`](../specs/2026-08-13-fixes-navegacion-sesion-frontend-design.md) y de su plan [`2026-08-13-fixes-navegacion-sesion-frontend-plan.md`](2026-08-13-fixes-navegacion-sesion-frontend-plan.md), mergeados en `dev` como `f15d932`. Los cinco hallazgos (M1–M5) y las dos decisiones ya tomadas por el usuario (**honrar `state.from`**, **migrar TODOS los sitios a `BotonVolver`**) son el contrato de alcance de este documento.

## Global Constraints

- **Comandos** (siempre desde `frontend/`): test puntual `npx vitest run <ruta>`; suite completa `npm test` (= `vitest run`); build `npm run build` (= `tsc -b && vite build`); lint `npm run lint` (= `oxlint`).
- **Sin dependencias nuevas.**
- **`@testing-library/user-event` NO está instalado.** Todos los tests usan `fireEvent` de `@testing-library/react`.
- **Tests colocados** junto al archivo (`*.test.tsx` / `*.test.ts`), hooks mockeados con `vi.spyOn(modulo, 'hook')`, factories de `src/test/factories.ts` (`usuarioDePrueba`, `usuarioSAE`), `afterEach(() => vi.restoreAllMocks())`.
- **Imports relativos** en `src/screens/`, `src/components/` y `src/features/` (el alias `@/` sólo se usa hoy dentro de `components/ui/` y de `features/asesorias/components/SinRegistroAsesor.tsx`; en ese archivo se mantiene `@/` por consistencia interna del archivo).
- **`noUnusedLocals` y `noUnusedParameters` están en `true`** (`tsconfig.app.json:25-26`): si una migración deja `navigate` o `useNavigate` sin uso, hay que borrarlos o `npm run build` falla.
- **Accesibilidad/estilo:** toque mínimo `min-h-11` / `h-11` (44 px), `.foco-visible` en **todo** elemento interactivo, `truncate` + `title` en textos que pueden desbordar, motion sólo con clases ya declaradas en `index.css`.
- **No se toca la API ni los hooks de datos.** Ningún cambio en `features/*/api.ts`, `api/client.ts` ni `api/types.ts`.
- **Sin ADR ni ítem de deuda nuevos:** son correcciones y limpieza dentro de decisiones ya tomadas. M5 cierra una duplicación existente que nunca se registró como ítem formal de deuda; no se crea uno retroactivo.
- **Commits** atómicos, formato `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>` ([ADR 0007](../../decisions/0007-commit-message-convention.md), [`docs/development/commit-conventions.md`](../../development/commit-conventions.md)). Tipos válidos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

---

## File Structure

| Archivo | Responsabilidad | Acción | Task |
|---|---|---|---|
| `frontend/src/components/MenuUsuario.tsx` | Menú del header: identidad + cerrar sesión | Modificar: logout terminal (`replace`), sin `aria-haspopup`, `aria-controls` sólo al abrir | 1 |
| `frontend/src/components/MenuUsuario.test.tsx` | Tests del menú | Modificar: 3 casos nuevos | 1 |
| `frontend/src/auth/destinoPostLogin.ts` | Función pura que traduce `location.state` a la URL post-autenticación | Crear | 2 |
| `frontend/src/auth/destinoPostLogin.test.ts` | Tests de la función pura | Crear | 2 |
| `frontend/src/screens/Landing.tsx` | Entrada pública `/` | Modificar: guard lee `from`; se quita `navigate('/home')` | 2 |
| `frontend/src/screens/Landing.test.tsx` | Tests de Landing | Reescribir el helper + 1 caso nuevo, 1 reinterpretado | 2 |
| `frontend/src/screens/Login.tsx` | Entrada `/login` | Modificar: guard lee `from`; se quitan los dos `navigate('/home')` | 2 |
| `frontend/src/screens/Login.test.tsx` | Tests de Login | Reescribir el helper + 1 caso nuevo, 1 reinterpretado | 2 |
| `frontend/src/auth/RutaProtegida.test.tsx` | Tests de las guardas de rol | Modificar: sonda que prueba el contrato `state.from` extremo a extremo | 2 |
| `frontend/src/components/BotonVolver.tsx` | Botón de regreso compartido (modo destino / modo handler) | Crear | 3 |
| `frontend/src/components/BotonVolver.test.tsx` | Tests del botón | Crear | 3 |
| `frontend/src/features/asesorias/screens/Asesorias.tsx` | Raíz de `/asesorias` | Migrar a `BotonVolver` ("← Inicio") | 4 |
| `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx` | Wizard de agendado | Migrar 3 botones ("← Volver a Asesorías" ×2, "← Atrás") | 4 |
| `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx` | Listado de la oferta | Migrar (`rutaVolver` / `etiquetaVolver` intactos) | 4 |
| `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx` | Detalle de una asesoría | Migrar 2 botones ("← Volver a Asesorías") | 4 |
| `frontend/src/features/asesorias/screens/MisMaterias.tsx` | Materias del asesor | Migrar ("← Volver a Asesorías") | 4 |
| `frontend/src/features/asesorias/screens/MiHorario.tsx` | Horario del asesor | Migrar ("← Volver a Asesorías") | 4 |
| `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx` | Estado sin registro de asesor | Migrar ("← Volver a Asesorías") | 4 |
| `frontend/src/features/asesorias/screens/AdminAsesorias.tsx` | Raíz de `/sae/asesorias` | Migrar ("← Inicio") | 5 |
| `frontend/src/features/asesorias/screens/AdminAsesores.tsx` | Directorio de asesores SAE | Migrar ("← Volver a Asesorías SAE") | 5 |
| `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx` | Detalle de asesor SAE | Migrar ("← Volver al directorio") | 5 |
| `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx` | Oferta por materia SAE | Migrar ("← Volver a la oferta") | 5 |
| `frontend/src/features/asesorias/screens/AdminDetalleAsesoria.tsx` | Detalle de sesión SAE | Migrar ("← Volver a Asesorías SAE") | 5 |

**Orden de dependencias:**

- **Task 1** (M1 + M4) es independiente: sólo toca `MenuUsuario`.
- **Task 2** (M2 + M3) es independiente de la 1: toca el helper nuevo, `Landing`, `Login` y el test de las guardas. M2 y M3 van juntos porque son el mismo cambio: quitar `navigate('/home')` sólo es correcto si el guard ya sabe a dónde mandar al usuario.
- **Task 3** (crear `BotonVolver`) debe ir **antes** de las Tasks 4 y 5.
- **Task 4** y **Task 5** dependen de la 3 y son independientes entre sí (no comparten ningún archivo).

**Decisiones de alcance registradas aquí:**

1. **`aria-haspopup` se elimina, no se cambia a `"dialog"`.** El panel no es un diálogo: no es modal, no tiene `role="dialog"`, no atrapa el foco. Anunciarlo como `dialog` sería la misma mentira que `menu`, sólo que distinta. El patrón *disclosure* de la APG se describe completo con `aria-expanded` + `aria-controls`; `aria-haspopup` sobra. El comentario de `MenuUsuario.tsx:9-12` ya justifica el patrón; el atributo era el único resto que lo contradecía.
2. **`aria-controls` sólo se renderiza cuando el panel está abierto** (el "opcional" del hallazgo M4 **entra** al alcance). Apuntar a un `id` inexistente es una referencia colgante que algunos lectores de pantalla anuncian como error; y el atributo está en el mismo `<button>` que ya se edita para quitar `aria-haspopup`, así que separarlo daría dos commits que un revisor sólo puede aceptar o rechazar juntos.
3. **`Login.tsx:87-96` (el botón de flecha con `navigate(-1)` y `aria-label="Volver"`) queda FUERA del alcance de `BotonVolver`.** No comparte el className, su nombre accesible no lleva "←", su contenido es un SVG y no texto, y su tamaño es `h-9 w-9`. Meterlo obligaría a `BotonVolver` a aceptar hijos arbitrarios y a parametrizar el tamaño, es decir a dejar de ser el componente que resuelve la duplicación real.
4. **`BotonVolver` se crea en su propia task (3) y se migra en las 4-5.** El componente nace con su propia suite de tests, así que el commit de la Task 3 no es código sin cobertura; separarlo permite que un revisor apruebe o rechace el diseño de la API **antes** de leer 15 ediciones mecánicas.
5. **La migración se parte en dos tasks por área** (alumno/asesor vs. SAE) para que cada commit siga siendo revisable de un vistazo. No comparten archivos, así que pueden ejecutarse en cualquier orden entre sí.
6. **El className canónico de `BotonVolver` es `foco-visible w-fit min-h-11 rounded-md text-sm text-primary`**, la unión de las cuatro variantes que hay hoy en el código. La migración por tanto:
   - añade `foco-visible` a los 2 botones de `DetalleAsesoria.tsx` (hoy `w-fit text-sm text-primary`, sin foco visible — infringe la constraint global);
   - añade `min-h-11` a los 5 botones que hoy usan `foco-visible w-fit rounded-md text-sm text-primary` (`SinRegistroAsesor`, `MisMaterias`, `MiHorario`) y a los 2 de `DetalleAsesoria` — todos por debajo del toque mínimo de 44 px;
   - añade `rounded-md` a los 10 restantes, lo que sólo redondea las esquinas del anillo de foco (son botones de texto sin fondo).
   Ningún nombre accesible cambia.

---

## Task 1: Logout terminal y disclosure honesto en `MenuUsuario` (M1 + M4)

**Files:**
- Modify: `frontend/src/components/MenuUsuario.tsx:49-56` (función `cerrarSesion`) y `:64-79` (el `<button>` disparador)
- Modify: `frontend/src/components/MenuUsuario.test.tsx:1-89` (imports + 3 casos nuevos)

**Interfaces:**
- Consumes: `useAuth()` de `auth/AuthContext` — `user: AuthUser | null`, `status: 'loading' | 'authenticated' | 'unauthenticated'`, `logout(): Promise<void>`; `useNavigate()` de `react-router-dom`.
- Produces: `MenuUsuario(): JSX.Element | null` — sin props, sin cambios en su firma. Su disparador conserva el nombre accesible `"Menú"` y la acción del panel conserva `"Cerrar sesión"`. Cambia el comportamiento observable: tras `logout()` navega a `/` **reemplazando** la entrada de historial, el disparador ya no expone `aria-haspopup`, y expone `aria-controls` sólo mientras `abierto === true`.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/components/MenuUsuario.test.tsx`, reemplazar la línea 3 por:

```tsx
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
```

Añadir, justo después de la función `abrir()` (línea 42) y antes del `describe`, una sonda que permite retroceder en el historial del `MemoryRouter`:

```tsx
/**
 * Botón de "atrás" del navegador simulado. Vive FUERA de `<Routes>` para
 * seguir montado después de la navegación, y es la única forma de observar
 * desde jsdom si el cierre de sesión hizo push o replace.
 */
function BotonAtras() {
  const navigate = useNavigate()
  return (
    <button type="button" onClick={() => navigate(-1)}>
      atrás de prueba
    </button>
  )
}
```

Y hacer que `montar` lo renderice: reemplazar el bloque `render(...)` de las líneas 25-32 por:

```tsx
  render(
    <MemoryRouter initialEntries={['/home']}>
      <Routes>
        <Route path="/home" element={<MenuUsuario />} />
        <Route path="/" element={<p>pantalla landing</p>} />
      </Routes>
      <BotonAtras />
    </MemoryRouter>,
  )
```

Y añadir los tres casos al final del `describe('MenuUsuario', ...)`, antes de su llave de cierre:

```tsx
  it('cerrar sesión es terminal: el botón Atrás no devuelve a la sesión', async () => {
    montar()
    abrir()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByText('pantalla landing')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'atrás de prueba' }))

    expect(screen.getByText('pantalla landing')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Menú' })).not.toBeInTheDocument()
  })

  it('el disparador no se anuncia como menú', () => {
    montar()
    expect(disparador()).not.toHaveAttribute('aria-haspopup')
    abrir()
    expect(disparador()).not.toHaveAttribute('aria-haspopup')
  })

  it('aria-controls sólo existe mientras el panel existe', () => {
    montar()
    expect(disparador()).not.toHaveAttribute('aria-controls')

    abrir()
    const idPanel = disparador().getAttribute('aria-controls')
    expect(idPanel).not.toBeNull()
    expect(document.getElementById(idPanel as string)).toBeInTheDocument()
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx`
Expected: FAIL en los tres casos nuevos — el de "terminal" porque `navigate('/')` hace push y el Atrás vuelve a `/home` (reaparece el botón "Menú"); el de `aria-haspopup` porque hoy vale `"true"`; el de `aria-controls` porque hoy se renderiza siempre y con el panel cerrado apunta a un `id` que no existe. Los 6 casos previos siguen pasando.

- [ ] **Step 3: Implementar los dos arreglos**

En `frontend/src/components/MenuUsuario.tsx`, reemplazar la función `cerrarSesion` (líneas 49-56) por:

```tsx
  async function cerrarSesion() {
    // `logout()` traga el error del POST y limpia el lado del cliente pase lo
    // que pase, así que no hay rama de error que mostrar; `cerrando` sólo
    // evita el doble disparo.
    setCerrando(true)
    await logout()
    // `replace` y no push: el sign-out es terminal. Con push, el botón Atrás
    // del navegador devolvía a /home — que sin sesión ya no es la pantalla que
    // el usuario dejó. Mismo criterio con el que las guardas de ruta redirigen.
    navigate('/', { replace: true })
  }
```

Y reemplazar el `<button>` disparador (líneas 64-79) por:

```tsx
      <button
        ref={disparadorRef}
        type="button"
        aria-label="Menú"
        aria-expanded={abierto}
        // Sin `aria-haspopup`: mapea a `menu` y contradice la elección
        // deliberada de NO usar role="menu" (ver el comentario de arriba).
        // `aria-controls` sólo cuando hay panel: apuntar a un id inexistente
        // es una referencia colgante.
        aria-controls={abierto ? idPanel : undefined}
        onClick={() => setAbierto((previo) => !previo)}
        className="foco-visible flex h-11 w-11 items-center justify-center rounded-full text-on-background"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" className="h-5 w-5" aria-hidden>
          <line x1="4" y1="7" x2="20" y2="7" />
          <line x1="4" y1="12" x2="20" y2="12" />
          <line x1="4" y1="17" x2="20" y2="17" />
        </svg>
      </button>
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx`
Expected: PASS (9 casos).

- [ ] **Step 5: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/MenuUsuario.tsx frontend/src/components/MenuUsuario.test.tsx
git commit -m "[fix][frontend] cierre de sesion terminal y disclosure sin aria-haspopup

- navigate('/', { replace: true }) tras logout: el boton Atras ya no vuelve a /home
- se quita aria-haspopup, que mapea a menu y contradice el patron disclosure elegido
- aria-controls solo mientras el panel existe, sin referencia colgante
- tests: sonda de historial para observar replace, y los dos atributos ARIA

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Un solo dueño de la redirección post-login, que honra `state.from` (M2 + M3)

**Files:**
- Create: `frontend/src/auth/destinoPostLogin.ts`
- Create: `frontend/src/auth/destinoPostLogin.test.ts`
- Modify: `frontend/src/screens/Landing.tsx:1-32`
- Modify: `frontend/src/screens/Landing.test.tsx` (reescritura completa)
- Modify: `frontend/src/screens/Login.tsx:1-6, 41-83`
- Modify: `frontend/src/screens/Login.test.tsx` (reescritura completa)
- Modify: `frontend/src/auth/RutaProtegida.test.tsx:1-7` y final del archivo

**Interfaces:**
- Consumes: `useAuth().status`; `useLocation()` y `Navigate` de `react-router-dom`; `PantallaCargando` de `components/PantallaCargando`. El estado de navegación lo produce `auth/RutaProtegida.tsx:16,31,46` con la forma `{ from: location }`.
- Produces:
  - `DESTINO_POR_DEFECTO: string` = `'/home'`.
  - `EstadoDeRedireccion` — `{ from?: { pathname?: string; search?: string; hash?: string } }`.
  - `destinoPostLogin(state: unknown): string` — devuelve la URL a la que redirigir tras autenticarse.
  - `Landing` y `Login` redirigen con `<Navigate to={destinoPostLogin(location.state)} replace />` cuando `status === 'authenticated'`, y ya **no** llaman `navigate('/home')` tras un login exitoso.

- [ ] **Step 1: Escribir los tests que fallan del helper**

Crear `frontend/src/auth/destinoPostLogin.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { destinoPostLogin, DESTINO_POR_DEFECTO } from './destinoPostLogin'

describe('destinoPostLogin', () => {
  it('sin state cae al destino por defecto', () => {
    expect(destinoPostLogin(undefined)).toBe('/home')
    expect(destinoPostLogin(null)).toBe('/home')
    expect(DESTINO_POR_DEFECTO).toBe('/home')
  })

  it('con state sin `from` cae al destino por defecto', () => {
    expect(destinoPostLogin({ otraCosa: 1 })).toBe('/home')
    expect(destinoPostLogin({ from: null })).toBe('/home')
    expect(destinoPostLogin({ from: {} })).toBe('/home')
  })

  it('devuelve la ruta que el usuario intentó abrir', () => {
    expect(destinoPostLogin({ from: { pathname: '/sae/asesorias' } })).toBe('/sae/asesorias')
  })

  it('conserva query string y fragmento', () => {
    expect(
      destinoPostLogin({ from: { pathname: '/asesorias', search: '?tab=historial', hash: '#top' } }),
    ).toBe('/asesorias?tab=historial#top')
  })

  it('no rebota hacia las propias pantallas de entrada', () => {
    expect(destinoPostLogin({ from: { pathname: '/' } })).toBe('/home')
    expect(destinoPostLogin({ from: { pathname: '/login' } })).toBe('/home')
  })

  it('rechaza destinos que no son rutas internas', () => {
    expect(destinoPostLogin({ from: { pathname: 'https://ejemplo.test/x' } })).toBe('/home')
    expect(destinoPostLogin({ from: { pathname: '//ejemplo.test/x' } })).toBe('/home')
    expect(destinoPostLogin({ from: { pathname: 42 } })).toBe('/home')
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/auth/destinoPostLogin.test.ts`
Expected: FAIL — no existe el módulo `./destinoPostLogin`.

- [ ] **Step 3: Implementar el helper**

Crear `frontend/src/auth/destinoPostLogin.ts`:

```ts
/** Destino cuando no hay una ruta intentada que honrar. */
export const DESTINO_POR_DEFECTO = '/home'

/**
 * Forma del `location.state` que las guardas de `RutaProtegida` dejan al
 * mandar a `/login`: `<Navigate to="/login" state={{ from: location }} />`.
 */
export interface EstadoDeRedireccion {
  from?: { pathname?: string; search?: string; hash?: string } | null
}

/**
 * Traduce el estado de navegación a la URL a la que llevar al usuario ya
 * autenticado.
 *
 * Hasta ahora las guardas guardaban `from` y nadie lo leía: el deep link se
 * perdía y todo mundo aterrizaba en `/home`. Este es el único lugar donde se
 * decide ese destino, y por eso también es donde se filtra lo que no debe
 * pasar: `state` viene de la barra de direcciones vía historial, así que se
 * trata como entrada no confiable. Sólo se aceptan rutas internas (una sola
 * barra inicial: `//host` sería un redirect abierto) y se descartan `/` y
 * `/login`, que devolverían al usuario a la pantalla de la que acaba de salir.
 */
export function destinoPostLogin(state: unknown): string {
  const from = (state as EstadoDeRedireccion | null | undefined)?.from
  const pathname = from?.pathname

  if (typeof pathname !== 'string') return DESTINO_POR_DEFECTO
  if (!pathname.startsWith('/') || pathname.startsWith('//')) return DESTINO_POR_DEFECTO
  if (pathname === '/' || pathname === '/login') return DESTINO_POR_DEFECTO

  return `${pathname}${from?.search ?? ''}${from?.hash ?? ''}`
}
```

- [ ] **Step 4: Correr los tests del helper y verificar que pasan**

Run: `npx vitest run src/auth/destinoPostLogin.test.ts`
Expected: PASS (6 casos).

- [ ] **Step 5: Reescribir `Landing.test.tsx`**

El helper `montar` deja de recibir el `status` como segundo posicional y pasa a recibir un objeto de opciones, para poder inyectar también el `state` de la entrada del router. Y los dos casos que asertaban `navigate('/home')` desde la pantalla cambian de intención: ahora la pantalla sólo dispara el login y la redirección es del guard.

Reemplazar el contenido completo de `frontend/src/screens/Landing.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { InitialEntry } from 'react-router-dom'
import { Landing } from './Landing'
import * as auth from '../auth/AuthContext'

type Estado = 'loading' | 'authenticated' | 'unauthenticated'

interface Opciones {
  status?: Estado
  /** Entrada inicial del router: string o `{ pathname, state }` para simular el `from` del guard. */
  entrada?: InitialEntry
}

function montar(
  loginWithGoogle: () => Promise<void>,
  { status = 'unauthenticated', entrada = '/' }: Opciones = {},
) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status,
    loginWithPassword: vi.fn(),
    loginWithGoogle,
    logout: vi.fn(),
  } as ReturnType<typeof auth.useAuth>)

  render(
    <MemoryRouter initialEntries={[entrada]}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/home" element={<p>pantalla home</p>} />
        <Route path="/login" element={<p>pantalla login</p>} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function botonDeGoogle() {
  return screen.getByRole('button', { name: 'Continuar con Correo Ciencias' })
}

describe('Landing', () => {
  afterEach(() => vi.restoreAllMocks())

  it('dispara el login y deja la redirección al guard', async () => {
    const loginWithGoogle = vi.fn().mockResolvedValue(undefined)
    montar(loginWithGoogle)

    fireEvent.click(botonDeGoogle())

    await waitFor(() => expect(loginWithGoogle).toHaveBeenCalledTimes(1))
    // La pantalla ya no navega a mano: mientras el doble de useAuth siga
    // diciendo 'unauthenticated', la landing se queda donde está. Quien
    // redirige es el guard de abajo, probado en sus propios casos.
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('si el login falla, muestra el error y no navega', async () => {
    montar(vi.fn().mockRejectedValue(new Error('popup cerrado')))

    fireEvent.click(botonDeGoogle())

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo iniciar sesión con Google.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('deshabilita el botón mientras el login está en curso', async () => {
    // Promesa que nunca se resuelve: fija el estado "conectando".
    montar(vi.fn().mockReturnValue(new Promise<void>(() => {})))

    fireEvent.click(botonDeGoogle())

    expect(await screen.findByRole('button', { name: 'Continuar con Correo Ciencias' })).toBeDisabled()
  })

  it('el botón secundario sigue llevando al login con correo y contraseña', async () => {
    montar(vi.fn().mockResolvedValue(undefined))

    fireEvent.click(screen.getByRole('button', { name: 'Entrar con correo y contraseña' }))

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })

  it('mientras la sesión se resuelve muestra el spinner y no la landing', () => {
    montar(vi.fn(), { status: 'loading' })

    expect(screen.getByLabelText('Cargando')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Continuar con Correo Ciencias' })).not.toBeInTheDocument()
  })

  it('con sesión ya iniciada y sin ruta intentada redirige a Home', () => {
    montar(vi.fn(), { status: 'authenticated' })

    expect(screen.getByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Continuar con Correo Ciencias' })).not.toBeInTheDocument()
  })

  it('con sesión ya iniciada honra la ruta que el usuario intentó abrir', () => {
    montar(vi.fn(), {
      status: 'authenticated',
      entrada: { pathname: '/', state: { from: { pathname: '/sae/asesorias', search: '', hash: '' } } },
    })

    expect(screen.getByText('área SAE')).toBeInTheDocument()
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Reescribir `Login.test.tsx`**

Reemplazar el contenido completo de `frontend/src/screens/Login.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { InitialEntry } from 'react-router-dom'
import { Login } from './Login'
import * as auth from '../auth/AuthContext'
import { ApiError } from '../api/client'

type Estado = 'loading' | 'authenticated' | 'unauthenticated'

interface Dobles {
  loginWithPassword?: (email: string, password: string) => Promise<void>
  loginWithGoogle?: () => Promise<void>
  status?: Estado
  /** Entrada inicial del router: string o `{ pathname, state }` para simular el `from` del guard. */
  entrada?: InitialEntry
}

function montar({
  loginWithPassword = vi.fn(),
  loginWithGoogle = vi.fn(),
  status = 'unauthenticated',
  entrada = '/login',
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
    <MemoryRouter initialEntries={[entrada]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<p>pantalla home</p>} />
        <Route path="/sae/asesorias" element={<p>área SAE</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function llenarCredenciales() {
  fireEvent.change(screen.getByLabelText('Correo'), {
    target: { value: 'ana@ciencias.unam.mx' },
  })
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'ClaveSegura123!' } })
}

describe('Login', () => {
  afterEach(() => vi.restoreAllMocks())

  it('los campos tienen label asociado y foco visible', () => {
    montar()

    const correo = screen.getByLabelText('Correo')
    expect(correo).toBeInTheDocument()
    expect(correo).toHaveClass('focus-visible:outline-2')
    expect(screen.getByLabelText('Contraseña')).toHaveClass('focus-visible:outline-primary')
  })

  it('envía las credenciales y deja la redirección al guard', async () => {
    const loginWithPassword = vi.fn().mockResolvedValue(undefined)
    montar({ loginWithPassword })

    llenarCredenciales()
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() =>
      expect(loginWithPassword).toHaveBeenCalledWith('ana@ciencias.unam.mx', 'ClaveSegura123!'),
    )
    // Ya no hay navigate('/home') en la pantalla: con el doble de useAuth fijo
    // en 'unauthenticated' el formulario se queda, y el guard es quien mueve.
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('muestra el mensaje de credenciales inválidas cuando el backend responde 400', async () => {
    montar({
      loginWithPassword: vi.fn().mockRejectedValue(new ApiError(400, { non_field_errors: ['x'] })),
    })

    llenarCredenciales()
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('el botón de Google usa loginWithGoogle', async () => {
    const loginWithGoogle = vi.fn().mockResolvedValue(undefined)
    montar({ loginWithGoogle })

    fireEvent.click(screen.getByRole('button', { name: 'Continuar con Correo Ciencias' }))

    await waitFor(() => expect(loginWithGoogle).toHaveBeenCalledTimes(1))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('si el login con Google falla, muestra el error y no navega', async () => {
    montar({ loginWithGoogle: vi.fn().mockRejectedValue(new Error('popup cerrado')) })

    fireEvent.click(screen.getByRole('button', { name: 'Continuar con Correo Ciencias' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo iniciar sesión con Google.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })

  it('mientras la sesión se resuelve muestra el spinner y no el formulario', () => {
    montar({ status: 'loading' })

    expect(screen.getByLabelText('Cargando')).toBeInTheDocument()
    expect(screen.queryByLabelText('Correo')).not.toBeInTheDocument()
  })

  it('con sesión ya iniciada y sin ruta intentada redirige a Home', () => {
    montar({ status: 'authenticated' })

    expect(screen.getByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByLabelText('Correo')).not.toBeInTheDocument()
  })

  it('con sesión ya iniciada honra la ruta que el usuario intentó abrir', () => {
    montar({
      status: 'authenticated',
      entrada: { pathname: '/login', state: { from: { pathname: '/sae/asesorias', search: '', hash: '' } } },
    })

    expect(screen.getByText('área SAE')).toBeInTheDocument()
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 7: Correr los dos tests y verificar que fallan**

Run: `npx vitest run src/screens/Landing.test.tsx src/screens/Login.test.tsx`
Expected: FAIL — en ambos archivos el caso "honra la ruta que el usuario intentó abrir" falla (hoy el guard hardcodea `/home`, así que aparece "pantalla home" y no "área SAE"). Los demás casos pasan, incluidos los reinterpretados: `navigate('/home')` todavía existe, pero sus aserciones ya no dependen de él.

- [ ] **Step 8: Implementar el guard en `Landing.tsx`**

Reemplazar las líneas 1-32 de `frontend/src/screens/Landing.tsx` por:

```tsx
import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Boton } from '../components/ui/Boton'
import { PantallaCargando } from '../components/PantallaCargando'
import { useAuth } from '../auth/AuthContext'
import { destinoPostLogin } from '../auth/destinoPostLogin'

export function Landing() {
  const navigate = useNavigate()
  const location = useLocation()
  const { loginWithGoogle, status } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Todos los hooks quedan arriba: las salidas tempranas van después, para no
  // romper el orden de hooks entre renders.
  if (status === 'loading') return <PantallaCargando />
  // Único dueño de la redirección post-autenticación. Antes también navegaba
  // `handleGoogleLogin`, con destino fijo /home: dos mecanismos para lo mismo,
  // y el que corría primero se comía el deep link que guardó la guarda de ruta.
  if (status === 'authenticated') {
    return <Navigate to={destinoPostLogin(location.state)} replace />
  }

  // Mismo flujo, mismo manejo de carga/error y mismo copy de error que
  // Login.tsx: son dos entradas a la misma acción, no dos comportamientos.
  async function handleGoogleLogin() {
    setError(null)
    setConectandoGoogle(true)
    try {
      await loginWithGoogle()
    } catch {
      setError('No se pudo iniciar sesión con Google.')
    } finally {
      setConectandoGoogle(false)
    }
  }
```

El resto del archivo (el `return` con el JSX, a partir de `return (` en la línea 34 original) no se toca. `navigate` sigue en uso: el botón secundario lleva a `/login`.

- [ ] **Step 9: Implementar el guard en `Login.tsx`**

En `frontend/src/screens/Login.tsx`, reemplazar la línea 2 por:

```tsx
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
```

Añadir tras la línea 6 (el import de `PantallaCargando`):

```tsx
import { destinoPostLogin } from '../auth/destinoPostLogin'
```

Y reemplazar las líneas 41-83 (desde `export function Login() {` hasta la llave de cierre de `handleGoogleLogin`) por:

```tsx
export function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { loginWithPassword, loginWithGoogle, status } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Mismo guard que Landing: son dos entradas a la misma acción, y es el único
  // lugar que decide a dónde va el usuario una vez autenticado.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'authenticated') {
    return <Navigate to={destinoPostLogin(location.state)} replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await loginWithPassword(email, password)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? 'Correo o contraseña incorrectos.'
          : 'No se pudo iniciar sesión. Intenta de nuevo.',
      )
    } finally {
      setEnviando(false)
    }
  }

  async function handleGoogleLogin() {
    setError(null)
    setConectandoGoogle(true)
    try {
      await loginWithGoogle()
    } catch {
      setError('No se pudo iniciar sesión con Google.')
    } finally {
      setConectandoGoogle(false)
    }
  }
```

El resto del archivo (el `return` con el JSX) no se toca. `navigate` sigue en uso: el botón de flecha del encabezado hace `navigate(-1)`.

- [ ] **Step 10: Correr los tests y verificar que pasan**

Run: `npx vitest run src/screens/Landing.test.tsx src/screens/Login.test.tsx src/auth/destinoPostLogin.test.ts`
Expected: PASS — 7 casos en Landing, 8 en Login, 6 en el helper.

- [ ] **Step 11: Fijar el contrato extremo a extremo en `RutaProtegida.test.tsx`**

Este caso comprueba que lo que la guarda guarda en `state.from` es exactamente lo que `destinoPostLogin` sabe leer: es la costura entre las dos mitades del arreglo, y hoy nadie la cubre.

En `frontend/src/auth/RutaProtegida.test.tsx`, reemplazar las líneas 1-7 por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { RutaDeAsesor, RutaDeAsesorias, RutaDeSAE } from './RutaProtegida'
import { destinoPostLogin } from './destinoPostLogin'
import * as client from '../api/client'
import { usuarioDePrueba, usuarioSAE } from '../test/factories'
```

Y añadir al final del archivo (después del `describe('RutaDeSAE', ...)`):

```tsx
/** Stand-in de `/login`: muestra el destino que el guard de Landing/Login calcularía. */
function SondaDeLogin() {
  const location = useLocation()
  return <p>destino: {destinoPostLogin(location.state)}</p>
}

describe('deep link tras la guarda', () => {
  afterEach(() => vi.restoreAllMocks())

  it('la ruta intentada viaja en state.from y destinoPostLogin la recupera', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(
      new client.ApiError(401, { detail: 'no autenticado' }),
    )

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
            <Route path="/login" element={<SondaDeLogin />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    )

    expect(await screen.findByText('destino: /sae/asesorias')).toBeInTheDocument()
  })
})
```

- [ ] **Step 12: Correr `RutaProtegida.test.tsx` y verificar que pasa**

Run: `npx vitest run src/auth/RutaProtegida.test.tsx`
Expected: PASS (12 casos: los 11 previos más el nuevo). **Este caso pasa desde el primer intento** — la guarda ya guardaba `state.from` y el helper ya existe desde el Step 3. Es un test de contrato, no de comportamiento nuevo: si alguien borra el `state={{ from: location }}` de `RutaProtegida.tsx`, este caso lo atrapa.

- [ ] **Step 13: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 14: Commit**

```bash
git add frontend/src/auth/destinoPostLogin.ts frontend/src/auth/destinoPostLogin.test.ts frontend/src/auth/RutaProtegida.test.tsx frontend/src/screens/Landing.tsx frontend/src/screens/Landing.test.tsx frontend/src/screens/Login.tsx frontend/src/screens/Login.test.tsx
git commit -m "[fix][frontend] el guard de sesion honra la ruta intentada y es el unico que redirige

- destinoPostLogin: traduce el state.from de las guardas a la URL post-login
- filtra lo que no es ruta interna y evita el rebote a / y /login; fallback /home
- Landing y Login redirigen con ese destino y dejan de llamar navigate('/home')
- tests: deep link a /sae/asesorias en ambas entradas y contrato de state.from

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Componente `BotonVolver` (M5, parte 1 de 3)

**Files:**
- Create: `frontend/src/components/BotonVolver.tsx`
- Create: `frontend/src/components/BotonVolver.test.tsx`

**Interfaces:**
- Consumes: `useNavigate()` de `react-router-dom`.
- Produces: `BotonVolver(props: BotonVolverProps): JSX.Element`, con

  ```ts
  type BotonVolverProps =
    | { etiqueta: string; a: string; onClick?: never }
    | { etiqueta: string; a?: never; onClick: () => void }
  ```

  `etiqueta` es a la vez el texto y el nombre accesible (incluye la flecha: `'← Volver a Asesorías'`). `a` es la ruta destino; `onClick` es un handler propio para los regresos que no son una ruta fija. La unión discriminada hace que pasar ambos —o ninguno— sea un error de `tsc`. Lo consumen las Tasks 4 y 5.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/components/BotonVolver.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { BotonVolver } from './BotonVolver'

function montar(elemento: React.ReactNode) {
  render(
    <MemoryRouter initialEntries={['/origen']}>
      <Routes>
        <Route path="/origen" element={elemento} />
        <Route path="/destino" element={<p>pantalla destino</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('BotonVolver', () => {
  it('usa la etiqueta como texto y como nombre accesible', () => {
    montar(<BotonVolver etiqueta="← Volver a Asesorías" a="/destino" />)

    expect(screen.getByRole('button', { name: '← Volver a Asesorías' })).toHaveTextContent(
      '← Volver a Asesorías',
    )
  })

  it('en modo destino navega a la ruta de `a`', () => {
    montar(<BotonVolver etiqueta="← Atrás" a="/destino" />)

    fireEvent.click(screen.getByRole('button', { name: '← Atrás' }))

    expect(screen.getByText('pantalla destino')).toBeInTheDocument()
  })

  it('en modo handler ejecuta `onClick` y no navega', () => {
    const volver = vi.fn()
    montar(<BotonVolver etiqueta="← Atrás" onClick={volver} />)

    fireEvent.click(screen.getByRole('button', { name: '← Atrás' }))

    expect(volver).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('pantalla destino')).not.toBeInTheDocument()
  })

  it('trae el toque mínimo y el foco visible', () => {
    montar(<BotonVolver etiqueta="← Inicio" a="/destino" />)

    const boton = screen.getByRole('button', { name: '← Inicio' })
    expect(boton).toHaveClass('foco-visible', 'min-h-11', 'w-fit', 'text-sm', 'text-primary')
    expect(boton).toHaveAttribute('type', 'button')
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/components/BotonVolver.test.tsx`
Expected: FAIL — no existe el módulo `./BotonVolver`.

- [ ] **Step 3: Implementar el componente**

Crear `frontend/src/components/BotonVolver.tsx`:

```tsx
import { useNavigate } from 'react-router-dom'

/**
 * Botón de regreso de las pantallas internas.
 *
 * El mismo `<button className="foco-visible w-fit min-h-11 text-sm text-primary">`
 * estaba copiado en 15 lugares, con cuatro variantes de className que se
 * habían ido separando entre sí (dos sin `min-h-11`, dos sin `foco-visible`).
 * Aquí el estilo vive una vez y las pantallas sólo dicen qué etiqueta usan y a
 * dónde llevan.
 *
 * Dos modos, excluyentes por tipo:
 * - destino: `a="/asesorias"` — el caso común, navegación a una ruta fija.
 * - handler: `onClick={volver}` — para los regresos que no son una ruta, como
 *   el wizard de agendado, que retrocede de paso en paso antes de salir.
 */
type BotonVolverProps =
  | { etiqueta: string; a: string; onClick?: never }
  | { etiqueta: string; a?: never; onClick: () => void }

export function BotonVolver({ etiqueta, a, onClick }: BotonVolverProps) {
  const navigate = useNavigate()

  function alHacerClick() {
    if (onClick !== undefined) return onClick()
    if (a !== undefined) navigate(a)
  }

  return (
    <button
      type="button"
      onClick={alHacerClick}
      className="foco-visible w-fit min-h-11 rounded-md text-sm text-primary"
    >
      {etiqueta}
    </button>
  )
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/BotonVolver.test.tsx`
Expected: PASS (4 casos).

- [ ] **Step 5: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/BotonVolver.tsx frontend/src/components/BotonVolver.test.tsx
git commit -m "[feat][frontend] componente BotonVolver compartido

- un solo boton de regreso con el className que estaba copiado en 15 sitios
- dos modos excluyentes por tipo: destino (a=ruta) y handler (onClick)
- className canonico: foco-visible, min-h-11 y rounded-md para todos

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: Migrar a `BotonVolver` las pantallas de alumno y asesor (M5, parte 2 de 3)

**Depends on:** Task 3 (`components/BotonVolver`).

**Files:**
- Modify: `frontend/src/features/asesorias/screens/Asesorias.tsx:1-11, 34-39`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx:1-12, 81-101`
- Modify: `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx:1-5, 50-55`
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx:1-19, 34-51`
- Modify: `frontend/src/features/asesorias/screens/MisMaterias.tsx:1-12, 24-27, 110-118`
- Modify: `frontend/src/features/asesorias/screens/MiHorario.tsx:1-9, 99-100, 264-272`
- Modify: `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx:1-29`

**Interfaces:**
- Consumes: `BotonVolver` (Task 3), con la firma `{ etiqueta: string; a: string } | { etiqueta: string; onClick: () => void }`.
- Produces: nada nuevo. Los nombres accesibles `"← Inicio"`, `"← Volver a Asesorías"`, `"← Atrás"` y el prop `etiquetaVolver` de `OfertaAsesorias` quedan **idénticos**; los tests existentes que los consultan por `name` son la red de seguridad de esta task.

- [ ] **Step 1: Fijar la línea base — la suite debe estar verde antes de tocar nada**

Run: `npx vitest run src/features/asesorias`
Expected: PASS. Es una refactorización: los tests que consultan `'← Inicio'`, `'← Volver a Asesorías SAE'` y compañía ya existen (`Asesorias.test.tsx:76`, `OfertaAsesorias.test.tsx:95,113`) y deben seguir pasando **sin modificarse** al terminar. Si algo está rojo aquí, para y repórtalo: no es culpa de esta task.

- [ ] **Step 2: Migrar `Asesorias.tsx`**

Añadir tras la línea 8 (el import de `Skeleton`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Y reemplazar las líneas 34-39 por:

```tsx
  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <BotonVolver etiqueta="← Inicio" a="/home" />
      <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>
```

`navigate` sigue en uso en el `useEffect` de la línea 30: **no** se toca su declaración.

- [ ] **Step 3: Migrar `AgendarAsesoria.tsx`**

Añadir tras la línea 7 (el import de `useMapaCarreras, useMapaMaterias`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Reemplazar la línea 84 por:

```tsx
        <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

Reemplazar la línea 93 por:

```tsx
        <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

Reemplazar la línea 101 por:

```tsx
      <BotonVolver etiqueta="← Atrás" onClick={volver} />
```

`navigate` sigue en uso dentro de la función `volver` (línea 48) y en el agendado: **no** se toca su declaración.

- [ ] **Step 4: Migrar `OfertaAsesorias.tsx`**

Añadir tras la línea 5 (el import de `Skeleton`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Y reemplazar las líneas 50-55 por:

```tsx
  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <BotonVolver etiqueta={etiquetaVolver} a={rutaVolver} />
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>
```

Los props `rutaVolver` y `etiquetaVolver` de `OfertaAsesoriasProps` (líneas 7-16) y sus defaults (líneas 25-26) **no se tocan**: `App.tsx:88-93` depende de ese contrato. `navigate` sigue en uso para `baseRutaMateria`.

- [ ] **Step 5: Migrar `DetalleAsesoria.tsx`**

Reemplazar la línea 2 por:

```tsx
import { useParams } from 'react-router-dom'
```

Añadir tras la línea 9 (el import de `Retroalimentacion`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Borrar la línea 19 completa (`  const navigate = useNavigate()`): es su única razón de existir aquí, y con `noUnusedLocals` en `true` dejarla rompe `npm run build`.

Reemplazar las líneas 38-40 por:

```tsx
        <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

Reemplazar las líneas 49-51 por:

```tsx
      <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

- [ ] **Step 6: Migrar `MisMaterias.tsx`**

Borrar la línea 2 completa (`import { useNavigate } from 'react-router-dom'`) — junto con la línea en blanco que la sigue queda una sola línea en blanco tras el import de `react`.

Añadir el import nuevo respetando el orden alfabético del bloque, justo antes del import de `IconBasura`:

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Borrar la línea 27 completa (`  const navigate = useNavigate()`).

Y reemplazar las líneas 112-118 por:

```tsx
      <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

- [ ] **Step 7: Migrar `MiHorario.tsx`**

Borrar la línea 2 completa (`import { useNavigate } from 'react-router-dom'`).

Añadir el import nuevo justo antes del import de `IconPresencial, IconVirtual`:

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Borrar la línea 100 completa (`  const navigate = useNavigate()`).

Y reemplazar las líneas 266-272 por:

```tsx
      <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

- [ ] **Step 8: Migrar `SinRegistroAsesor.tsx`**

Este archivo usa el alias `@/` para sus imports de `components/`; se mantiene por consistencia interna. Reemplazar las líneas 1-6 por:

```tsx
import { useState } from 'react'

import { BotonVolver } from '@/components/BotonVolver'
import { Boton } from '@/components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '@/components/ui/Retroalimentacion'
import { useCrearRegistro } from '../api'
```

Borrar la línea 15 completa (`  const navigate = useNavigate()`).

Y reemplazar las líneas 22-28 por:

```tsx
      <BotonVolver etiqueta="← Volver a Asesorías" a="/asesorias" />
```

- [ ] **Step 9: Correr los tests de la feature y verificar que siguen verdes**

Run: `npx vitest run src/features/asesorias`
Expected: PASS — exactamente los mismos casos del Step 1, sin haber tocado ningún archivo `.test.tsx`. Si `'← Inicio'` o `'← Volver a Asesorías SAE'` dejaron de encontrarse, la etiqueta se transcribió mal (ojo con la flecha `←` U+2190 y el espacio que la sigue).

- [ ] **Step 10: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS. `tsc -b` es aquí la verificación clave: atrapa cualquier `navigate` o `useNavigate` que haya quedado sin uso.

- [ ] **Step 11: Commit**

```bash
git add frontend/src/features/asesorias/screens/Asesorias.tsx frontend/src/features/asesorias/screens/AgendarAsesoria.tsx frontend/src/features/asesorias/screens/OfertaAsesorias.tsx frontend/src/features/asesorias/screens/DetalleAsesoria.tsx frontend/src/features/asesorias/screens/MisMaterias.tsx frontend/src/features/asesorias/screens/MiHorario.tsx frontend/src/features/asesorias/components/SinRegistroAsesor.tsx
git commit -m "[refactor][frontend] migrar a BotonVolver las pantallas de alumno y asesor

- 10 botones de regreso en 7 archivos pasan al componente compartido
- DetalleAsesoria gana foco visible y toque minimo, que le faltaban
- se retiran los useNavigate que quedaron sin uso
- etiquetas y contratos de props intactos: los tests existentes no cambian

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: Migrar a `BotonVolver` las pantallas del área SAE (M5, parte 3 de 3)

**Depends on:** Task 3 (`components/BotonVolver`).

**Files:**
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorias.tsx:1-9, 22-27`
- Modify: `frontend/src/features/asesorias/screens/AdminAsesores.tsx:1-4, 20-28`
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx:1-6, 13-32`
- Modify: `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx:1-7, 16-40`
- Modify: `frontend/src/features/asesorias/screens/AdminDetalleAsesoria.tsx:1-3, 26-39`

**Interfaces:**
- Consumes: `BotonVolver` (Task 3).
- Produces: nada nuevo. Los nombres accesibles `"← Inicio"`, `"← Volver a Asesorías SAE"`, `"← Volver al directorio"` y `"← Volver a la oferta"` quedan **idénticos**; los tests existentes (`AdminAsesorias.test.tsx:129`, `AdminAsesorDetalle.test.tsx:139`, `AdminOfertaMateria.test.tsx:73`) son la red de seguridad.

- [ ] **Step 1: Fijar la línea base — la suite debe estar verde antes de tocar nada**

Run: `npx vitest run src/features/asesorias`
Expected: PASS. Igual que en la task anterior: ningún archivo `.test.tsx` se modifica en esta task.

- [ ] **Step 2: Migrar `AdminAsesorias.tsx`**

Añadir tras la línea 4 (el import de `Skeleton`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Y reemplazar las líneas 22-27 por:

```tsx
  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <BotonVolver etiqueta="← Inicio" a="/home" />
      <h1 className="text-lg font-semibold text-on-background">Asesorías · SAE</h1>
```

`navigate` sigue en uso en la línea 32 (`/sae/asesorias/oferta`): **no** se toca su declaración.

- [ ] **Step 3: Migrar `AdminAsesores.tsx`**

Añadir tras la línea 4 (el import de `Skeleton`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Y reemplazar las líneas 20-28 por:

```tsx
  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <BotonVolver etiqueta="← Volver a Asesorías SAE" a="/sae/asesorias" />
      <h1 className="text-lg font-semibold text-on-background">Asesores</h1>
```

`navigate` sigue en uso en la línea 61 (detalle del asesor): **no** se toca su declaración.

- [ ] **Step 4: Migrar `AdminAsesorDetalle.tsx`**

Reemplazar la línea 2 por:

```tsx
import { useParams } from 'react-router-dom'
```

Añadir tras la línea 4 (el import de `Skeleton`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Borrar la línea 16 completa (`  const navigate = useNavigate()`).

Y reemplazar las líneas 24-32 (la constante `volver`) por:

```tsx
  const volver = <BotonVolver etiqueta="← Volver al directorio" a="/sae/asesores" />
```

El resto del archivo sigue usando `{volver}` igual que antes: no hay más cambios.

- [ ] **Step 5: Migrar `AdminOfertaMateria.tsx`**

Reemplazar la línea 2 por:

```tsx
import { useParams } from 'react-router-dom'
```

Añadir tras la línea 6 (el import de `Skeleton`):

```tsx
import { BotonVolver } from '../../../components/BotonVolver'
```

Borrar la línea 19 completa (`  const navigate = useNavigate()`).

Y reemplazar las líneas 32-40 (la constante `volver`) por:

```tsx
  const volver = <BotonVolver etiqueta="← Volver a la oferta" a="/sae/asesorias/oferta" />
```

El resto del archivo sigue usando `{volver}` igual que antes.

- [ ] **Step 6: Migrar `AdminDetalleAsesoria.tsx`**

Reemplazar las líneas 1-3 por:

```tsx
import { useLocation } from 'react-router-dom'
import { BotonVolver } from '../../../components/BotonVolver'
import { InsigniaEstado } from '../../../components/ui/InsigniaEstado'
import type { AsesoriaAdmin } from '../../../api/types'
```

Borrar la línea 27 completa (`  const navigate = useNavigate()`).

Y reemplazar las líneas 31-39 (la constante `volver`) por:

```tsx
  const volver = <BotonVolver etiqueta="← Volver a Asesorías SAE" a="/sae/asesorias" />
```

El resto del archivo sigue usando `{volver}` igual que antes.

- [ ] **Step 7: Correr los tests de la feature y verificar que siguen verdes**

Run: `npx vitest run src/features/asesorias`
Expected: PASS — los mismos casos del Step 1, sin haber tocado ningún archivo `.test.tsx`.

- [ ] **Step 8: Verificar que no queda ninguna copia del className**

Run: `grep -rn "w-fit min-h-11 text-sm text-primary\|w-fit rounded-md text-sm text-primary\|min-h-11 w-fit text-sm text-primary" src/`
Expected: sin resultados (exit code 1). El único lugar donde vive ese conjunto de clases es ahora `src/components/BotonVolver.tsx`, y ahí el orden es `foco-visible w-fit min-h-11 rounded-md text-sm text-primary`, que ninguno de los tres patrones buscados encaja.

- [ ] **Step 9: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminAsesorias.tsx frontend/src/features/asesorias/screens/AdminAsesores.tsx frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx frontend/src/features/asesorias/screens/AdminDetalleAsesoria.tsx
git commit -m "[refactor][frontend] migrar a BotonVolver las pantallas del area SAE

- 5 botones de regreso en 5 archivos pasan al componente compartido
- se retiran los useNavigate que quedaron sin uso
- ya no queda ninguna copia del className del boton de regreso en el codigo
- etiquetas intactas: los tests existentes no cambian

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Verificación final

- [ ] **Suite completa, build y lint desde `frontend/`**

Run: `npm test && npm run build && npm run lint`
Expected: PASS, sin tests saltados.

- [ ] **El className duplicado ya no existe fuera del componente**

Run: `grep -rln "text-sm text-primary" src/ | grep -v BotonVolver`
Expected: sólo archivos donde `text-sm text-primary` pertenece a otro control (p. ej. el `+ Agregar` de `MisMaterias.tsx:128` o el botón de oferta de `AdminAsesorias.tsx:33`), nunca a un botón cuyo texto empiece con `←`.

- [ ] **Repaso manual** (con `npm run dev`):
  1. Con sesión: `/home` → hamburguesa → "Cerrar sesión" → cae en `/`; el botón Atrás del navegador **no** regresa a `/home`.
  2. Sin sesión, abrir directamente `/sae/asesorias` → aterriza en `/login` → iniciar sesión (siendo SAE) → aterriza en **`/sae/asesorias`**, no en `/home`.
  3. Sin sesión, abrir `/` → iniciar sesión → aterriza en `/home`.
  4. Recorrer los botones "←" de: `/asesorias`, `/asesorias/nueva`, `/asesorias/nueva/:id` (los tres pasos), `/asesorias/materias`, `/asesorias/horario`, `/sae/asesorias`, `/sae/asesorias/oferta`, `/sae/asesores`, `/sae/asesores/:id` — cada uno con el mismo aspecto y su destino de siempre.
  5. Navegar con Tab hasta un botón "←": el anillo de foco es visible y el área táctil llega a 44 px.

---

## Self-review

**1. Cobertura del alcance**

| Requisito | Task | Steps |
|---|---|---|
| M1 — logout terminal (`navigate('/', { replace: true })`) | Task 1 | 1 (test), 3 (impl) |
| M1 — el test de cerrar sesión sigue verde | Task 1 | 4 (los 6 casos previos siguen ahí) |
| M2 — quitar `navigate('/home')` de `Landing.tsx` | Task 2 | 8 |
| M2 — quitar los dos `navigate('/home')` de `Login.tsx` | Task 2 | 9 |
| M2 — tests de Landing/Login actualizados con intención | Task 2 | 5, 6 |
| M3 — el guard lee `location.state.from` con fallback a `/home` | Task 2 | 3 (helper), 8, 9 (guards) |
| M3 — tipo del state definido | Task 2 | 3 (`EstadoDeRedireccion`) |
| M3 — caso deep-link `/sae/asesorias` sin sesión → login → aterriza ahí | Task 2 | 5, 6 (Landing y Login), 11 (contrato de la guarda) |
| M3 — caso sin `from` → `/home` | Task 2 | 1 (helper), 5, 6 |
| M3 — `unauthenticated` sin cambios | Task 2 | 5, 6 (los casos de login/error siguen sobre `unauthenticated`) |
| M4 — `aria-haspopup` (decisión: quitarlo) | Task 1 | 1, 3 + Decisión de alcance 1 |
| M4 — `aria-controls` sólo con el panel abierto (opcional: entra) | Task 1 | 1, 3 + Decisión de alcance 2 |
| M5 — componente `BotonVolver` con los dos modos | Task 3 | 1, 3 |
| M5 — prior art `etiquetaVolver` respetado | Task 4 | 4 (props de `OfertaAsesorias` intactos; `App.tsx` no se toca) |
| M5 — migrar los 15 botones de los 12 archivos | Tasks 4 y 5 | Task 4 steps 2-8 (10 botones / 7 archivos), Task 5 steps 2-6 (5 botones / 5 archivos) |
| M5 — nombres accesibles preservados exactamente | Tasks 4 y 5 | Steps 1 y 9 / 1 y 7: los `.test.tsx` no se modifican |
| M5 — `Login.tsx:87` (`navigate(-1)`) fuera de alcance | — | Decisión de alcance 3 |
| Restricción: sin ADR ni ítem de deuda | — | Global Constraints |

Sin huecos: M1–M5 tienen task, y las dos decisiones bloqueadas por el usuario (honrar `state.from`, migrar todos los sitios) están implementadas, no discutidas.

**2. Sin placeholders**

Cada step que toca código trae el código completo y las rutas con números de línea verificados contra el estado actual de `dev` (`691c496`). No hay "similar a la Task N", ni tests descritos en prosa, ni "manejar los casos borde".

**3. Consistencia de tipos y nombres**

- `destinoPostLogin(state: unknown): string` y `DESTINO_POR_DEFECTO` — definidos en Task 2 Step 3; usados con esos nombres exactos en Step 1 (tests), Step 8 (`Landing.tsx`), Step 9 (`Login.tsx`) y Step 11 (`RutaProtegida.test.tsx`).
- `EstadoDeRedireccion.from` — `{ pathname?, search?, hash? }`, compatible con el `location` completo que `RutaProtegida.tsx:16,31,46` pone en `state={{ from: location }}` (un `Location` de React Router tiene esas tres propiedades como `string`).
- `BotonVolver` — props `etiqueta`, `a`, `onClick`; el nombre `a` se usa igual en Task 3 (definición y tests) y en las 15 invocaciones de las Tasks 4 y 5; `onClick` se usa en una sola invocación real (`AgendarAsesoria.tsx:101`, `onClick={volver}`), la que la unión discriminada exige que no lleve `a`.
- `etiquetaVolver` / `rutaVolver` — props existentes de `OfertaAsesorias`; no cambian de nombre ni de default (`'← Volver a Asesorías'`, `'/asesorias'`), así que `App.tsx:88-93` sigue compilando sin tocarse.
- `status` — el tipo `'loading' | 'authenticated' | 'unauthenticated'` de los helpers de test coincide con `EstadoSesion` de `AuthContext.tsx:7`.
- `InitialEntry` — tipo exportado por `react-router-dom`, importado como `import type` en los dos helpers de test de la Task 2.
- Nombres accesibles, escritos idénticos en implementación y aserciones: `"Menú"`, `"Cerrar sesión"`, `"atrás de prueba"`, `"Cargando"`, `"Continuar con Correo Ciencias"`, `"Entrar"`, `"Entrar con correo y contraseña"`, `"← Inicio"`, `"← Atrás"`, `"← Volver a Asesorías"`, `"← Volver a Asesorías SAE"`, `"← Volver al directorio"`, `"← Volver a la oferta"`.
- Textos de sonda usados en `Routes` de prueba: `"pantalla home"`, `"pantalla landing"`, `"pantalla login"`, `"área SAE"`, `"pantalla destino"`, `"destino: /sae/asesorias"`.
