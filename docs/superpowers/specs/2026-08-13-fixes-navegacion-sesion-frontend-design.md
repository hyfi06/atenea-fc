# Diseño de Spec — Fixes de navegación y sesión del frontend

**Fecha:** 2026-08-13
**Status:** Approved

---

## Contexto

### Por qué este plan

Cuatro bugs reportados sobre el frontend desplegado en `atenea.unam.dev`. Los cuatro son de **navegación y sesión**, no de datos: ninguno toca la API, ninguno cambia un contrato y ninguno introduce una decisión de arquitectura nueva.

1. **No hay forma de cerrar sesión.** El botón hamburguesa de `Home` existe visualmente pero no tiene `onClick`; `logout()` ya está implementado en `AuthContext` y nadie lo llama.
2. **No hay forma de volver al inicio desde Asesorías.** Ni `/sae/asesorias` ni `/asesorias` — las dos pantallas raíz de sección — tienen enlace de regreso a `/home`. Quien entra por la tarjeta de servicio queda atrapado salvo por el botón "atrás" del navegador.
3. **La landing no reconoce la sesión.** Quien ya tiene sesión y abre `/` ve la pantalla de "Continuar con Correo Ciencias" como si fuera un visitante nuevo. Lo mismo en `/login`.
4. **Las rutas inexistentes renderizan la nada.** `App.tsx` no tiene ruta comodín: un typo en la URL deja una página en blanco, sin mensaje ni salida.

**No amerita ADR nuevo.** Un ADR registra una decisión de arquitectura; esto son correcciones a pantallas ya decididas por [ADR 0014](../../decisions/0014-tokens-logo-iconos-frontend.md), [ADR 0018](../../decisions/0018-contrato-autenticacion-frontend-backend.md), [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md), [ADR 0022](../../decisions/0022-asesorias-vista-unificada-frontend.md) y [ADR 0024](../../decisions/0024-asesorias-sae-admin-frontend.md), que siguen vigentes sin cambio. Tampoco genera deuda técnica nueva: no hay simplificación deliberada que sostener — cada fix cierra el hueco completo dentro de su alcance.

### Estado actual (referencias verificadas)

- `screens/Home.tsx:17-23` — botón `aria-label="Menú"` con `<svg>` de tres líneas, **sin `onClick`**, `h-9 w-9` (bajo el toque mínimo de 44 px) y sin `.foco-visible`. Es el único elemento del header aparte del `Logo`.
- `auth/AuthContext.tsx:65-74` — `logout()` hace `POST /api/auth/logout/` (tolerando el fallo), limpia `localStorage` y deja `status = 'unauthenticated'`. Ya está en el `AuthContextValue` (línea 15) y nadie lo consume.
- `api/types.ts` — `AuthUser` expone `nombre_completo` y `email` (además de `pk`, `first_name`, `apellido1/2`, `roles` y los tres perfiles).
- `auth/RutaProtegida.tsx:6-12` — `PantallaCargando` (spinner centrado, `min-h-svh`, `aria-label="Cargando"`) está definido **como función local no exportada**; lo usan las tres guardas (`RutaDeAsesor`, `RutaDeAsesorias`, `RutaDeSAE`).
- `screens/Landing.tsx` y `screens/Login.tsx` — ambas consumen `useAuth()` sólo para `loginWithGoogle`/`loginWithPassword`; **ninguna lee `status`**. Tras un login exitoso navegan a `/home` con `navigate('/home')`.
- `App.tsx:22-128` — `BrowserRouter`/`Routes`/`Route`; `/`, `/login`, `/home`, `/health` públicas (sin guarda), `/asesorias/*` bajo `RutaDeAsesorias`/`RutaDeAsesor`, `/sae/*` bajo `RutaDeSAE`. **No hay `path="*"`.**
- `features/asesorias/screens/OfertaAsesorias.tsx:52-54` — patrón de regreso ya establecido: `<button type="button" onClick={() => navigate(rutaVolver)} className="foco-visible w-fit min-h-11 text-sm text-primary">{etiquetaVolver}</button>`, colocado **antes** del `<h1>`.
- `features/asesorias/screens/Asesorias.tsx:35-36` y `screens/AdminAsesorias.tsx:23-24` — ambas abren con `<main className="flex min-h-svh flex-col gap-4 px-6 py-6">` + `<h1>`, sin botón de regreso.
- `components/ui/Boton.tsx` — `Boton({ cargando = false, variante = 'primario' | 'secundario' | 'peligro', ...ButtonHTMLAttributes })`; renderiza `<button>` con `h-11`, `rounded-full` y foco visible propio.
- `components/Logo.tsx` — `Logo({ className })`, `<svg role="img" aria-label="Atenea">`.
- `index.css` — clases de motion `.entrada-dialogo` (180 ms ease-out), `.entrada-lista`, `.spinner`, y la utilidad `.foco-visible`; todas las animaciones están neutralizadas dentro de `@media (prefers-reduced-motion: reduce)`.
- **No existe** ningún componente de menú/dropdown/popover en `components/ui/` (verificado repo-wide). Sí existe `Dialogo`/`dialog` sobre `@radix-ui/react-dialog`, pero es un diálogo modal, no un menú anclado.
- Tests: Vitest + Testing Library, colocados junto al archivo, hooks mockeados con `vi.spyOn`, factories en `src/test/factories.ts` (`usuarioDePrueba`, `usuarioSAE`). `@testing-library/user-event` **no** está instalado: se usa `fireEvent`.
- `screens/Home.test.tsx` mockea **sólo** `useEsMiembroSAE` y no envuelve en `AuthProvider`. Al pasar `Home` a consumir `useAuth()`, ese archivo revienta con `useAuth debe usarse dentro de AuthProvider` si no se actualiza.
- `screens/Landing.test.tsx` y `screens/Login.test.tsx` ya mockean `useAuth` completo con `status: 'unauthenticated'`, así que los casos existentes sobreviven al guard nuevo sin tocarse.

---

## Decisiones de arquitectura

| Decisión | Elegida | Alternativa descartada | Por qué |
|---|---|---|---|
| Contenido del menú hamburguesa | **Identidad arriba** (`nombre_completo` + `email`) **+ "Cerrar sesión" abajo** | Sólo el botón de cerrar sesión | Decisión explícita del usuario. El menú también responde "¿con qué cuenta estoy?", que hoy no se puede saber en ningún lado de la app. |
| Patrón ARIA del menú | **Disclosure**: disparador con `aria-expanded` + `aria-controls`, panel `<div>` con `id` | `role="menu"` + `role="menuitem"` | `role="menu"` exige que **todo** hijo sea `menuitem`; el bloque de identidad no es accionable y quedaría fuera del árbol de accesibilidad o mal anunciado. El disclosure es correcto para un panel mixto (texto + una acción). |
| Dependencia para el menú | **Ninguna**: React + CSS, cierre por `Escape` y por `mousedown` fuera, con listeners en `document` | Añadir `@radix-ui/react-dropdown-menu` | [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md) admite primitivos de Radix, pero una dependencia nueva para un panel de dos filas no se paga. `Dialogo` no sirve: es modal y se apodera del foco de la página. |
| Ubicación del menú | Componente propio **`components/MenuUsuario.tsx`** con test propio | Inline dentro de `Home.tsx` | Concentra el estado (abierto/cerrado, listeners de `document`, foco de retorno) fuera de la pantalla, y permite probar el comportamiento sin montar la rejilla de servicios. `Home` queda como layout. |
| Menú para visitante sin sesión | `MenuUsuario` **no renderiza nada** si `status !== 'authenticated'` | Mostrar la hamburguesa deshabilitada, o con "Iniciar sesión" | `/home` es ruta pública (sin guarda): un anónimo puede llegar. Sin sesión no hay identidad que mostrar ni sesión que cerrar; un control que no hace nada es exactamente el bug que se está arreglando. |
| Destino tras cerrar sesión | `await logout()` → `navigate('/')` | `navigate('/login')` | La landing es la entrada canónica de la app; `/login` es la ruta secundaria de correo+contraseña. Decisión explícita del usuario. |
| Enlace de regreso en Asesorías | Botón **"← Inicio"** → `/home` en **`/sae/asesorias` y `/asesorias`** | Sólo en el área SAE; o un `navigate(-1)` | Ambas son pantallas raíz de sección a las que se llega desde la rejilla de `Home`; el bug es el mismo en las dos. Destino fijo y no `-1` porque el historial puede venir de cualquier lado (recarga directa, deep link). |
| Forma del enlace de regreso | Reusar **literalmente** el patrón de `OfertaAsesorias:52-54` (botón de texto `text-primary`, `min-h-11`, `w-fit`, antes del `<h1>`) | Componente `BotonVolver` compartido nuevo | Con tres usos del mismo patrón de tres líneas, extraer un componente añade una indirección sin quitar nada. Si aparece un cuarto uso con variantes, ahí se extrae. |
| Estado de carga en `/` y `/login` | **Spinner** (`PantallaCargando`) mientras `status === 'loading'` | Renderizar la landing y "parpadear" al redirigir | Mismo criterio que las guardas de `RutaProtegida`: nunca se muestra un estado que se va a contradecir un tick después. |
| Reuso de `PantallaCargando` | **Extraerlo** a `components/PantallaCargando.tsx` y que `RutaProtegida.tsx` lo importe | Inlinear el spinner en `Landing` y `Login` | Con cinco consumidores (3 guardas + 2 entradas de auth), copiar el markup garantiza que se desincronicen. La extracción es mecánica y no cambia el comportamiento de ninguna guarda. |
| Alcance del redirect por sesión | **Landing (`/`) y Login (`/login`)** | Sólo la landing | Decisión explícita del usuario: son dos entradas a la misma acción y ya comparten flujo y copy de error (comentario en `Landing.tsx:13-14`). Dejar `/login` sin guard sólo mueve el bug. |
| 404 | Pantalla nueva **`screens/NoEncontrado.tsx`** + `<Route path="*">` al final de `Routes` | `<Navigate to="/" replace />` en el comodín | Redirigir en silencio esconde el typo y deja al usuario preguntándose qué pasó. Una pantalla explícita con salida es la convención de la web y cuesta un archivo. |
| Salida del 404 | Botón "Volver al inicio" → **`/`** | → `/home` | `/` ya resuelve el caso con sesión gracias al fix 3 (redirige a `/home`) y el caso sin sesión (muestra la landing). Un solo destino cubre ambos. |

---

## Pantallas y flujos

### 1. Menú de usuario — `components/MenuUsuario.tsx` (crear)

**Consumido por:** `screens/Home.tsx`, en el lugar exacto del botón actual del header.

**Estado:** `abierto: boolean`, `cerrando: boolean`. `useAuth()` aporta `user` y `status`.

**Render:**

- Si `status !== 'authenticated'` o `user === null` → `null`.
- Disparador: `<button type="button" aria-label="Menú" aria-haspopup="true" aria-expanded={abierto} aria-controls={idPanel}>` con el mismo `<svg>` de tres líneas, ahora `h-11 w-11`, `rounded-full` y `.foco-visible`.
- Panel (sólo con `abierto`): `<div id={idPanel}>` posicionado con `absolute right-0 top-12 z-10`, `rounded-2xl bg-surface-container p-3 shadow-lg`, clase de motion `entrada-dialogo`. Contiene, en este orden:
  1. `user.nombre_completo` — `text-sm font-medium text-on-surface`.
  2. `user.email` — `truncate text-xs text-on-surface-variant` + `title` con el correo completo.
  3. Separador `border-outline-variant`.
  4. `<button type="button">Cerrar sesión</button>` — `.foco-visible`, `min-h-11`, `text-error`, `disabled={cerrando}`.

**Interacción:**

- Click en el disparador → alterna `abierto`.
- `Escape` (keydown en `document`) → cierra y **devuelve el foco al disparador**.
- `mousedown` en `document` fuera del contenedor → cierra (sin mover el foco). Se usa `mousedown` y no `pointerdown` porque jsdom no implementa `PointerEvent` de forma confiable y el evento de compatibilidad cubre igual el caso táctil.
- Los listeners se registran sólo mientras `abierto` y se limpian en el `return` del `useEffect`.
- "Cerrar sesión" → `setCerrando(true)` → `await logout()` → `navigate('/')`. `logout()` no lanza (traga el error del `POST`), así que no hay rama de error que mostrar; `cerrando` sólo evita el doble disparo.

**`Home.tsx`:** sustituye el `<button aria-label="Menú">` inerte por `<MenuUsuario />`. El header no cambia: el ancla del panel es el `<div className="relative">` propio de `MenuUsuario`, que envuelve al disparador. Nada más se toca (rejilla de servicios y tarjeta SAE intactas).

### 2. Regreso a Inicio — `Asesorias.tsx` y `AdminAsesorias.tsx` (modificar)

En ambas, como **primer hijo** del `<main>`, antes del `<h1>`:

```tsx
<button type="button" onClick={() => navigate('/home')} className="foco-visible w-fit min-h-11 text-sm text-primary">
  ← Inicio
</button>
```

`AdminAsesorias` ya tiene `navigate` en scope; `Asesorias` también. No se toca ninguna otra pantalla: `/asesorias/*` y `/sae/*` en profundidad ya tienen su propio regreso a la raíz de sección.

### 3. Estado de carga compartido — `components/PantallaCargando.tsx` (crear)

Se mueve la función tal cual desde `auth/RutaProtegida.tsx:6-12` y se exporta:

```tsx
export function PantallaCargando() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="spinner h-6 w-6 text-primary" aria-label="Cargando" />
    </div>
  )
}
```

`RutaProtegida.tsx` borra la definición local y la importa. Las tres guardas quedan idénticas en comportamiento.

### 4. Guard de sesión en las entradas de auth — `Landing.tsx` y `Login.tsx` (modificar)

En ambas, **después de todos los hooks** (`useNavigate`, `useAuth`, los `useState`) y antes del `return` del JSX:

```tsx
if (status === 'loading') return <PantallaCargando />
if (status === 'authenticated') return <Navigate to="/home" replace />
```

`status` se desestructura del `useAuth()` que ya se llama. `Navigate` se importa de `react-router-dom`. El `navigate('/home')` que sigue a un login exitoso se conserva: es el camino que ya tienen los tests y el guard sólo lo hace redundante, no incorrecto.

### 5. Pantalla 404 — `screens/NoEncontrado.tsx` (crear)

**Ruta:** `path="*"`, último `<Route>` de `Routes` en `App.tsx`.

**Cuerpo:** misma estética que la landing — `<main className="flex min-h-svh flex-col items-center justify-center gap-4 px-6 py-12 text-center">` con:

- `<Logo className="h-16 w-16 text-primary" />`
- `<p className="text-5xl font-semibold text-primary">404</p>`
- `<h1 className="text-lg font-semibold text-on-background">Página no encontrada</h1>`
- `<p className="max-w-[28ch] text-sm text-on-surface-variant">La dirección que abriste no existe o cambió de lugar.</p>`
- `<Boton type="button" onClick={() => navigate('/')} className="px-6">Volver al inicio</Boton>`

---

## Testing

Vitest + Testing Library, tests colocados, `fireEvent` (no hay `user-event`), `vi.spyOn` sobre los módulos de hooks, factories de `src/test/factories.ts`.

**`components/MenuUsuario.test.tsx` (crear)** — mockea `useAuth` (patrón de `Landing.test.tsx`) y monta en `MemoryRouter`+`Routes` con una ruta `/` señuelo:

- Con sesión, el panel está cerrado al inicio: el disparador tiene `aria-expanded="false"` y no hay "Cerrar sesión" en el DOM.
- Al hacer click en "Menú", aparecen `nombre_completo`, `email` y "Cerrar sesión", y `aria-expanded` pasa a `"true"`.
- `Escape` cierra el panel y el foco vuelve al disparador.
- `mousedown` fuera del menú lo cierra.
- "Cerrar sesión" llama a `logout` una sola vez y navega a `/`.
- Con `status: 'unauthenticated'` no se renderiza el disparador.

**`screens/Home.test.tsx` (actualizar — obligatorio)** — `montar()` debe además mockear `useAuth` con `usuarioDePrueba()` y `status: 'authenticated'`; si no, `useAuth` lanza al no haber `AuthProvider`. Casos existentes (tarjeta SAE condicional, navegación a `/sae/asesorias`, resto de servicios) se conservan tal cual + un caso nuevo: **hacer click en la hamburguesa abre el menú** (aparecen el correo y "Cerrar sesión"). Ojo: un caso que sólo busque el botón "Menú" pasaría sin arreglar nada — el botón inerte ya existe.

**`features/asesorias/screens/Asesorias.test.tsx` (actualizar)** — el helper `envolver` pasa de `MemoryRouter` pelón a `MemoryRouter`+`Routes` con `/asesorias` y `/home`; caso nuevo: click en "← Inicio" renderiza la pantalla de home.

**`features/asesorias/screens/AdminAsesorias.test.tsx` (actualizar)** — añadir la ruta `/home` al `Routes` existente; caso nuevo: click en "← Inicio" navega a home.

**`screens/Landing.test.tsx` / `screens/Login.test.tsx` (actualizar)** — el helper de montaje acepta `status` (default `'unauthenticated'`, que deja pasar todos los casos actuales sin tocarlos). Casos nuevos en cada archivo:

- Con `status: 'loading'` se ve el spinner (`aria-label="Cargando"`) y **no** el formulario/los botones de la pantalla.
- Con `status: 'authenticated'` se renderiza la pantalla de home (redirect) y no la de auth.

**`screens/NoEncontrado.test.tsx` (crear)** — `App` no se puede montar en jsdom (trae su propio `BrowserRouter` y arrastra todas las pantallas con sus queries), así que **no hay `App.test.tsx`**: el comodín se prueba aquí, montando `MemoryRouter` + un `Routes` mínimo que incluye `path="*"` e `initialEntries={['/ruta-que-no-existe']}`. Casos: una dirección desconocida renderiza "404" y el encabezado "Página no encontrada"; "Volver al inicio" navega a `/`. Que la línea `<Route path="*">` esté efectivamente en `App.tsx` lo cubre `tsc -b` (la pantalla debe existir e importarse) más la revisión del diff del commit.

**`auth/RutaProtegida.test.tsx`** — sin cambios; sigue verde tras extraer `PantallaCargando`, y esa es justamente la verificación de que la extracción no alteró nada.

Verificación por tarea, siempre desde `frontend/`: `npx vitest run <ruta>` para el test puntual, `npm test` para la suite (`vitest run`), `npm run build` (`tsc -b && vite build`) y `npm run lint` (`oxlint`).

---

## Out of scope

- **Guardas para `/home`.** `/home` sigue siendo ruta pública, igual que hoy; el menú simplemente no se dibuja sin sesión. Proteger la ruta es un cambio de política de acceso, no un fix de navegación.
- **Menú de usuario en pantallas distintas de `Home`.** El header con hamburguesa sólo existe en `Home`; convertirlo en layout compartido es un rediseño.
- **Más entradas en el menú** (perfil, preferencias, ayuda): no hay pantallas a las que apuntar.
- **Invalidación del refresh token al cerrar sesión** → ya registrado en [deuda 0007](../../technical-debt/0007-logout-sin-invalidacion-refresh-token.md); este fix cablea el `logout()` existente, no cambia su contrato.
- **Breadcrumbs / barra de navegación global.** Se mantiene el patrón actual de un enlace de regreso por pantalla.
- **`document.title` por ruta**, incluido el del 404.

---

## Self-review

- **Sin placeholders ni TBD:** cada fix tiene archivo, punto de inserción, markup concreto, tokens verificados contra `index.css` y casos de prueba nombrados.
- **Alcance cohesivo:** los cuatro fixes comparten superficie (navegación y sesión del SPA) y ninguno toca la API, los hooks de datos ni las pantallas de asesorías en profundidad.
- **Ambigüedades resueltas explícitamente:** contenido del menú (identidad + logout), destino tras el logout (`/`), alcance del redirect (`/` **y** `/login`), alcance del "← Inicio" (`/asesorias` **y** `/sae/asesorias`), y el reuso de `PantallaCargando` (se extrae a `components/`, no se duplica).
- **Consistente con los patrones del repo:** botón de regreso copiado de `OfertaAsesorias`, spinner idéntico al de las guardas, `Boton`/`Logo` existentes, `.foco-visible` y `min-h-11` en todo lo interactivo, motion sólo con clases de `index.css` que ya respetan `prefers-reduced-motion`, cero dependencias nuevas.
- **Riesgo conocido y atendido:** `Home` empieza a consumir `useAuth()`, lo que rompe `Home.test.tsx` tal como está hoy; la actualización de ese archivo es un requisito explícito, no un efecto colateral.
- **Sin ADR ni deuda nuevos, y dicho por qué:** son correcciones dentro de decisiones ya tomadas, y ninguna deja un supuesto frágil que alguien deba revisar después.
