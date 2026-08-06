# Frontend — Login con `id_token` (ADR 0019), rol desde el contrato de `/api/auth/user/` y fix de `Landing.tsx` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ejecutar en `frontend/` lo que la [spec de login del paso 2](../specs/2026-08-04-login-oauth-design.md) y [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md) ya decidieron: el SPA obtiene un **ID token** de Google (no un `access_token` OAuth), consume el perfil/rol que el plan de backend expone en `/api/auth/user/` en vez de sondear endpoints por rol, y el botón "Continuar con Correo Ciencias" de `Landing.tsx` deja de navegar a `/home` sin haber iniciado sesión.

**Architecture:** Tres capas, de adentro hacia afuera, más una de pulido. (1) **Contrato de datos:** `api/types.ts` gana la forma exacta del payload de usuario que produce `accounts.serializers.UserDetailsSerializer` (Task 3 del plan de backend) y `AuthContext` la expone, incluyendo un valor derivado `roles` que es el único punto de tolerancia a un backend que todavía no lo manda. (2) **Transporte:** `auth/google.ts` cambia de `google.accounts.oauth2.initTokenClient` (autorización OAuth, `access_token`) a `google.accounts.id` (autenticación OIDC, `credential`/`id_token`), y `loginWithGoogle` manda `{id_token}`. (3) **Consumo de rol:** `auth/rol.ts` deja de sondear `GET /api/asesorias/registros/` y lee `roles` del contexto; `RutaProtegida.tsx` se simplifica porque ya no hay una segunda fuente de "cargando". (4) **Pantallas:** `Landing.tsx` invoca el login real, `Login.tsx` gana el foco visible que el paso 7 exige, y los dos pasan a componer el `Boton` compartido en vez de repetir sus clases.

**Tech Stack:** React 19, TypeScript 6, Vite 8, Tailwind CSS v4.3 (CSS-first, sin `tailwind.config.js`), React Router 7, Vitest 4 + Testing Library (`@testing-library/react` 16, `jest-dom` 7; **no** hay `@testing-library/user-event`, así que todos los tests usan `fireEvent`), `pnpm`, `oxlint`, Google Identity Services (script `https://accounts.google.com/gsi/client`, sin paquete npm).

---

## Global Constraints

- **Todos los comandos de este plan se corren desde `frontend/`.** `pnpm test <ruta>` corre un archivo; `pnpm test` corre la suite completa; `pnpm build` es `tsc -b && vite build`; `pnpm lint` es `oxlint`.
- **No se toca `backend/`.** Este plan es exclusivamente frontend (más documentación compartida en la Task 7).
- **Dependencia dura del plan de backend del paso 4, escrito y NO ejecutado** (`docs/superpowers/plans/2026-08-04-login-oauth-backend.md`). Dos contratos que este plan consume no existen todavía en `dev-frontend`:
  - `POST /api/auth/google/` hoy **exige** `access_token` y rechaza `id_token` solo (Task 1 de ese plan lo invierte). Después de la Task 2 de *este* plan, **el login con Google no funciona en runtime** hasta que esa task de backend se ejecute.
  - `GET /api/auth/user/` hoy devuelve `{pk, email, first_name}` sin `roles` (Task 3 de ese plan lo cambia). Después de la Task 3 de *este* plan, `useEsAsesor()` devuelve `false` para todo el mundo, así que **las rutas `/asesorias*` redirigen a `/home`** hasta que esa task de backend se ejecute.
  - **Los tests de este plan mockean esas respuestas y no tocan red, así que la suite pasa igual.** No inventes un fallback, no cambies el contrato, no "arregles" la redirección. Es el mismo criterio que ya tomó el plan del paso 8 con los tres endpoints de asesorías. La consecuencia operativa está en la Decisión 6 del final: **este plan y las Tasks 1-3 del plan de backend deben ejecutarse y desplegarse como una sola unidad.**
- **Este plan NO depende de que el plan del paso 8 (componentes) se haya ejecutado.** No usa `Dialogo`, `dialog.tsx`, `tabs.tsx`, el alias `@/`, `cn()` ni la clase `.foco-visible` — login no usa diálogos ni pestañas. Tampoco toca ninguno de los archivos que ese plan modifica (`index.css`, `components.json`, los 4 diálogos, `vite.config.ts`, los `tsconfig`). El único punto de contacto es `components/ui/Boton.tsx`, que el plan del paso 8 declara explícitamente **intocado** por su decisión 5 — así que la Task 4 de este plan no pisa nada de ese plan. Los dos planes pueden ejecutarse en cualquier orden.
- **Imports relativos**, como todo `src/` hoy (`'../components/ui/Boton'`). El alias `@/` lo introduce el plan del paso 8; usarlo aquí crearía una dependencia de orden entre planes que la restricción anterior evita.
- **Foco visible (checklist del paso 7, `docs/development/contribuir-componentes.md`):** todo elemento interactivo que este plan cree o toque lleva exactamente `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary`. Ese trío produce el mismo CSS que la clase `.foco-visible` del paso 8 (`outline: 2px solid var(--color-primary); outline-offset: 2px`), sin tocar `index.css`. Ver Decisión 8.
- **Cero variables de entorno nuevas.** `VITE_GOOGLE_OAUTH_CLIENT_ID` (ya en `frontend/.env.example`) es la misma variable, el mismo Client ID; solo cambia qué función de la librería de Google la consume.
- **Cero dependencias nuevas.** Google Identity Services se carga como script, no como paquete. No se agrega `@testing-library/user-event` (no está instalado; los tests usan `fireEvent`).
- **Cero cambios de copy visible.** "Continuar con Correo Ciencias", "Entrar con correo y contraseña", "Entrar", "¿Olvidaste tu contraseña?", "Correo", "Contraseña" quedan idénticos. El único texto nuevo es el mensaje de error de `Landing.tsx`, que es **literalmente el mismo string** que ya usa `Login.tsx`: `'No se pudo iniciar sesión con Google.'`.
- **No se reabren decisiones ya tomadas.** El transporte (`id_token`, no `access_token`, no Authorization Code) está fijado por ADR 0019. El storage/transporte del JWT propio de Atenea (split dev/prod: `localStorage` + header en dev, cookie `httpOnly` en prod) está fijado por la decisión 2 de ADR 0018 y **no cambia** — `persistirSesion`/`limpiarSesion` y `api/client.ts` no se tocan salvo lo que diga un step explícito (no lo dice ninguno). El logout sin invalidación de refresh token (deuda 0007) y el CSRF en cookie JWT (deuda 0009, decisión 6 de la spec) no se tocan.
- **TDD estricto, commits atómicos.** Cada task escribe el test primero, lo corre para verlo fallar, implementa lo mínimo, lo corre para verlo pasar, y comitea.
- **Convención de commits del repo** (`docs/development/commit-conventions.md`, ADR 0007): `[type][scope] resumen` en la primera línea, bullets de detalle en el cuerpo, `Signed-off-by` generado con `git commit -s`. Tipos usados aquí: `feat`, `fix`, `refactor`, `docs`.
- **Trampa de tooling a tener presente todo el plan:** `tsconfig.app.json` tiene `"exclude": ["src/**/*.test.ts", "src/**/*.test.tsx"]`, y Vitest transpila sin typechecar. **Un error de tipos dentro de un archivo `.test.tsx` no lo detecta ni `pnpm build` ni `pnpm test`.** Por eso la Task 1 mete la fábrica de usuarios de prueba en `src/test/factories.ts` (que **sí** entra en `tsc -b`, porque no termina en `.test.ts`): es el único lugar donde la forma de `AuthUser` queda verificada por el compilador. En cambio `noUnusedLocals` **sí** está activo para el código de `src/`, así que dejar un import muerto en `rol.ts` o `Login.tsx` rompe `pnpm build`.

---

## File Structure

**Contrato de datos y contexto de sesión (Task 1)**

- **Modificar** `frontend/src/api/types.ts` — `AuthUser` pasa de `{pk, email, first_name}` a la forma completa del `UserDetailsSerializer` del backend; se agregan `RolUsuario`, `PerfilAlumno`, `PerfilAcademico`, `PerfilAsesorAcademico`.
- **Modificar** `frontend/src/auth/AuthContext.tsx` — `AuthContextValue` gana `roles`.
- **Crear** `frontend/src/test/factories.ts` — `usuarioDePrueba()`, la única fábrica de `AuthUser` de toda la suite.
- **Modificar** `frontend/src/auth/AuthContext.test.tsx` — se reescribe completo sobre la fábrica.

**Transporte de Google (Task 2)**

- **Modificar** `frontend/src/auth/google.ts` — `solicitarAccessTokenDeGoogle` desaparece; entra `solicitarIdTokenDeGoogle`. Cambia también la declaración global de `Window['google']`.
- **Crear** `frontend/src/auth/google.test.ts` — primer test de este archivo; hoy no tiene ninguno.
- **Modificar** `frontend/src/auth/AuthContext.tsx` — `loginWithGoogle` manda `{id_token}`.
- **Modificar** `frontend/src/auth/AuthContext.test.tsx` — test del payload exacto.

**Rol y guard de ruta (Task 3)**

- **Modificar** `frontend/src/auth/rol.ts` — se borra el sondeo con TanStack Query; `useEsAsesor()` lee el contexto y se agrega `useEsAlumno()`.
- **Modificar** `frontend/src/auth/rol.test.tsx` — se reescribe completo.
- **Modificar** `frontend/src/auth/RutaProtegida.tsx` — una sola fuente de "cargando".
- **Crear** `frontend/src/auth/RutaProtegida.test.tsx` — el guard no tiene test hoy.

**Botón compartido (Task 4)**

- **Modificar** `frontend/src/components/ui/Boton.tsx` — estado `:focus-visible`.
- **Crear** `frontend/src/components/ui/Boton.test.tsx` — primer test de un primitivo de `components/ui/`.

**Pantallas (Tasks 5 y 6)**

- **Modificar** `frontend/src/screens/Landing.tsx` + **Crear** `frontend/src/screens/Landing.test.tsx`.
- **Modificar** `frontend/src/screens/Login.tsx` + **Crear** `frontend/src/screens/Login.test.tsx`.

**Documentación (Task 7)**

- **Modificar** `docs/decisions/0019-transporte-login-google-id-token.md`, `docs/development/api-frontend.md`, `docs/development/contribuir-componentes.md`, `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md`, `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`.

**Por qué este orden.** El contrato de datos va primero aunque el titular del trabajo sea el transporte: la Task 2 y la Task 3 necesitan construir objetos `AuthUser` en sus mocks, y hacerlo antes de fijar la forma obligaría a reescribir esos mismos mocks una task después. `Boton` (Task 4) va antes de las dos pantallas porque las dos lo componen.

---

## Decisiones de diseño no fijadas por los specs

La spec del paso 2 y ADR 0019 fijaron el *qué*. Estas son las decisiones de *forma exacta* que toma este plan para ser ejecutable sin volver a diseño. Cada una está donde el checkpoint puede aceptarla o rechazarla por separado; el detalle con su razón está al final del documento.

| # | Decisión | Task |
|---|---|---|
| 1 | El `id_token` se pide con One Tap programático (`google.accounts.id.prompt()`), no con el botón renderizado de Google — es lo único que preserva la UX que la spec exige no cambiar. | 2 |
| 2 | `solicitarIdTokenDeGoogle` rechaza a los 60 s y llama `google.accounts.id.cancel()`, para que el botón no quede girando para siempre si One Tap no responde. | 2 |
| 3 | Los campos de perfil/rol son **obligatorios** en `AuthUser`, no opcionales; la tolerancia a un backend que aún no los manda vive en un solo punto (`user?.roles ?? []`). | 1 |
| 4 | El contexto expone `roles` derivado además de `user`, en vez de que cada consumidor escriba `user?.roles ?? []`. | 1 |
| 5 | `useEsAsesor()` devuelve `boolean` (ya no `{data, isPending}` de TanStack Query) y se agrega `useEsAlumno()`; **no** se agrega `useEsAsesorActivo()`. | 3 |
| 6 | Se elimina el sondeo de rol **sin fallback**, aunque el backend todavía no exponga `roles`. | 3 |
| 7 | La fábrica `usuarioDePrueba()` vive en `src/test/factories.ts` (compartida) y no local a cada archivo de test. | 1 |
| 8 | El foco visible se escribe con utilidades de Tailwind, no con la clase `.foco-visible` que introduce el plan del paso 8. | 4, 5, 6 |
| 9 | El foco entra **una sola vez** en `Boton.tsx`, y `Login`/`Landing` pasan a componer `Boton` en vez de repetir sus clases. | 4, 5, 6 |
| 10 | `Landing` no redirige automáticamente a `/home` cuando ya hay sesión: sigue siendo una pantalla pública. | 5 |
| 11 | La actualización de `docs/development/api-frontend.md` es condicional al estado del plan de backend, resuelta con un `grep`. | 7 |
| 12 | El mensaje de "no existe una cuenta para este correo" **no** se muestra tal cual: las pantallas conservan su copy genérico de error. | 5, 6 |

---

### Task 1: `AuthUser` trae perfil y rol, y el contexto los expone

Consume el contrato que fija la **Task 3 del plan de backend** (`accounts.serializers.UserDetailsSerializer`): el mismo serializer alimenta `GET /api/auth/user/` y la clave `"user"` del body de `POST /api/auth/login/` y `POST /api/auth/google/`, así que el rol llega **con el login mismo**, sin una segunda llamada. Esta task fija esa forma en TypeScript y la expone en el contexto; los tests la mockean, no tocan red.

Hoy `AuthUser` es `{pk, email, first_name}` (`frontend/src/api/types.ts:1-5`) y el contexto no expone nada de rol.

**Files:**
- Modify: `frontend/src/api/types.ts:1-5`
- Modify: `frontend/src/auth/AuthContext.tsx`
- Create: `frontend/src/test/factories.ts`
- Test: `frontend/src/auth/AuthContext.test.tsx` (reescritura completa)

**Interfaces:**
- Consumes: `apiGet`, `apiPost`, `ApiError` de `frontend/src/api/client.ts` (sin cambios); el contrato de respuesta de la Task 3 del plan de backend.
- Produces:
  - `api/types.ts`: `RolUsuario = 'alumno' | 'academico' | 'asesor_academico'`; `PerfilAlumno`, `PerfilAcademico`, `PerfilAsesorAcademico`; `AuthUser` con `pk`, `email`, `first_name`, `apellido1`, `apellido2`, `nombre_completo`, `roles: RolUsuario[]`, `perfil_alumno: PerfilAlumno | null`, `perfil_academico: PerfilAcademico | null`, `perfil_asesor_academico: PerfilAsesorAcademico | null`.
  - `auth/AuthContext.tsx`: `useAuth()` devuelve además `roles: RolUsuario[]` (`[]` si no hay sesión). Las Tasks 3, 5 y 6 lo consumen.
  - `src/test/factories.ts`: `usuarioDePrueba(overrides?: Partial<AuthUser>): AuthUser`. Las Tasks 2, 3 y 5 la consumen.

- [ ] **Step 1: Escribir la fábrica de usuarios de prueba**

Crear `frontend/src/test/factories.ts`:

```ts
import type { AuthUser } from '../api/types'

/**
 * Usuario con la forma exacta que devuelve `GET /api/auth/user/` y que viaja
 * en la clave `user` del body de login (mismo serializer del lado del
 * backend). Vive fuera de los archivos `.test.tsx` a propósito: `tsconfig.app.json`
 * excluye los tests de `tsc -b`, así que este es el único lugar donde el
 * compilador verifica que la forma sigue cuadrando con `AuthUser`.
 */
export function usuarioDePrueba(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    pk: 1,
    email: 'usuaria@ciencias.unam.mx',
    first_name: 'Ana',
    apellido1: 'López',
    apellido2: 'Ruiz',
    nombre_completo: 'Ana López Ruiz',
    roles: [],
    perfil_alumno: null,
    perfil_academico: null,
    perfil_asesor_academico: null,
    ...overrides,
  }
}
```

Este archivo **no compila todavía** (`AuthUser` aún no tiene esos campos). Es parte del RED.

- [ ] **Step 2: Escribir los tests del contexto — RED**

Reemplazar el contenido completo de `frontend/src/auth/AuthContext.test.tsx` por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import * as client from '../api/client'
import { usuarioDePrueba } from '../test/factories'
import type { AuthUser } from '../api/types'

function Sonda() {
  const { status, user, roles, loginWithPassword } = useAuth()
  return (
    <>
      <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
      <div data-testid="roles">{roles.join(',') || 'sin-roles'}</div>
      <button type="button" onClick={() => loginWithPassword('a@ciencias.unam.mx', 'x')}>
        Entrar con contraseña
      </button>
    </>
  )
}

function montar() {
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )
}

describe('AuthProvider', () => {
  afterEach(() => vi.restoreAllMocks())

  it('pasa a unauthenticated si /api/auth/user/ responde 401 al montar', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated:sin-usuario')
    })
    expect(screen.getByTestId('roles')).toHaveTextContent('sin-roles')
  })

  it('pasa a authenticated con el usuario si /api/auth/user/ responde ok', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ email: 'asesor@ciencias.unam.mx' }),
    )

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('authenticated:asesor@ciencias.unam.mx')
    })
  })

  it('expone los roles que trae el usuario autenticado', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_academico: { id: 7, numero_trabajador: '12345' },
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: true },
      }),
    )

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('roles')).toHaveTextContent('academico,asesor_academico')
    })
  })

  it('no revienta si la respuesta todavía no trae roles (backend previo al plan del paso 4)', async () => {
    // El contrato de `roles` lo agrega la Task 3 del plan de backend, aún sin
    // ejecutar. Mientras tanto la app debe arrancar autenticada y sin roles,
    // no romperse al leer una propiedad ausente.
    const usuarioViejo = { pk: 1, email: 'vieja@ciencias.unam.mx', first_name: 'Ana' } as unknown as AuthUser
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioViejo)

    montar()

    await waitFor(() => {
      expect(screen.getByTestId('estado')).toHaveTextContent('authenticated:vieja@ciencias.unam.mx')
    })
    expect(screen.getByTestId('roles')).toHaveTextContent('sin-roles')
  })

  it('el rol llega con el login mismo, sin una segunda llamada a /api/auth/user/', async () => {
    const apiGet = vi
      .spyOn(client, 'apiGet')
      .mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    vi.spyOn(client, 'apiPost').mockResolvedValue({
      access: 'jwt-access',
      refresh: 'jwt-refresh',
      user: usuarioDePrueba({
        roles: ['alumno'],
        perfil_alumno: {
          id: 4,
          numero_cuenta: '312345678',
          carrera: 5,
          carrera_nombre: 'Actuaría',
          generacion: 2023,
        },
      }),
    })

    montar()
    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated'))

    fireEvent.click(screen.getByRole('button', { name: 'Entrar con contraseña' }))

    await waitFor(() => expect(screen.getByTestId('roles')).toHaveTextContent('alumno'))
    expect(apiGet).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 3: Correr los tests y confirmar que fallan**

Run: `pnpm test src/auth/AuthContext.test.tsx`

Expected: FAIL — el archivo ni siquiera llega a correr los casos: Vitest aborta al resolver `usuarioDePrueba`, porque `src/test/factories.ts` referencia campos (`apellido1`, `roles`, …) que `AuthUser` todavía no declara. Si por alguna razón sí arranca, los tres tests que leen `data-testid="roles"` fallan con `Unable to find an element by: [data-testid="roles"]`, porque el contexto todavía no expone `roles` y la `Sonda` no compila el destructuring.

- [ ] **Step 4: Fijar la forma del usuario en `types.ts`**

En `frontend/src/api/types.ts`, reemplazar las líneas 1-5 (la interfaz `AuthUser` actual) por:

```ts
// Forma exacta de `accounts.serializers.UserDetailsSerializer` del backend.
// El mismo objeto alimenta GET /api/auth/user/ y la clave `user` del body de
// POST /api/auth/login/ y POST /api/auth/google/.
export type RolUsuario = 'alumno' | 'academico' | 'asesor_academico'

export interface PerfilAlumno {
  id: number
  numero_cuenta: string
  carrera: number
  carrera_nombre: string
  generacion: number
}

export interface PerfilAcademico {
  id: number
  numero_trabajador: string
}

export interface PerfilAsesorAcademico {
  id: number
  area: number
  area_nombre: string
  // Ojo: `asesor_academico` aparece en `roles` aunque esto sea false — el rol
  // sigue el criterio de la permission class EsAsesorAcademico del backend,
  // que solo comprueba que el perfil exista.
  activo: boolean
}

export interface AuthUser {
  pk: number
  email: string
  first_name: string
  apellido1: string
  apellido2: string
  nombre_completo: string
  roles: RolUsuario[]
  perfil_alumno: PerfilAlumno | null
  perfil_academico: PerfilAcademico | null
  perfil_asesor_academico: PerfilAsesorAcademico | null
}
```

El resto del archivo (`LoginResponse`, `Materia`, `Carrera`, `RegistroAsesor`, `Disponibilidad`, `Asesoria`, los alias de formato/estado) no se toca. `LoginResponse.user: AuthUser` ya apunta a la interfaz nueva sin cambios.

- [ ] **Step 5: Exponer `roles` en el contexto**

En `frontend/src/auth/AuthContext.tsx`:

1. Cambiar el import de tipos (línea 3) por:

```ts
import type { AuthUser, LoginResponse, RolUsuario } from '../api/types'
```

2. Agregar `roles` a la interfaz del contexto (líneas 8-14):

```ts
interface AuthContextValue {
  user: AuthUser | null
  roles: RolUsuario[]
  status: EstadoSesion
  loginWithPassword: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => Promise<void>
}
```

3. Reemplazar el `return` del provider (líneas 74-78) por:

```tsx
  // `roles` se deriva de `user` en vez de guardarse aparte: hay una sola
  // fuente de verdad. El `?? []` es el ÚNICO punto del frontend que tolera
  // que el backend todavía no mande el campo (Task 3 del plan del paso 4);
  // gracias a él ningún consumidor necesita defenderse por su cuenta.
  const roles = user?.roles ?? []

  return (
    <AuthContext.Provider
      value={{ user, roles, status, loginWithPassword, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
```

- [ ] **Step 6: Correr los tests y confirmar que pasan**

Run: `pnpm test src/auth/AuthContext.test.tsx`

Expected: PASS — los 5 casos.

- [ ] **Step 7: Correr la suite y el build completos**

Run: `pnpm test && pnpm build && pnpm lint`

Expected: los tres en verde. `pnpm build` es la verificación que importa aquí: typecheca `src/test/factories.ts` contra el `AuthUser` nuevo (los archivos `.test.tsx` no los typecheca nadie).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/api/types.ts frontend/src/auth/AuthContext.tsx \
        frontend/src/auth/AuthContext.test.tsx frontend/src/test/factories.ts
git commit -s -m "[feat][frontend] exponer perfil y rol del usuario en el contexto de auth" \
  -m "- AuthUser pasa a la forma completa de UserDetailsSerializer del backend:
    apellidos, nombre_completo, roles y un objeto por perfil (o null), mas
    los tipos RolUsuario/PerfilAlumno/PerfilAcademico/PerfilAsesorAcademico.
- useAuth() expone roles derivado de user; el ?? [] es el unico punto que
    tolera que el backend todavia no mande el campo, con test dedicado.
- Fabrica usuarioDePrueba en src/test/factories.ts: al no terminar en
    .test.ts entra en tsc -b, asi que es el unico lugar donde el compilador
    verifica la forma del payload de usuario.
- Test que fija que el rol llega con el body del login mismo, sin una
    segunda llamada a /api/auth/user/."
```

---

### Task 2: El SPA obtiene un `id_token` de Google y lo manda al backend

Implementa la decisión central de [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md) del lado del cliente. Hoy `frontend/src/auth/google.ts` usa `google.accounts.oauth2.initTokenClient` con `scope: 'email profile'` — el mecanismo de **autorización** de OAuth — y `AuthContext.loginWithGoogle` (línea 57) manda `{access_token}`. Pasa a `google.accounts.id`, el mecanismo de **autenticación** (OIDC), que entrega un JWT firmado en `response.credential`.

Los dos archivos van en la misma task y el mismo commit porque `google.ts` no tiene otro consumidor: separarlos dejaría un `pnpm build` roto entre commits (`noUnusedLocals` + el import colgante en `AuthContext`).

**Files:**
- Modify: `frontend/src/auth/google.ts` (reescritura completa)
- Modify: `frontend/src/auth/AuthContext.tsx:4` y `:54-61`
- Test: `frontend/src/auth/google.test.ts` (crear)
- Test: `frontend/src/auth/AuthContext.test.tsx` (agregar)

**Interfaces:**
- Consumes: `usuarioDePrueba` (Task 1); `apiPost` de `api/client.ts`.
- Produces:
  - `auth/google.ts`: `cargarGoogleIdentityServices(): Promise<void>` (mismo nombre, ahora comprueba `window.google?.accounts?.id`), `solicitarIdTokenDeGoogle(clientId: string): Promise<string>` (resuelve con el JWT de `credential`), y el tipo exportado `NotificacionPrompt`. **`solicitarAccessTokenDeGoogle` deja de existir.**
  - `POST /api/auth/google/` se llama con el body `{ id_token: string }`.

- [ ] **Step 1: Escribir los tests del flujo de Google — RED**

Crear `frontend/src/auth/google.test.ts`:

```ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cargarGoogleIdentityServices, solicitarIdTokenDeGoogle, type NotificacionPrompt } from './google'

type RespuestaCredencial = { credential?: string }

/**
 * Sustituye la librería de Google por un doble que captura el callback de
 * credential y el listener de notificaciones, para poder dispararlos a mano.
 */
function montarGoogleFalso() {
  let callback: ((r: RespuestaCredencial) => void) | undefined
  let notificar: ((n: NotificacionPrompt) => void) | undefined

  const initialize = vi.fn((config: { client_id: string; callback: (r: RespuestaCredencial) => void }) => {
    callback = config.callback
  })
  const prompt = vi.fn((listener?: (n: NotificacionPrompt) => void) => {
    notificar = listener
  })
  const cancel = vi.fn()

  window.google = { accounts: { id: { initialize, prompt, cancel } } }

  return {
    initialize,
    prompt,
    cancel,
    responderCon: (r: RespuestaCredencial) => callback!(r),
    notificarCon: (n: NotificacionPrompt) => notificar!(n),
  }
}

describe('solicitarIdTokenDeGoogle', () => {
  afterEach(() => {
    delete window.google
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('inicializa Sign In With Google con el client_id y sin pedir ningún scope', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.initialize).toHaveBeenCalled())

    const config = google.initialize.mock.calls[0][0] as Record<string, unknown>
    expect(config.client_id).toBe('client-id-de-prueba')
    // ADR 0019: el id_token trae email/name/sub por sí solo. Pedir un scope
    // sería volver a pedir autorización de API, que es justo lo que se dejó.
    expect(config).not.toHaveProperty('scope')
    expect(google.prompt).toHaveBeenCalled()

    google.responderCon({ credential: 'jwt-de-google' })
    await expect(promesa).resolves.toBe('jwt-de-google')
  })

  it('resuelve con la credencial que entrega el callback', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.prompt).toHaveBeenCalled())
    google.responderCon({ credential: 'jwt-de-google' })

    await expect(promesa).resolves.toBe('jwt-de-google')
  })

  it('rechaza si One Tap no llegó a mostrarse', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.prompt).toHaveBeenCalled())
    google.notificarCon({ isNotDisplayed: () => true })

    await expect(promesa).rejects.toThrow('Login con Google cancelado.')
  })

  it('no rechaza cuando el momento se cierra porque ya devolvió la credencial', async () => {
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    await vi.waitFor(() => expect(google.prompt).toHaveBeenCalled())
    // Camino feliz: Google marca el momento como "dismissed" con este motivo
    // justo cuando entrega la credencial. Mirar solo isDismissedMoment()
    // rechazaría un login exitoso.
    google.notificarCon({
      isDismissedMoment: () => true,
      getDismissedReason: () => 'credential_returned',
    })
    google.responderCon({ credential: 'jwt-de-google' })

    await expect(promesa).resolves.toBe('jwt-de-google')
  })

  it('rechaza y cancela One Tap si nadie responde en 60 s', async () => {
    vi.useFakeTimers()
    const google = montarGoogleFalso()

    const promesa = solicitarIdTokenDeGoogle('client-id-de-prueba')
    const assertion = expect(promesa).rejects.toThrow('Login con Google cancelado.')
    await vi.advanceTimersByTimeAsync(60_000)

    await assertion
    expect(google.cancel).toHaveBeenCalled()
  })
})

describe('cargarGoogleIdentityServices', () => {
  beforeEach(() => {
    delete window.google
    document.head.innerHTML = ''
    vi.resetModules()
  })

  afterEach(() => {
    delete window.google
    document.head.innerHTML = ''
  })

  function scriptsDeGoogle() {
    return document.head.querySelectorAll('script[src="https://accounts.google.com/gsi/client"]')
  }

  it('inyecta el script de Google Identity Services si la librería no está en la página', async () => {
    const { cargarGoogleIdentityServices: cargar } = await import('./google')

    const promesa = cargar()
    const script = scriptsDeGoogle()[0] as HTMLScriptElement
    expect(script).toBeTruthy()
    expect(script.async).toBe(true)
    script.onload!(new Event('load'))

    await expect(promesa).resolves.toBeUndefined()
  })

  it('permite reintentar si el script falla al cargar', async () => {
    const { cargarGoogleIdentityServices: cargar } = await import('./google')

    const primera = cargar()
    ;(scriptsDeGoogle()[0] as HTMLScriptElement).onerror!(new Event('error'))
    await expect(primera).rejects.toThrow('No se pudo cargar Google Identity Services.')

    cargar()
    expect(scriptsDeGoogle()).toHaveLength(2)
  })
})

// Referencia usada solo para que el import de tipo no quede sin uso si se
// reordenan los tests; `cargarGoogleIdentityServices` se ejercita arriba.
void cargarGoogleIdentityServices
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/auth/google.test.ts`

Expected: FAIL — el archivo no puede resolver el import: `solicitarIdTokenDeGoogle` y `NotificacionPrompt` no existen en `./google` (hoy exporta `solicitarAccessTokenDeGoogle`). Vitest reporta el archivo entero como fallido antes de correr ningún caso.

- [ ] **Step 3: Reescribir `google.ts` con el flujo de ID token**

Reemplazar el contenido completo de `frontend/src/auth/google.ts` por:

```ts
/**
 * Google Identity Services — "Sign In With Google" (`google.accounts.id`).
 *
 * ADR 0019: se dejó `google.accounts.oauth2.initTokenClient` (que entrega un
 * access_token de OAuth) porque el backend, al validar ese token, no
 * comprobaba que se hubiera emitido para el client_id de Atenea. El ID token
 * es un JWT firmado por Google cuyo `audience` el backend sí verifica.
 */

export interface RespuestaCredencial {
  credential?: string
}

export interface NotificacionPrompt {
  isNotDisplayed?: () => boolean
  isSkippedMoment?: () => boolean
  isDismissedMoment?: () => boolean
  getDismissedReason?: () => string
}

interface ConfigInitialize {
  client_id: string
  callback: (respuesta: RespuestaCredencial) => void
  auto_select?: boolean
  cancel_on_tap_outside?: boolean
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize(config: ConfigInitialize): void
          prompt(listener?: (notificacion: NotificacionPrompt) => void): void
          cancel(): void
        }
      }
    }
  }
}

// Si One Tap no se muestra ni se cierra (caso posible con FedCM, donde las
// notificaciones dejan de ser informativas), la promesa nunca se resolvería y
// el botón quedaría girando para siempre. Ver Decisión 2 del plan.
const MS_ESPERA_ONE_TAP = 60_000

let cargando: Promise<void> | null = null

export function cargarGoogleIdentityServices(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve()
  if (cargando) return cargando

  cargando = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => {
      // Se limpia la promesa fallida para que un fallo de red transitorio no
      // deje el login roto por el resto de la sesión del navegador.
      cargando = null
      reject(new Error('No se pudo cargar Google Identity Services.'))
    }
    document.head.appendChild(script)
  })
  return cargando
}

function promptSinCredencial(notificacion: NotificacionPrompt): boolean {
  try {
    if (notificacion.isNotDisplayed?.()) return true
    if (notificacion.isSkippedMoment?.()) return true
    // El momento también se marca como "dismissed" en el camino feliz, con
    // motivo `credential_returned`: ahí no hay nada que rechazar.
    return (
      (notificacion.isDismissedMoment?.() ?? false) &&
      notificacion.getDismissedReason?.() !== 'credential_returned'
    )
  } catch {
    // En modo FedCM estos métodos pueden no estar disponibles y lanzar. Sin
    // señal utilizable no se rechaza: el callback de credencial sigue siendo
    // el único camino de éxito, y el timeout cubre el caso sin respuesta.
    return false
  }
}

export async function solicitarIdTokenDeGoogle(clientId: string): Promise<string> {
  await cargarGoogleIdentityServices()
  const id = window.google!.accounts.id

  return new Promise<string>((resolve, reject) => {
    let temporizador: ReturnType<typeof setTimeout>

    const terminar = (accion: () => void) => {
      clearTimeout(temporizador)
      accion()
    }

    temporizador = setTimeout(() => {
      id.cancel()
      reject(new Error('Login con Google cancelado.'))
    }, MS_ESPERA_ONE_TAP)

    id.initialize({
      client_id: clientId,
      // Sin `scope`: el ID token trae email/name/sub por defecto. Pedir un
      // scope OAuth sería pedir autorización para llamar APIs de Google a
      // nombre del usuario, que Atenea no hace (ADR 0019).
      callback: (respuesta) =>
        terminar(() =>
          respuesta.credential
            ? resolve(respuesta.credential)
            : reject(new Error('Login con Google cancelado.')),
        ),
      auto_select: false,
      cancel_on_tap_outside: true,
    })

    id.prompt((notificacion) => {
      if (promptSinCredencial(notificacion)) {
        terminar(() => reject(new Error('Login con Google cancelado.')))
      }
    })
  })
}
```

- [ ] **Step 4: Correr los tests de Google y confirmar que pasan**

Run: `pnpm test src/auth/google.test.ts`

Expected: PASS — los 7 casos.

- [ ] **Step 5: Escribir el test del payload que manda el contexto — RED**

En `frontend/src/auth/AuthContext.test.tsx`, agregar el import del módulo de Google junto a los que ya existen:

```ts
import * as google from './google'
```

y agregar este caso al final del `describe('AuthProvider', ...)`:

```tsx
  it('manda a POST /api/auth/google/ el id_token que devuelve Google', async () => {
    vi.stubEnv('VITE_GOOGLE_OAUTH_CLIENT_ID', 'client-id-de-prueba')
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    const solicitar = vi.spyOn(google, 'solicitarIdTokenDeGoogle').mockResolvedValue('jwt-de-google')
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({
      access: 'jwt-access',
      refresh: 'jwt-refresh',
      user: usuarioDePrueba({ roles: ['alumno'] }),
    })

    montar()
    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated'))

    fireEvent.click(screen.getByRole('button', { name: 'Entrar con Google' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/auth/google/', { id_token: 'jwt-de-google' }),
    )
    expect(solicitar).toHaveBeenCalledWith('client-id-de-prueba')
    vi.unstubAllEnvs()
  })
```

y agregar el botón correspondiente a la `Sonda`, que pasa a ser:

```tsx
function Sonda() {
  const { status, user, roles, loginWithPassword, loginWithGoogle } = useAuth()
  return (
    <>
      <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
      <div data-testid="roles">{roles.join(',') || 'sin-roles'}</div>
      <button type="button" onClick={() => loginWithPassword('a@ciencias.unam.mx', 'x')}>
        Entrar con contraseña
      </button>
      <button type="button" onClick={() => loginWithGoogle()}>
        Entrar con Google
      </button>
    </>
  )
}
```

- [ ] **Step 6: Correr el test y confirmar que falla**

Run: `pnpm test src/auth/AuthContext.test.tsx`

Expected: FAIL solo en el caso nuevo, con `AssertionError: expected "apiPost" to be called with arguments: [ '/api/auth/google/', { id_token: 'jwt-de-google' } ]` — el espía de `solicitarIdTokenDeGoogle` ni siquiera se usa, porque `AuthContext` sigue importando `solicitarAccessTokenDeGoogle`, que ya no existe: el error real que verás primero es el de import fallido del módulo `./google`. Los otros 5 casos siguen en PASS.

- [ ] **Step 7: Cambiar el transporte en `AuthContext`**

En `frontend/src/auth/AuthContext.tsx`:

1. Reemplazar la línea 4 por:

```ts
import { solicitarIdTokenDeGoogle } from './google'
```

2. Reemplazar `loginWithGoogle` (líneas 54-61) por:

```ts
  async function loginWithGoogle() {
    const clientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID
    const idToken = await solicitarIdTokenDeGoogle(clientId)
    const data = await apiPost<LoginResponse>('/api/auth/google/', { id_token: idToken })
    persistirSesion(data)
    setUser(data.user)
    setStatus('authenticated')
  }
```

- [ ] **Step 8: Correr los tests y confirmar que pasan**

Run: `pnpm test src/auth`

Expected: PASS — `google.test.ts` (7), `AuthContext.test.tsx` (6) y `rol.test.tsx` (2, todavía el de sondeo, intacto).

- [ ] **Step 9: Verificar que no quedó rastro del transporte viejo**

Run:
```bash
grep -rn "access_token\|initTokenClient\|solicitarAccessTokenDeGoogle\|accounts.oauth2" src/ || echo "SIN RASTRO DEL TRANSPORTE VIEJO"
pnpm build && pnpm lint
```

Expected: el `grep` imprime `SIN RASTRO DEL TRANSPORTE VIEJO`, y el build y el lint en verde.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/auth/google.ts frontend/src/auth/google.test.ts \
        frontend/src/auth/AuthContext.tsx frontend/src/auth/AuthContext.test.tsx
git commit -s -m "[feat][frontend] migrar el login con Google a id_token (Sign In With Google)" \
  -m "- google.ts pasa de google.accounts.oauth2.initTokenClient (access_token
    de OAuth, con scope 'email profile') a google.accounts.id: el callback
    entrega un id_token OIDC y ya no se pide ningun scope. ADR 0019.
- loginWithGoogle manda { id_token } a POST /api/auth/google/.
- La promesa se rechaza si One Tap no se muestra o se cierra sin credencial,
    y a los 60 s llama a google.accounts.id.cancel(), para que el boton no
    quede girando indefinidamente cuando la notificacion no informa (FedCM).
- Primer test de google.ts: client_id correcto, ausencia de scope, camino
    feliz, cierre sin credencial, timeout, y carga/reintento del script.
- Bloqueo conocido: el backend todavia exige access_token; el login con
    Google no funciona en runtime hasta ejecutar la Task 1 del plan
    docs/superpowers/plans/2026-08-04-login-oauth-backend.md."
```

---

### Task 3: El rol se lee del contexto, no se sondea la API

Cierra el workaround 1 de la [deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md) del lado del cliente. Hoy `frontend/src/auth/rol.ts` hace una petición a `GET /api/asesorias/registros/` y deduce el rol del código de estado (200 = asesor, 403 = no). Con `roles` en el contexto (Task 1), esa llamada sobra: el rol ya viaja en el body del login.

`RutaProtegida.tsx` va en la misma task porque hoy consume `{data, isPending}` de TanStack Query: cambiar `rol.ts` sin cambiarlo dejaría `pnpm build` roto.

**Files:**
- Modify: `frontend/src/auth/rol.ts` (reescritura completa)
- Modify: `frontend/src/auth/RutaProtegida.tsx:14-27`
- Test: `frontend/src/auth/rol.test.tsx` (reescritura completa)
- Test: `frontend/src/auth/RutaProtegida.test.tsx` (crear)

**Interfaces:**
- Consumes: `useAuth().roles` (Task 1); `usuarioDePrueba` (Task 1).
- Produces:
  - `auth/rol.ts`: `useEsAsesor(): boolean`, `useEsAlumno(): boolean`. **Ya no devuelven el objeto de TanStack Query.** `RutaDeAsesor` es su único consumidor de producción.
  - `auth/RutaProtegida.tsx`: `RutaDeAsesor` sin cambios de firma (`{ children }`).

- [ ] **Step 1: Reescribir los tests de rol — RED**

Reemplazar el contenido completo de `frontend/src/auth/rol.test.tsx` por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider } from './AuthContext'
import { useEsAlumno, useEsAsesor } from './rol'
import * as client from '../api/client'
import { usuarioDePrueba } from '../test/factories'
import type { AuthUser } from '../api/types'

function Sonda() {
  const esAsesor = useEsAsesor()
  const esAlumno = useEsAlumno()
  return <div data-testid="rol">{`asesor=${esAsesor} alumno=${esAlumno}`}</div>
}

function montarCon(usuario: AuthUser) {
  vi.spyOn(client, 'apiGet').mockResolvedValue(usuario)
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )
}

describe('hooks de rol', () => {
  afterEach(() => vi.restoreAllMocks())

  it('reconoce al asesor académico por el rol que viene del contexto', async () => {
    montarCon(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: true },
      }),
    )

    await waitFor(() => {
      expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true alumno=false')
    })
  })

  it('reconoce al alumno', async () => {
    montarCon(
      usuarioDePrueba({
        roles: ['alumno'],
        perfil_alumno: {
          id: 4,
          numero_cuenta: '312345678',
          carrera: 5,
          carrera_nombre: 'Actuaría',
          generacion: 2023,
        },
      }),
    )

    await waitFor(() => {
      expect(screen.getByTestId('rol')).toHaveTextContent('asesor=false alumno=true')
    })
  })

  it('un asesor con el perfil inactivo sigue contando como asesor', async () => {
    // Mismo criterio que la permission class EsAsesorAcademico del backend,
    // que solo comprueba que el perfil exista. Divergir haría que la UI
    // escondiera una pantalla a la que el backend sí da acceso.
    montarCon(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: false },
      }),
    )

    await waitFor(() => {
      expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true')
    })
  })

  it('no consulta ningún endpoint de asesorías para averiguar el rol', async () => {
    const apiGet = vi
      .spyOn(client, 'apiGet')
      .mockResolvedValue(usuarioDePrueba({ roles: ['asesor_academico'] }))

    render(
      <AuthProvider>
        <Sonda />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('rol')).toHaveTextContent('asesor=true'))
    expect(apiGet).toHaveBeenCalledTimes(1)
    expect(apiGet).toHaveBeenCalledWith('/api/auth/user/')
  })
})
```

- [ ] **Step 2: Escribir los tests del guard de ruta — RED**

Crear `frontend/src/auth/RutaProtegida.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import { RutaDeAsesor } from './RutaProtegida'
import * as client from '../api/client'
import { usuarioDePrueba } from '../test/factories'

function montar() {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/asesorias']}>
        <Routes>
          <Route
            path="/asesorias"
            element={
              <RutaDeAsesor>
                <p>panel del asesor</p>
              </RutaDeAsesor>
            }
          />
          <Route path="/home" element={<p>pantalla home</p>} />
          <Route path="/login" element={<p>pantalla login</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RutaDeAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('deja pasar al asesor académico', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({ roles: ['academico', 'asesor_academico'] }),
    )

    montar()

    expect(await screen.findByText('panel del asesor')).toBeInTheDocument()
  })

  it('manda a Home a quien tiene sesión pero no es asesor', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(usuarioDePrueba({ roles: ['alumno'] }))

    montar()

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(screen.queryByText('panel del asesor')).not.toBeInTheDocument()
  })

  it('manda a Login a quien no tiene sesión', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))

    montar()

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })

  it('deja pasar al asesor aunque su perfil esté inactivo', async () => {
    vi.spyOn(client, 'apiGet').mockResolvedValue(
      usuarioDePrueba({
        roles: ['academico', 'asesor_academico'],
        perfil_asesor_academico: { id: 3, area: 2, area_nombre: 'Matemáticas', activo: false },
      }),
    )

    montar()

    expect(await screen.findByText('panel del asesor')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Correr los dos archivos y confirmar que fallan**

Run: `pnpm test src/auth/rol.test.tsx src/auth/RutaProtegida.test.tsx`

Expected: FAIL.
- `rol.test.tsx` → el archivo no resuelve el import `useEsAlumno` (no existe), y `useEsAsesor()` sigue devolviendo un objeto de TanStack Query, así que la `Sonda` renderizaría `asesor=[object Object]`. Además, sin `QueryClientProvider` la versión actual del hook lanza `No QueryClient set`.
- `RutaProtegida.test.tsx` → los cuatro casos fallan por lo mismo: `useEsAsesor()` sin `QueryClientProvider` lanza dentro del guard.

- [ ] **Step 4: Reescribir `rol.ts`**

Reemplazar el contenido completo de `frontend/src/auth/rol.ts` por:

```ts
import { useAuth } from './AuthContext'

/**
 * El rol viene con el propio login: `GET /api/auth/user/` y la clave `user`
 * del body de `/api/auth/login/` y `/api/auth/google/` comparten serializer
 * en el backend, así que `roles` ya está en el contexto de auth.
 *
 * Esto reemplaza el sondeo que había aquí (pedir `GET /api/asesorias/registros/`
 * y leer 200 vs 403), que era el workaround 1 de la deuda técnica 0010: no
 * escalaba a más de un rol sin una petición extra por cada rol a verificar.
 */
export function useEsAsesor(): boolean {
  // `asesor_academico` aparece aunque el perfil esté inactivo — mismo criterio
  // que la permission class EsAsesorAcademico, que solo comprueba existencia.
  return useAuth().roles.includes('asesor_academico')
}

export function useEsAlumno(): boolean {
  return useAuth().roles.includes('alumno')
}
```

- [ ] **Step 5: Simplificar el guard de ruta**

En `frontend/src/auth/RutaProtegida.tsx`, reemplazar la función `RutaDeAsesor` (líneas 14-27) por:

```tsx
export function RutaDeAsesor({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const esAsesor = useEsAsesor()
  const location = useLocation()

  // Antes había dos estados de carga (el de la sesión y el del sondeo de rol).
  // Ahora el rol llega con la sesión, así que `status` es la única compuerta.
  if (status === 'loading') return <PantallaCargando />
  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  if (!esAsesor) return <Navigate to="/home" replace />

  return <>{children}</>
}
```

El import de `useEsAsesor` (línea 4) y el componente `PantallaCargando` no cambian.

- [ ] **Step 6: Correr los tests y confirmar que pasan**

Run: `pnpm test src/auth`

Expected: PASS — `google.test.ts` (7), `AuthContext.test.tsx` (6), `rol.test.tsx` (4), `RutaProtegida.test.tsx` (4).

- [ ] **Step 7: Verificar que el sondeo desapareció y que nada quedó colgando**

Run:
```bash
grep -rn "asesorias/registros" src/auth/ || echo "SIN SONDEO DE ROL EN auth/"
pnpm test && pnpm build && pnpm lint
```

Expected: el `grep` imprime `SIN SONDEO DE ROL EN auth/` (el string sí sigue apareciendo en `src/features/asesorias/api.ts`, que es su uso legítimo — por eso el `grep` se acota a `src/auth/`). Los tres comandos en verde; `pnpm build` es el que atrapa un import muerto de `@tanstack/react-query` o de `RegistroAsesor` si quedó alguno (`noUnusedLocals`).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/auth/rol.ts frontend/src/auth/rol.test.tsx \
        frontend/src/auth/RutaProtegida.tsx frontend/src/auth/RutaProtegida.test.tsx
git commit -s -m "[refactor][frontend] leer el rol del contexto de auth en vez de sondear la API" \
  -m "- useEsAsesor() deja de pedir GET /api/asesorias/registros/ para leer el
    codigo 200 vs 403 (workaround 1 de la deuda tecnica 0010) y pasa a leer
    roles del contexto; devuelve boolean, ya no el objeto de TanStack Query.
- Se agrega useEsAlumno(), que con el sondeo habria exigido un segundo
    endpoint centinela.
- El criterio de asesor sigue al de la permission class EsAsesorAcademico:
    el rol cuenta aunque perfil_asesor_academico.activo sea false, con test.
- RutaDeAsesor queda con una sola compuerta de carga (status de sesion) y
    estrena test: deja pasar al asesor, manda a Home al que no lo es y a
    Login al que no tiene sesion.
- Bloqueo conocido: /api/auth/user/ todavia no devuelve roles; hasta que se
    ejecute la Task 3 del plan de backend, /asesorias* redirige a /home en
    runtime. Los tests mockean la respuesta y no tocan red."
```

---

### Task 4: `Boton` gana el estado de foco visible

Cimiento compartido de las dos pantallas de login. El checklist de accesibilidad del paso 7 (`docs/development/contribuir-componentes.md`) nombra este gap de forma literal: *"la única regla de foco en todo el proyecto (`Login.tsx`) usa `outline-none focus:border-primary`, sin un ring perceptible"*. `Boton.tsx` hoy no tiene ninguna regla de foco, así que sus 6 consumidores actuales (los 4 diálogos de asesorías, `DetalleAsesoria`, `DisponibilidadAsesor`) dependen del outline por defecto del navegador.

Entra aquí, en el componente, y no en cada pantalla: es un cambio de una línea que cubre a todos los consumidores presentes y futuros. `Boton.tsx` no lo toca ningún otro plan — el del paso 8 lo declara explícitamente intocado.

**Files:**
- Modify: `frontend/src/components/ui/Boton.tsx:18`
- Test: `frontend/src/components/ui/Boton.test.tsx` (crear)

**Interfaces:**
- Consumes: nada.
- Produces: `Boton` con la misma firma (`cargando?`, `variante?: 'primario' | 'secundario' | 'peligro'`, más `ButtonHTMLAttributes<HTMLButtonElement>`) y foco visible. Las Tasks 5 y 6 lo componen.

- [ ] **Step 1: Escribir los tests — RED**

Crear `frontend/src/components/ui/Boton.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Boton } from './Boton'

describe('Boton', () => {
  it('lleva un estado de foco visible perceptible (checklist del paso 7)', () => {
    render(<Boton>Entrar</Boton>)

    const boton = screen.getByRole('button', { name: 'Entrar' })
    expect(boton).toHaveClass('focus-visible:outline-2')
    expect(boton).toHaveClass('focus-visible:outline-offset-2')
    expect(boton).toHaveClass('focus-visible:outline-primary')
  })

  it('muestra el spinner y queda deshabilitado mientras carga', () => {
    const { container } = render(<Boton cargando>Entrar</Boton>)

    expect(screen.getByRole('button', { name: 'Entrar' })).toBeDisabled()
    const spinner = container.querySelector('.spinner')
    expect(spinner).toBeTruthy()
    expect(spinner).toHaveAttribute('aria-hidden')
  })

  it('no dispara onClick mientras carga', () => {
    const onClick = vi.fn()
    render(
      <Boton cargando onClick={onClick}>
        Entrar
      </Boton>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(onClick).not.toHaveBeenCalled()
  })

  it('la variante secundario usa el contorno y no el relleno primario', () => {
    render(<Boton variante="secundario">Continuar con Correo Ciencias</Boton>)

    const boton = screen.getByRole('button', { name: 'Continuar con Correo Ciencias' })
    expect(boton).toHaveClass('border-outline')
    expect(boton).not.toHaveClass('bg-primary')
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/components/ui/Boton.test.tsx`

Expected: FAIL solo el primer caso, con `expected element to have class "focus-visible:outline-2"`. Los otros tres pasan ya — son la red de seguridad de que el cambio de la línea de clases no rompe nada de lo que `Boton` ya hacía, no tests de comportamiento nuevo.

- [ ] **Step 3: Agregar el foco al componente**

En `frontend/src/components/ui/Boton.tsx`, reemplazar la plantilla de `className` (línea 18) por:

```tsx
      className={`flex h-11 items-center justify-center gap-2 rounded-full text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60 ${VARIANTES[variante]} ${className}`}
```

Nada más del archivo cambia.

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pnpm test src/components/ui/Boton.test.tsx`

Expected: PASS — los 4 casos.

- [ ] **Step 5: Verificar que los consumidores actuales siguen sanos**

Run: `pnpm test && pnpm build && pnpm lint`

Expected: los tres en verde. `Boton` lo usan hoy 6 archivos (`DialogoCancelar`, `DialogoNuevoBloque`, `DialogoAgregarMateria`, `DialogoBloqueActivo`, `DetalleAsesoria`, `DisponibilidadAsesor`); ninguno pasa un `className` que compita con `outline-*`, así que el único efecto visible es el anillo de foco nuevo.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/Boton.tsx frontend/src/components/ui/Boton.test.tsx
git commit -s -m "[fix][frontend] foco visible en el boton compartido" \
  -m "- Boton gana focus-visible:outline-2 / offset-2 / outline-primary, el
    estado que el checklist de accesibilidad de contribuir-componentes.md
    exige en todo elemento interactivo y que ningun componente del proyecto
    tenia. Cubre de una sola vez a sus 6 consumidores actuales.
- Primer test de un primitivo de components/ui: foco, spinner con
    aria-hidden y disabled durante la carga, onClick bloqueado mientras
    carga, y el contorno de la variante secundario."
```

---

### Task 5: El botón de `Landing` inicia sesión de verdad

Implementa la **decisión 5 de la spec del paso 2**, el único defecto funcional real del flujo de login: `frontend/src/screens/Landing.tsx:25` hace `onClick={() => navigate('/home')}` — cualquiera que abra la app entra a `/home` sin autenticarse. Pasa a invocar `useAuth().loginWithGoogle()` (el mismo flujo de `id_token` que `Login.tsx`), con manejo de carga y de error, y navega solo si el login resuelve.

El copy no cambia. El botón secundario ("Entrar con correo y contraseña") sigue navegando a `/login` tal cual.

**Files:**
- Modify: `frontend/src/screens/Landing.tsx` (reescritura completa)
- Test: `frontend/src/screens/Landing.test.tsx` (crear)

**Interfaces:**
- Consumes: `useAuth()` (Tasks 1 y 2), `Boton` (Task 4), `Logo` de `components/Logo` (sin cambios).
- Produces: `Landing` con la misma firma (`export function Landing()`, sin props). `App.tsx` no cambia.

- [ ] **Step 1: Escribir los tests — RED**

Crear `frontend/src/screens/Landing.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Landing } from './Landing'
import * as auth from '../auth/AuthContext'

function montar(loginWithGoogle: () => Promise<void>) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status: 'unauthenticated',
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

function botonDeGoogle() {
  return screen.getByRole('button', { name: 'Continuar con Correo Ciencias' })
}

describe('Landing', () => {
  afterEach(() => vi.restoreAllMocks())

  it('navega a Home solo después de que el login resuelve', async () => {
    const loginWithGoogle = vi.fn().mockResolvedValue(undefined)
    montar(loginWithGoogle)

    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
    fireEvent.click(botonDeGoogle())

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(loginWithGoogle).toHaveBeenCalledTimes(1)
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
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/screens/Landing.test.tsx`

Expected: FAIL en 3 de los 4.
- `navega a Home solo después de que el login resuelve` → FAIL: `loginWithGoogle` nunca se llama (`expected "spy" to be called 1 times, but got 0 times`). Ojo: la aserción de `pantalla home` **pasa** — precisamente porque hoy navega sin login. Ese es el defecto que este task corrige.
- `si el login falla, muestra el error y no navega` → FAIL con `Unable to find role="alert"`, y además ya navegó a `/home`.
- `deshabilita el botón mientras el login está en curso` → FAIL: el botón nunca se deshabilita.
- `el botón secundario…` → PASS ya. Es el test de regresión de lo que no debe cambiar.

- [ ] **Step 3: Reescribir `Landing.tsx`**

Reemplazar el contenido completo de `frontend/src/screens/Landing.tsx` por:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Logo } from '../components/Logo'
import { Boton } from '../components/ui/Boton'
import { useAuth } from '../auth/AuthContext'

export function Landing() {
  const navigate = useNavigate()
  const { loginWithGoogle } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [conectandoGoogle, setConectandoGoogle] = useState(false)

  // Mismo flujo, mismo manejo de carga/error y mismo copy de error que
  // Login.tsx: son dos entradas a la misma acción, no dos comportamientos.
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
    <main className="flex min-h-svh flex-col items-center justify-between px-6 py-12">
      <div />

      <div className="flex flex-col items-center gap-4 text-center">
        <Logo className="h-20 w-20 text-primary" />
        <h1 className="text-2xl font-semibold">Atenea</h1>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Secretaría de Asuntos Estudiantiles
        </p>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Facultad de Ciencias, UNAM
        </p>
      </div>

      <div className="flex w-full max-w-xs flex-col gap-3">
        {error && (
          <p role="alert" className="text-center text-sm text-error">
            {error}
          </p>
        )}

        <Boton type="button" onClick={handleGoogleLogin} cargando={conectandoGoogle}>
          Continuar con Correo Ciencias
        </Boton>

        <button
          type="button"
          onClick={() => navigate('/login')}
          className="h-11 rounded-full text-sm font-semibold text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          Entrar con correo y contraseña
        </button>
      </div>
    </main>
  )
}
```

Notas para quien implementa:
- El botón primario pasa a componer `Boton` (variante `primario` por defecto): las clases que tenía escritas a mano (`h-11 rounded-full bg-primary text-sm font-semibold text-on-primary`) son exactamente las que `Boton` produce, más el spinner de `cargando` y el foco de la Task 4, gratis.
- El botón secundario **no** usa `Boton` porque ninguna variante corresponde a "texto plano sin fondo ni contorno"; conserva sus clases y solo gana el foco. No se inventa una variante nueva para un solo caso.
- El error va arriba de los botones, dentro del mismo contenedor de ancho fijo, para que no desplace el bloque central del logo al aparecer.

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pnpm test src/screens/Landing.test.tsx`

Expected: PASS — los 4 casos.

- [ ] **Step 5: Verificar la suite completa**

Run: `pnpm test && pnpm build && pnpm lint`

Expected: los tres en verde.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/Landing.tsx frontend/src/screens/Landing.test.tsx
git commit -s -m "[fix][frontend] el boton de Landing inicia sesion en vez de navegar sin login" \
  -m "- 'Continuar con Correo Ciencias' pasa de navigate('/home') directo a
    useAuth().loginWithGoogle(), y navega solo si el login resuelve; con
    estado de carga y mensaje de error role=alert, identico al de Login.tsx.
    Decision 5 de la spec docs/superpowers/specs/2026-08-04-login-oauth-design.md.
- El boton primario pasa a componer Boton (mismas clases, mas spinner y
    foco visible); el secundario conserva su estilo de texto plano y gana el
    foco, y sigue llevando a /login sin cambios.
- Test nuevo: no navega si el login falla, no navega antes de que resuelva,
    y se deshabilita mientras conecta."
```

---

### Task 6: Foco visible en la pantalla de `Login`

Cierra el último pendiente que el paso 8 dejó anotado para este paso: *"el foco visible de `Login.tsx`"*. Es el archivo que el checklist del paso 7 cita por nombre como el ejemplo del gap (`outline-none focus:border-primary`, sin anillo perceptible). Los dos botones de acción pasan a componer `Boton` — que ya trae el anillo desde la Task 4 — y los tres controles restantes (los dos campos, el botón de volver y el de "¿Olvidaste tu contraseña?") lo reciben directo.

El comportamiento de la pantalla no cambia; por eso esta task es también la primera cobertura de test que tiene `Login.tsx`, que hoy tiene lógica real (dos flujos de login, dos estados de carga, dos mensajes de error) y cero tests.

**Files:**
- Modify: `frontend/src/screens/Login.tsx` (reescritura completa)
- Test: `frontend/src/screens/Login.test.tsx` (crear)

**Interfaces:**
- Consumes: `useAuth()` (Tasks 1 y 2), `Boton` (Task 4), `ApiError` de `api/client.ts`.
- Produces: `Login` con la misma firma (`export function Login()`, sin props).

- [ ] **Step 1: Escribir los tests — RED**

Crear `frontend/src/screens/Login.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Login } from './Login'
import * as auth from '../auth/AuthContext'
import { ApiError } from '../api/client'

interface Dobles {
  loginWithPassword?: (email: string, password: string) => Promise<void>
  loginWithGoogle?: () => Promise<void>
}

function montar({ loginWithPassword = vi.fn(), loginWithGoogle = vi.fn() }: Dobles = {}) {
  vi.spyOn(auth, 'useAuth').mockReturnValue({
    user: null,
    roles: [],
    status: 'unauthenticated',
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

  it('envía las credenciales y navega a Home', async () => {
    const loginWithPassword = vi.fn().mockResolvedValue(undefined)
    montar({ loginWithPassword })

    llenarCredenciales()
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(loginWithPassword).toHaveBeenCalledWith('ana@ciencias.unam.mx', 'ClaveSegura123!')
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

  it('el botón de Google usa loginWithGoogle y navega solo si resuelve', async () => {
    const loginWithGoogle = vi.fn().mockResolvedValue(undefined)
    montar({ loginWithGoogle })

    fireEvent.click(screen.getByRole('button', { name: 'Continuar con Correo Ciencias' }))

    expect(await screen.findByText('pantalla home')).toBeInTheDocument()
    expect(loginWithGoogle).toHaveBeenCalledTimes(1)
  })

  it('si el login con Google falla, muestra el error y no navega', async () => {
    montar({ loginWithGoogle: vi.fn().mockRejectedValue(new Error('popup cerrado')) })

    fireEvent.click(screen.getByRole('button', { name: 'Continuar con Correo Ciencias' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo iniciar sesión con Google.')
    expect(screen.queryByText('pantalla home')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/screens/Login.test.tsx`

Expected: FAIL en 1 de los 5.
- `los campos tienen label asociado y foco visible` → FAIL con `expected element to have class "focus-visible:outline-2"`. `getByLabelText` **sí** encuentra los campos hoy (Testing Library resuelve el `<label>` que envuelve al `<input>`), así que lo único rojo es el foco.
- Los otros 4 → PASS ya. Son la red que prueba que el cambio de markup no altera el comportamiento; si alguno se pone rojo después del Step 3, el cambio se pasó de la raya.

- [ ] **Step 3: Reescribir `Login.tsx`**

Reemplazar el contenido completo de `frontend/src/screens/Login.tsx` por:

```tsx
import { useId, useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import { Boton } from '../components/ui/Boton'

const FOCO_VISIBLE = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary'

interface TextFieldProps {
  label: string
  type: string
  value: string
  autoComplete: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
}

function TextField({ label, type, value, autoComplete, onChange }: TextFieldProps) {
  const id = useId()
  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="absolute -top-2 left-3 z-10 bg-background px-1 text-xs text-on-surface-variant"
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        required
        className={`h-14 w-full rounded-md border border-outline bg-transparent px-3.5 text-sm text-on-surface focus:border-primary ${FOCO_VISIBLE}`}
      />
    </div>
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
        className={`mb-8 flex h-9 w-9 items-center justify-center rounded-full text-on-background ${FOCO_VISIBLE}`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden>
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

        <button type="button" className={`self-end rounded-md text-xs font-medium text-primary ${FOCO_VISIBLE}`}>
          ¿Olvidaste tu contraseña?
        </button>

        <Boton type="submit" cargando={enviando}>
          Entrar
        </Boton>

        <div className="flex items-center gap-3 text-xs text-on-surface-variant">
          <span className="h-px flex-1 bg-outline-variant" />
          o
          <span className="h-px flex-1 bg-outline-variant" />
        </div>

        <Boton type="button" variante="secundario" onClick={handleGoogleLogin} cargando={conectandoGoogle}>
          Continuar con Correo Ciencias
        </Boton>
      </form>
    </main>
  )
}
```

Notas para quien implementa:
- El `<label>` que envolvía al `<input>` pasa a asociarse con `htmlFor`/`id` vía `useId()`, como pide el checklist del paso 7. Se agrega `z-10` al label porque ahora es hermano del input, no su padre, y el input pintaría encima de su fondo.
- Se quita `outline-none` del input: era exactamente la regla que anulaba el foco del navegador sin poner nada en su lugar. `focus:border-primary` se conserva.
- Los dos botones de acción pasan a `Boton`: las clases que tenían a mano son las mismas que produce `Boton` (`primario` = `bg-primary text-on-primary`; `secundario` = `border border-outline text-primary`), y `disabled={x}` + spinner manual se colapsan en `cargando={x}`. **Este cambio de markup es el mecanismo del fix**, no un refactor aparte: el anillo de foco de esos dos botones vive en `Boton` desde la Task 4.
- El SVG de la flecha gana `aria-hidden`: es decorativo, el nombre accesible ya lo da el `aria-label="Volver"` del botón.

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pnpm test src/screens/Login.test.tsx`

Expected: PASS — los 5 casos. Si alguno de los 4 que estaban verdes en el Step 2 se puso rojo, el markup cambió comportamiento: revísalo antes de seguir.

- [ ] **Step 5: Verificar que no queda ningún control de login sin foco**

Run:
```bash
grep -rn "outline-none" src/screens/ || echo "SIN outline-none EN LAS PANTALLAS"
grep -c "focus-visible:outline-primary" src/screens/Login.tsx
pnpm test && pnpm build && pnpm lint
```

Expected: el primer `grep` imprime `SIN outline-none EN LAS PANTALLAS`; el segundo imprime `4` (la constante `FOCO_VISIBLE` y sus 3 usos: campo de texto, botón de volver, "¿Olvidaste tu contraseña?" — los dos `Boton` traen el suyo). Los tres comandos en verde.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/Login.tsx frontend/src/screens/Login.test.tsx
git commit -s -m "[fix][frontend] foco visible perceptible en la pantalla de Login" \
  -m "- Se quita el outline-none de los campos (la regla que el checklist de
    contribuir-componentes.md cita como el gap de foco del proyecto) y se
    agrega focus-visible con anillo en campos, boton de volver y el enlace
    de contrasena olvidada.
- Los dos botones de accion pasan a componer Boton, que ya trae el anillo:
    es el mecanismo del fix, no un refactor aparte. Mismas clases, mismo
    aspecto, y disabled+spinner manuales se colapsan en cargando.
- Los labels pasan de envolver el input a asociarse con htmlFor/useId, y el
    SVG de la flecha gana aria-hidden (el nombre lo da el aria-label).
- Primer test de Login.tsx: envio de credenciales, error 400 de
    credenciales, login con Google y su error, y labels/foco de los campos."
```

---

### Task 7: Documentar el cambio de contrato del lado del cliente

Todo cambio de contrato en este repo se refleja en `docs/development/api-frontend.md` y en el `## Changelog` del ADR correspondiente, sin reescribir la decisión original (patrón del commit `d6ade66`). Esta task además deja registrado el bloqueo de runtime, que es lo más importante que hereda quien retome el trabajo.

**Files:**
- Modify: `docs/decisions/0019-transporte-login-google-id-token.md`
- Modify: `docs/development/api-frontend.md`
- Modify: `docs/development/contribuir-componentes.md`
- Modify: `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md`
- Modify: `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`

**Interfaces:**
- Consumes: los contratos verificados por los tests de las Tasks 1-6.
- Produces: nada consumido por código.

- [ ] **Step 1: Agregar el Changelog de frontend a la ADR 0019**

Al final de `docs/decisions/0019-transporte-login-google-id-token.md`, en la sección `## Changelog`, agregar:

```markdown
- **2026-08-04** — Implementada en el frontend. `frontend/src/auth/google.ts` dejó de exponer `solicitarAccessTokenDeGoogle` (basada en `google.accounts.oauth2.initTokenClient` con `scope: 'email profile'`) y expone `solicitarIdTokenDeGoogle`, que usa `google.accounts.id.initialize` + `prompt()` y resuelve con el `credential` (JWT OIDC) del callback; `AuthContext.loginWithGoogle` manda `{id_token}` a `POST /api/auth/google/`. No se pide ningún scope, no se agregó ninguna variable de entorno ni dependencia. Detalles de forma que el frontend tuvo que decidir y que esta ADR no fijaba: se usa **One Tap programático** y no el botón renderizado de Google, porque la spec exige que la UX de `Login.tsx` no cambie (sigue siendo el botón propio "Continuar con Correo Ciencias"); y la promesa se rechaza a los 60 s llamando `google.accounts.id.cancel()`, porque en modo FedCM las notificaciones de `prompt()` pueden dejar de informar por qué One Tap no apareció y el botón quedaría cargando indefinidamente. Cobertura en `frontend/src/auth/google.test.ts` (client_id correcto, ausencia de `scope`, camino feliz, cierre sin credencial, timeout, carga y reintento del script) y en `AuthContext.test.tsx` (el body exacto que se postea). **El login con Google no funciona end-to-end hasta que se ejecute la Task 1 del [plan de backend](../superpowers/plans/2026-08-04-login-oauth-backend.md)**, que todavía exige `access_token`.
```

- [ ] **Step 2: Actualizar la guía de API según el estado del plan de backend**

Primero, determinar en qué estado está el documento:

Run: `grep -n "id_token" docs/development/api-frontend.md`

- **Si el `grep` no devuelve nada** (el plan de backend no se ejecutó todavía): en `docs/development/api-frontend.md`, reemplazar los puntos 1 y 2 de la subsección "### Login con Google (único flujo social soportado)" por:

```markdown
1. El SPA usa Google Identity Services — **Sign In With Google** (`google.accounts.id`, no `google.accounts.oauth2`) para obtener un **ID token** (JWT OIDC) directamente en el navegador, vía One Tap. **No existe flujo de redirect/Authorization Code** — se eliminó del backend el 2026-08-01 (commit `cdefb7e`); no hay ruta de callback que implementar.
2. `POST /api/auth/google/` con `{"id_token": "<jwt>"}` (ADR 0019). **Estado a 2026-08-04: el frontend ya manda `id_token` y el backend todavía exige `access_token`** — el login con Google no funciona end-to-end hasta que se ejecute la Task 1 del [plan de backend](../superpowers/plans/2026-08-04-login-oauth-backend.md). El motivo del cambio: la ruta de validación de `access_token` en allauth (`_fetch_user_info`) no verificaba que el token se hubiera emitido para el `client_id` de Atenea (`audience`).
```

- **Si el `grep` sí devuelve líneas** (el plan de backend ya corrió y esa sección ya describe `id_token`): no reescribas nada de esa sección. Agrega únicamente, al final del punto 2, la frase:

```markdown
El frontend implementa este transporte desde 2026-08-04 (`frontend/src/auth/google.ts`, `solicitarIdTokenDeGoogle`).
```

En cualquiera de los dos casos, agregar además al final de la subsección "### Otros endpoints de `accounts`" (después de la tabla):

```markdown
El SPA consume `roles` de este payload para decidir qué puede ver el usuario (`frontend/src/auth/rol.ts`: `useEsAsesor`, `useEsAlumno`; `frontend/src/auth/RutaProtegida.tsx`). Ya **no** existe el sondeo de `GET /api/asesorias/registros/` con lectura de 200 vs 403 que describía la deuda técnica 0010: si `roles` no viene en la respuesta, el frontend trata al usuario como si no tuviera ningún rol.
```

- [ ] **Step 3: Actualizar el gap de foco en la guía de componentes**

En `docs/development/contribuir-componentes.md`, en la sección "## Checklist de accesibilidad", reemplazar el bullet **Foco visible** completo por:

```markdown
- **Foco visible:** **todo elemento interactivo nuevo necesita un estado de foco visible** (ring o cambio de color con suficiente contraste), no solo quitar el outline por defecto del navegador. El patrón del proyecto es `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary`, ya aplicado en `components/ui/Boton.tsx` (y por lo tanto en todos sus consumidores), `screens/Login.tsx` y `screens/Landing.tsx`. El gap original que motivó esta regla —`Login.tsx` usaba `outline-none focus:border-primary`, sin anillo perceptible— quedó corregido el 2026-08-04. Lo que sigue sin cubrir: los controles interactivos de `features/asesorias/` que no pasan por `Boton`.
```

- [ ] **Step 4: Anotar el estado del consumidor en la deuda técnica 0010**

Agregar al **final** de `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md` (después de lo que ya haya ahí, sin tocar ninguna línea anterior — el plan de backend edita la cabecera y agrega su propia sección, y los dos cambios no se pisan en ningún orden de ejecución):

```markdown
## Estado del consumidor en el frontend (2026-08-04)

El workaround 1 (sondear `GET /api/asesorias/registros/` y leer 200 vs 403) **ya no existe en el código**: `frontend/src/auth/rol.ts` lee `roles` del contexto de autenticación, que a su vez lo toma del payload de `GET /api/auth/user/` y del body del login. Se agregó también `useEsAlumno()`, que con el sondeo habría exigido un segundo endpoint centinela — el escenario que la sección "Qué se simplificó" señalaba como el límite del parche.

Se eliminó **sin fallback**: si el backend todavía no manda `roles`, el frontend trata al usuario como si no tuviera ningún rol y las rutas de asesor redirigen a Home. Es deliberado, para que la falta del contrato sea visible en vez de quedar enmascarada por el sondeo viejo (y porque el login con Google, en la misma pasada, ya depende del mismo plan de backend). Ver `docs/superpowers/plans/2026-08-04-login-oauth-frontend.md`.

El workaround 2 (mostrar `"Alumno #<id>"` en vez de un nombre) **no** se tocó en el frontend: depende de `alumno_nombre`/`asesor_nombre` en `AsesoriaSerializer` y de las pantallas de asesorías, fuera del alcance del plan de login.
```

- [ ] **Step 5: Registrar la ejecución en el ledger de progreso**

En `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`:

No toques la fila 9 de la tabla "Estado por paso" — esa fila la cierra la **escritura** del plan, no su ejecución; si ya dice `Completo`, déjala así.

Agregar una sección nueva antes de `## Próximo paso`:

```markdown
## Hallazgos de la ejecución del plan de login frontend (`dev-frontend`)

- **El bloqueo más importante que deja este trabajo:** el frontend ya habla el contrato nuevo y el backend todavía no. `POST /api/auth/google/` sigue exigiendo `access_token`, así que el login con Google no funciona en runtime; y `GET /api/auth/user/` sigue sin `roles`, así que `/asesorias*` redirige a `/home` para todos. Las dos cosas se resuelven ejecutando las Tasks 1 y 3 del plan de backend del paso 4 — **este plan y esas dos tasks son una sola unidad de release**, no dos entregas independientes. La suite de tests pasa porque mockea las respuestas y no toca red.
- Se decidió eliminar el sondeo de rol **sin fallback transitorio**. La alternativa (leer `roles` si viene, sondear si no) mantendría viva exactamente la deuda 0010 y escondería que el backend no se ha integrado; además no compraría nada, porque el login con Google ya está bloqueado por el mismo plan de backend en la misma pasada.
- Google Identity Services obligó a una decisión que ni la spec ni ADR 0019 fijaban: conservar el botón propio "Continuar con Correo Ciencias" (la spec exige que la UX no cambie) implica usar **One Tap programático** (`google.accounts.id.prompt()`), no el botón renderizado de Google. One Tap puede quedar suprimido por el navegador o por una decisión previa del usuario, y en modo FedCM las notificaciones dejan de decir por qué. Mitigación implementada: timeout de 60 s + `cancel()`, para que el botón no quede girando. **Señal para revisitar:** si al probar con el backend integrado One Tap resulta suprimido con frecuencia, la salida es el botón renderizado de Google — y eso sí es un cambio de UX, así que pasa por `superpowers:brainstorming` antes de código, según el paso 7.
- El foco visible entró en `Boton.tsx` (una vez, para sus 6 consumidores) en vez de repetirse por pantalla, y se escribió con utilidades de Tailwind en vez de la clase `.foco-visible` que introduce el plan del paso 8 — mismo CSS resultante, cero dependencia de orden entre los dos planes. Cuando ambos estén ejecutados, sustituir las utilidades por la clase es un refactor de una línea por sitio.
- `AuthContext.test.tsx`, `rol.test.tsx` y los tests nuevos comparten `src/test/factories.ts`. Vale la pena saber por qué está fuera de un archivo `.test.ts`: `tsconfig.app.json` excluye los tests de `tsc -b` y Vitest no typechecea, así que ese archivo es **el único punto donde el compilador verifica la forma de `AuthUser`** contra el contrato del backend.
- Quedó sin hacer, con razón: mostrar el mensaje real del backend cuando el correo no está provisionado ("No existe una cuenta para este correo. Contacta a la SAE."). Exige `primerMensajeDeError`, que el plan del paso 8 crea en `frontend/src/api/errores.ts`; escribirlo aquí duplicaría ese archivo. Es el primer trabajo natural una vez que los dos planes estén ejecutados.
```

Y reemplazar la sección `## Próximo paso` por:

```markdown
## Próximo paso

Ejecutar el plan de backend del paso 4 (`docs/superpowers/plans/2026-08-04-login-oauth-backend.md`), al menos sus Tasks 1 y 3, que son las que desbloquean el login con Google y la detección de rol que el frontend ya consume. Después de eso quedan pendientes, en este orden de dependencia: el plan de componentes del paso 8 (`docs/superpowers/plans/2026-08-04-sistema-componentes.md`, escrito y sin ejecutar), y los ajustes del paso 3 que ninguno de los dos planes cubre — el "← Home" y los subtabs de semestre de `SesionesAsesor`, el "Cancelar asesoría" en contorno y los íconos de formato en `DetalleAsesoria`, y la tarjeta condicional de Home (que ya puede leer el rol con `useEsAsesor()`/`useEsAlumno()`, pero necesita el ícono `IconAsesoriasAcademicas` y su propia revisión visual).
```

- [ ] **Step 6: Verificar que ningún archivo falta y que la suite sigue verde**

Run:
```bash
cd /home/hyfi/Development/atenea-fc
for f in docs/decisions/0019-transporte-login-google-id-token.md \
         docs/development/api-frontend.md \
         docs/development/contribuir-componentes.md \
         docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md \
         docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md; do
  [ -f "$f" ] && echo "OK $f" || echo "MISSING $f"
done
grep -rn "initTokenClient\|solicitarAccessTokenDeGoogle" docs/ || echo "SIN REFERENCIAS AL TRANSPORTE VIEJO EN docs/"
pnpm --dir frontend test && pnpm --dir frontend build && pnpm --dir frontend lint
```

Expected: las 5 líneas dicen `OK`; el `grep` imprime `SIN REFERENCIAS AL TRANSPORTE VIEJO EN docs/` (si aparece alguna línea en un documento que describa el transporte como vigente, corrígela antes de comitear; las menciones dentro de ADR 0018/0019 que hablan del transporte **descartado** en pasado son correctas y deben quedarse — por eso este `grep` se lee, no se automatiza). Los tres comandos de frontend en verde.

- [ ] **Step 7: Commit**

```bash
git add docs/decisions/0019-transporte-login-google-id-token.md \
        docs/development/api-frontend.md \
        docs/development/contribuir-componentes.md \
        docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md \
        docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md
git commit -s -m "[docs] documentar el login con id_token y el consumo de rol en el frontend" \
  -m "- Changelog en ADR 0019 con la implementacion de frontend y las dos
    decisiones de forma que la ADR no fijaba: One Tap programatico en vez
    del boton renderizado de Google, y timeout de 60 s con cancel().
- api-frontend.md: el SPA manda id_token y consume roles del payload de
    usuario; queda anotado que el backend todavia no acompana el contrato.
- contribuir-componentes.md: el gap de foco de Login.tsx pasa de gap a
    patron del proyecto, con lo que sigue sin cubrir acotado.
- Deuda tecnica 0010: se registra que el workaround 1 desaparecio del
    frontend, sin fallback y a proposito, y que el 2 sigue vigente.
- Ledger: hallazgos de la ejecucion, con el bloqueo de runtime hacia el
    plan de backend como el punto principal, y proximo paso reescrito."
```

---

## Self-Review

**1. Cobertura de los requisitos**

| Requisito | Fuente | Task |
|---|---|---|
| `google.ts` migra de `initTokenClient` a `google.accounts.id` + callback de credential | spec paso 2, "Cambios de frontend"; ADR 0019 | 2 |
| Ya no se solicita `scope: 'email profile'` | spec paso 2; ADR 0019 | 2 (aserción explícita `expect(config).not.toHaveProperty('scope')`) |
| `loginWithGoogle` manda `{id_token}` en vez de `{access_token}` | spec paso 2 | 2 |
| Sigue siendo popup/One Tap, sin navegación de página completa ni ruta de callback | ADR 0019 | 2 (Decisión 1) |
| `Login.tsx` no cambia su UX de cara al usuario | spec paso 2 | 2 (no se toca), 6 (solo foco y composición de `Boton`, mismo aspecto y mismo copy) |
| `Landing.tsx` deja de hacer `navigate('/home')` directo y navega solo tras un login exitoso | spec paso 2, decisión 5 | 5 |
| Manejo de carga/error en `Landing.tsx`, análogo al de `Login.tsx` | spec paso 2, decisión 5 | 5 |
| Cero variables de entorno nuevas, mismo `VITE_GOOGLE_OAUTH_CLIENT_ID` | spec paso 2, "Variables de entorno" | Global Constraints; verificado en 2 |
| Split dev/prod del JWT propio sin cambios | ADR 0018 decisión 2; spec paso 2 decisión 2 | ninguna task toca `persistirSesion`/`api/client.ts` |
| Logout sin invalidar refresh token sin cambios | ADR 0018 decisión 3; deuda 0007 | ninguna task toca `logout` |
| `AuthContext` expone rol/perfil con la forma del contrato de backend | plan paso 4, Task 3; instrucción del paso 9 | 1 |
| `roles` como lista de claves estables (`alumno`/`academico`/`asesor_academico`) | plan paso 4, decisión 3 | 1 (`RolUsuario`) |
| `asesor_academico` cuenta aunque `activo` sea `false` | plan paso 4, decisión 5 | 1 (comentario en el tipo), 3 (dos tests: hook y guard) |
| El rol llega con el login mismo, sin llamada extra | plan paso 4, Task 3 | 1 (test que cuenta las llamadas a `apiGet`) |
| Decidir y documentar si `useEsAsesor()` deja de sondear | instrucción del paso 9 | 3 + Decisiones 5 y 6 |
| Hook de rol nuevo para alumno | instrucción del paso 9 | 3 (`useEsAlumno`) |
| `RutaProtegida.tsx` revisado a la luz de lo anterior | instrucción del paso 9 | 3 |
| Dependencia hacia el plan de backend documentada explícitamente, no silenciada | instrucción del paso 9; precedente del paso 8 | Global Constraints, Decisión 6, Tasks 2/3 (bullets de commit), Task 7 (ledger, ADR 0019, api-frontend.md, deuda 0010) |
| Tests de comportamiento en todo el flujo de auth con lógica propia, con mocks del backend y sin red | paso 7, "Estructura de un componente nuevo" | 1 (6), 2 (7+1), 3 (4+4), 4 (4), 5 (4), 6 (5) — 35 casos |
| `:focus-visible` en todo elemento interactivo tocado | paso 7, checklist | 4, 5, 6 |
| Labels asociados, el placeholder nunca es el único label | paso 7, checklist | 6 (`htmlFor`/`useId`) |
| `aria-hidden` en SVG decorativos | paso 7, checklist | 6 (flecha de volver), 4 (spinner, ya lo tenía) |
| Live regions para errores async (`role="alert"`) | paso 7, checklist | 5, 6 |
| Pares `{rol}`/`on-{rol}` de contraste, cero hex literales | paso 7, lineamientos; ADR 0014 | 4, 5, 6 (solo tokens ya existentes) |
| Criterio `components/ui/` vs `features/` respetado | paso 7 | 4 (`Boton` no conoce el dominio; no se crea nada en `features/`) |
| Consistencia con el plan del paso 8 sin depender de él | instrucción del paso 9 | Global Constraints; Decisión 8 |

**Fuera de alcance a propósito, sin omisión silenciosa.** Cada uno con su razón, y todos registrados también en el ledger (Task 7, Step 5):

- **CSRF en cookie JWT (deuda 0009).** La decisión 6 de la spec del paso 2 ya decidió explícitamente **no** activarlo en este trabajo: `SameSite="Lax"` ya bloquea el escenario clásico, la señal de revisión documentada no se ha dado, y activarlo exigiría trabajo de frontend (leer y reenviar el token CSRF en cada `POST`/`PATCH`/`DELETE`) que el cambio de transporte de Google no motiva. `JWT_AUTH_COOKIE_USE_CSRF` sigue en `False` y `api/client.ts` no se toca.
- **Invalidación de refresh token en logout (deuda 0007).** Sin cambios, por la decisión 3 de ADR 0018 reafirmada en la decisión 3 de la spec. `logout()` sigue limpiando solo el lado del cliente.
- **Cualquier cambio al plan de backend del paso 4.** Ese plan no se toca, no se reescribe y no se ejecuta aquí. Este plan se implementa **contra** sus contratos, no los negocia.
- **Los diálogos, tabs y demás componentes del plan del paso 8.** Login no usa ninguno. `Dialogo`, `dialog.tsx`, `tabs.tsx`, `cn()`, el alias `@/` y la clase `.foco-visible` quedan intactos, y ningún archivo de este plan colisiona con los de aquel.
- **Resolver la deuda 0010 más allá de lo que el contrato del paso 4 ya definió.** El workaround 2 (mostrar `"Alumno #<id>"`) y un endpoint para que un asesor resuelva el nombre de un alumno arbitrario son Fase 3; el frontend de este plan ni los usa ni los prepara.
- **El mensaje real del backend cuando el correo no está provisionado.** Exige `primerMensajeDeError`, que el plan del paso 8 crea en `api/errores.ts`; escribirlo aquí duplicaría ese archivo y crearía la dependencia de orden entre planes que este plan evita. No hay regresión: hoy `Login.tsx` ya muestra el mismo mensaje genérico. Ver Decisión 12.
- **Los otros pendientes que el paso 8 dejó anotados para el paso 9** — el "← Home" y los subtabs de semestre de `SesionesAsesor`, el "Cancelar asesoría" en contorno y los íconos de formato de `DetalleAsesoria`, y la tarjeta condicional de Home. Son trabajo de las vistas de asesorías (spec del paso 3), no de login; la tarjeta de Home además necesita el ícono `IconAsesoriasAcademicas` y su propia revisión visual. De esa lista, este plan sí toma el único ítem que es de login: el foco visible de `Login.tsx` (Task 6).

**2. Placeholders**

Sin `TBD`, sin "implementar después", sin "manejar los casos borde". Cada step de código trae el bloque completo listo para pegar; cada step de verificación trae el comando exacto y el resultado esperado, incluida la razón por la que cada test falla en RED (y, donde aplica, cuáles **no** fallan y por qué eso es lo correcto — Tasks 5 y 6). Las dos únicas instrucciones condicionales son deliberadas y acotadas: el Step 2 de la Task 7 (el estado de `api-frontend.md` depende de si el plan de backend ya corrió, resuelto con un `grep` que decide entre dos textos, ambos escritos completos) y el Step 5 de la misma task (no tocar la fila 9 del ledger si ya está cerrada).

**3. Consistencia de tipos y nombres**

- `AuthUser`, `RolUsuario`, `PerfilAlumno`, `PerfilAcademico`, `PerfilAsesorAcademico` se definen en la Task 1 y se usan con esos nombres exactos en las Tasks 2, 3 y 5. Los nombres de campo son los del payload del backend (`snake_case`: `perfil_asesor_academico`, `numero_cuenta`, `area_nombre`), porque son datos que vienen por HTTP — mientras que los identificadores propios del frontend siguen en `camelCase`/español, que es la convención que ya usa `api.ts`.
- `usuarioDePrueba(overrides)` se define en la Task 1 y se llama con esa firma en las Tasks 1, 2 y 3.
- `useAuth()` devuelve `{user, roles, status, loginWithPassword, loginWithGoogle, logout}` desde la Task 1, y ese objeto completo es el que los dobles de las Tasks 5 y 6 construyen (con `as ReturnType<typeof auth.useAuth>`, el mismo idioma que ya usa `SesionesAsesor.test.tsx`).
- `solicitarIdTokenDeGoogle(clientId: string): Promise<string>` se define en la Task 2 y se espía con ese nombre en `AuthContext.test.tsx` de la misma task. `NotificacionPrompt` se exporta de `google.ts` y se importa en `google.test.ts`.
- `useEsAsesor(): boolean` cambia de forma en la Task 3, y su único consumidor de producción (`RutaDeAsesor`) se actualiza en el mismo commit — no queda ningún punto del repo esperando el `{data, isPending}` viejo (verificado por `grep` en el Step 7 de esa task).
- `Boton` conserva exactamente su firma (`cargando`, `variante`, más los atributos nativos) en la Task 4, que es lo que permite que las Tasks 5 y 6 lo compongan sin adaptadores y que sus 6 consumidores actuales no cambien.
- El trío de clases de foco es literalmente el mismo string en `Boton.tsx` (Task 4), `Landing.tsx` (Task 5) y la constante `FOCO_VISIBLE` de `Login.tsx` (Task 6), y es el que los tests de las tres tasks asertan.

**4. Verificación previa contra el código real**

Antes de escribir el plan se confirmó, no se infirió: `Login.tsx` y `Landing.tsx` **no** usan `Boton` hoy (escriben sus clases a mano), y esas clases coinciden carácter por carácter con las que `Boton` produce para las variantes `primario` y `secundario` — por eso la migración de las Tasks 5 y 6 no cambia el aspecto. `Boton` tiene hoy 6 consumidores, ninguno de los cuales pasa un `className` con `outline-*` que compita con el foco nuevo. `useEsAsesor` tiene un único consumidor de producción (`RutaProtegida.tsx`), lo que permite cambiar su forma de retorno en un solo commit. `AuthContext.test.tsx` ya espía `client.apiGet` con `vi.spyOn` y funciona, y `SesionesAsesor.test.tsx` ya espía exports de módulo con `as ReturnType<typeof ...>` — los dos idiomas que este plan reutiliza; `@testing-library/user-event` **no** está instalado, por eso todo es `fireEvent`. `tsconfig.app.json` excluye `src/**/*.test.ts(x)` de `tsc -b` y Vitest transpila sin typechecar, lo que es la razón concreta de que `src/test/factories.ts` exista fuera de un archivo de test; en cambio `noUnusedLocals` sí aplica a `src/`, así que los imports muertos de las Tasks 3 y 6 sí rompen el build. `index.css` (ADR 0014) define `--color-primary`, que es lo que hace válido `outline-primary` como utilidad de Tailwind v4 sin configuración adicional, y hoy **no** contiene ninguna clase `.foco-visible` (la introduce el plan del paso 8). `frontend/.env.example` ya trae `VITE_GOOGLE_OAUTH_CLIENT_ID`, así que no hay variable nueva que agregar.

---

## Decisiones de diseño no fijadas por los specs — detalle

**1. One Tap programático, no el botón renderizado de Google.** ADR 0019 y la spec dicen "el flujo de botón/One Tap" sin elegir. La restricción que decide es de la propia spec: *"`Login.tsx` — el botón sigue disparando el mismo flujo…; no cambia su UX de cara al usuario"*. El botón renderizado (`google.accounts.id.renderButton`) es la vía más confiable de obtener un `credential`, pero pinta el botón con la marca de Google, con su propio texto y su propio estilo — reemplazar "Continuar con Correo Ciencias" por "Sign in with Google" **es** un cambio de UX, y además uno que la spec excluye y que el paso 7 mandaría a `superpowers:brainstorming` con mockup antes de escribir código. Queda entonces `initialize` + `prompt()` (One Tap), que sí permite disparar el flujo desde un botón propio. El costo real y asumido: One Tap puede quedar suprimido por el navegador o por una decisión previa del usuario ("no volver a mostrar"), y el usuario ve que el botón no hace nada más que un mensaje de error. **Señal para revisitar, ya anotada en el ledger:** si al probar con el backend integrado la supresión resulta frecuente, la salida es el botón renderizado, y ese cambio entra por brainstorming. Las alternativas descartadas: incrustar el botón de Google invisible debajo del propio y reenviarle el clic (frágil, no testeable, y depende de detalles internos del iframe de Google), y volver a Authorization Code + redirect (ya descartada por ADR 0019 por razones que no cambian).

**2. Timeout de 60 s y `cancel()`.** Sin esto, la promesa de `solicitarIdTokenDeGoogle` puede no resolverse nunca: si One Tap no aparece y la notificación no es informativa —lo que ocurre en modo FedCM, donde `isNotDisplayed()`/`isSkippedMoment()` dejaron de estar disponibles— nadie llama ni al callback ni al listener, y el `finally` de `Login`/`Landing` no llega a correr, así que el botón queda deshabilitado con el spinner girando hasta que el usuario recargue. Sesenta segundos es un valor conservador: más largo que cualquier interacción real de One Tap, corto frente a "para siempre". Se acompaña de `google.accounts.id.cancel()` para no dejar un prompt colgado que interfiera con el siguiente intento, y eso además hace el comportamiento observable en el test. El mensaje de rechazo es el mismo que el de cancelación, para que las pantallas no tengan que distinguir dos casos que el usuario vive igual. La guarda `try/catch` alrededor de los métodos de notificación es de la misma familia: si la API cambia bajo nuestros pies, el flujo degrada a "espera y expira", no a una excepción.

**3. Campos de perfil/rol obligatorios en `AuthUser`.** La alternativa era declararlos opcionales (`roles?: RolUsuario[]`) para reflejar que el backend todavía no los manda. Se descarta: haría que **cada** consumidor tuviera que defenderse (`user?.roles?.includes(...)`), volviendo permanente una condición transitoria y perdiendo la ayuda del compilador el día que el backend sí los mande. Con los campos obligatorios, el desajuste temporal se concentra en un solo `?? []` con un comentario que dice exactamente qué lo justifica y cuándo deja de hacer falta, más un test que fija ese comportamiento (`no revienta si la respuesta todavía no trae roles`). Es la misma forma que el plan del paso 8 usó para sus endpoints inexistentes: escribir el contrato real, no un contrato defensivo.

**4. El contexto expone `roles` derivado.** Podría no hacerlo y dejar que `rol.ts` leyera `user?.roles ?? []`. Se prefiere exponerlo porque el `?? []` de la Decisión 3 tiene que vivir en **un** lugar para que la promesa "ningún consumidor se defiende por su cuenta" sea cierta, y porque `roles` es el dato que casi todos los consumidores quieren (los perfiles completos los quiere casi nadie). No se guarda en un `useState` aparte: se deriva de `user` en cada render, así que no hay dos fuentes de verdad que puedan desincronizarse. Que sea un array nuevo por render es irrelevante — todos sus consumidores lo reducen inmediatamente a un booleano.

**5. `useEsAsesor()` devuelve `boolean`; se agrega `useEsAlumno()`; no se agrega `useEsAsesorActivo()`.** El `{data, isPending}` de hoy es un artefacto de que el rol se obtenía con una petición; sin petición no hay estado pendiente propio que reportar, y conservar la envoltura obligaría a fabricar un `isPending: false` mentiroso. El único consumidor ya tenía que combinar dos estados de carga y ahora combina uno. `useEsAlumno()` se agrega porque es el hook que la deuda 0010 nombraba como el punto donde el sondeo se rompía ("no escala a más de un rol sin agregar una llamada de sondeo por cada rol") y porque la tarjeta condicional de Home del paso 3 lo va a pedir; ahora cuesta una línea. `useEsAsesorActivo()` **no** se agrega: nadie lo consume hoy, `perfil_asesor_academico.activo` ya está disponible en el contexto para quien lo necesite, y adivinar la forma que querrá el primer consumidor real es exactamente el tipo de API especulativa que YAGNI descarta.

**6. Se elimina el sondeo sin fallback.** La alternativa concreta era un `useEsAsesor` de transición: usar `roles` si el campo viene, y sondear `GET /api/asesorias/registros/` si no. Se descarta por tres razones, en orden de peso. (a) **No compra nada:** la Task 2 de este mismo plan ya deja el login con Google inoperante hasta que el backend se integre, así que ninguna cantidad de fallback en `rol.ts` vuelve la rama usable end-to-end; solo salvaría el caso de un usuario que entra con contraseña y quiere ver `/asesorias`. (b) **Esconde el problema:** un fallback silencioso hace que la falta de integración solo se note cuando alguien la busca, mientras que la redirección a `/home` es visible el primer día. (c) **Mantiene viva la deuda:** el sondeo es literalmente el workaround que la deuda 0010 describe, y este plan es el que lo cierra del lado del cliente; conservarlo "por si acaso" convierte una eliminación en una duplicación. Es también el criterio que ya tomó el plan del paso 8 con sus tres endpoints inexistentes. La consecuencia queda declarada en Global Constraints, en los bullets de los commits de las Tasks 2 y 3, y en el ledger: **este plan y las Tasks 1 y 3 del plan de backend son una sola unidad de release.**

**7. `usuarioDePrueba()` en `src/test/factories.ts`.** El repo hoy usa fábricas locales (`crearAsesoria` dentro de `SesionesAsesor.test.tsx`), y seguir esa convención habría significado copiar un objeto de 10 campos en tres archivos de test. Lo que decide no es la duplicación sino el typechecking: `tsconfig.app.json` excluye `src/**/*.test.ts(x)` de `tsc -b` y Vitest transpila sin typechecar, así que una fábrica local dentro de un `.test.tsx` **no la verifica nadie** — podría divergir de `AuthUser` sin que ningún comando del repo se queje. Un archivo que no termina en `.test.ts` sí entra en `tsc -b`, y con eso `pnpm build` se convierte en la alarma que avisa cuando el contrato de usuario cambia. El costo (un archivo de código no productivo dentro de `src/`) es nulo en el bundle: nada de `src/` lo importa, así que Vite lo elimina.

**8. Foco con utilidades de Tailwind, no con `.foco-visible`.** La Task 1 del plan del paso 8 declara `.foco-visible:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px }` en `index.css`. Usarla aquí obligaría a ejecutar ese plan antes que este, o a declarar la clase también en este plan y arriesgar una definición duplicada según el orden. `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary` produce exactamente el mismo CSS (en Tailwind v4 las utilidades de ancho de outline fijan el estilo `solid`, y `--color-primary` ya existe desde ADR 0014), no toca ningún archivo compartido, y deja los dos planes conmutables. Cuando ambos estén ejecutados, sustituir las utilidades por la clase es un refactor de una línea por sitio, anotado en el ledger. La contrapartida asumida: el trío se repite en cuatro lugares (`Boton.tsx` y las tres apariciones de la constante `FOCO_VISIBLE` de `Login.tsx`), no en uno.

**9. El foco entra en `Boton`, y `Login`/`Landing` pasan a componerlo.** Alternativa: agregar las clases de foco al markup de cada pantalla y dejar `Boton` como está. Se descarta porque `Boton` es el punto donde el proyecto ya centralizó "cómo se ve un botón", y el foco es parte de eso — repetirlo por pantalla garantiza que el próximo botón nazca sin él, que es exactamente cómo se generó el gap que el paso 7 documenta. Además, `Boton` no lo toca ningún otro plan (el del paso 8 lo declara intocado por su decisión 5), así que el cambio no compite con nada. La migración de las dos pantallas es el corolario: sus clases escritas a mano ya son las de `Boton`, así que componerlo es sustituir código duplicado por el componente que existe para eso, y de paso heredar el spinner de `cargando`. El único botón que **no** migra es el secundario de `Landing` ("Entrar con correo y contraseña"): es texto plano sin fondo ni contorno, y `Boton` no tiene una variante así; inventar una para un solo caso sería peor que dejarle sus tres clases y su foco.

**10. `Landing` no redirige si ya hay sesión.** Sería fácil agregar "si `status === 'authenticated'`, `Navigate` a `/home`", y es una mejora plausible. No se hace: ninguna spec lo pide, cambia el comportamiento de la ruta pública `/` (que hoy siempre muestra la landing, incluso con sesión), y decidirlo bien exige responder qué debe ver un usuario con sesión que escribe la URL raíz a propósito — una pregunta de producto, no de implementación. Este plan corrige el defecto que la spec sí nombró (el botón que navegaba sin autenticar) y deja la pantalla pública como está. Si en runtime resulta molesto, es un cambio de tres líneas con su propio test.

**11. La edición de `api-frontend.md` es condicional.** Es el único documento que los dos planes (paso 4 y paso 9) modifican en la misma sección, y el orden de ejecución entre ellos no está fijado. Escribir un texto único obligaría a suponer un orden, y suponer mal produciría o una descripción falsa del backend o el borrado del trabajo del otro plan. El `grep` del Step 2 de la Task 7 resuelve la ambigüedad en un segundo y las dos ramas están escritas completas, así que no es un "TBD" disfrazado. El mismo cuidado se aplicó a la deuda 0010: la sección que agrega este plan va **al final** del archivo y no toca ninguna línea que el plan de backend edite, así que los dos cambios conviven en cualquier orden.

**12. Las pantallas conservan su copy genérico de error.** La spec del paso 2 documenta que un correo sin cuenta provisionada devuelve `400` con "No existe una cuenta para este correo. Contacta a la SAE." — un mensaje mucho más útil que "No se pudo iniciar sesión con Google.". Mostrarlo exige extraer el primer mensaje del cuerpo del `ApiError`, que es justamente `primerMensajeDeError`, la función que el plan del paso 8 saca a `frontend/src/api/errores.ts` (su decisión 10). Escribirla aquí crearía dos versiones del mismo archivo entre planes, que es el único acoplamiento que este plan se propuso evitar. Como no hay regresión (hoy `Login.tsx` ya muestra el mismo texto genérico y `Landing.tsx` no muestra nada), se difiere con la anotación explícita de que es el primer trabajo a hacer una vez que ambos planes estén ejecutados — registrada en el ledger, no solo aquí.

---

### Critical Files for Implementation
- /home/hyfi/Development/atenea-fc/frontend/src/auth/AuthContext.tsx
- /home/hyfi/Development/atenea-fc/frontend/src/auth/google.ts
- /home/hyfi/Development/atenea-fc/frontend/src/auth/rol.ts
- /home/hyfi/Development/atenea-fc/frontend/src/screens/Landing.tsx
- /home/hyfi/Development/atenea-fc/frontend/src/api/types.ts
