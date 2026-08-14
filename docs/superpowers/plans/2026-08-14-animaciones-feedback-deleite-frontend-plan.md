# Animaciones de feedback y deleite del frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar los huecos de cobertura de motion catalogados en el spec: press feedback en todo control (A), salidas animadas para toast/dropdown/modal (B), transición en mensajes de error, swaps de skeleton y listas sin stagger (C), y entrada escalonada en las dos pantallas de baja frecuencia (D).

**Architecture:** Todo el vocabulario nuevo vive en `frontend/src/index.css`: tres variables de easing (`--ease-out`, `--ease-in-out`, `--ease-drawer`), dos clases de press feedback compartidas (`.presionable`, `.fila-interactiva`), seis `@keyframes` nuevas con sus clases (`.salida-toast`, `.entrada-menu`, `.salida-menu`, `.salida-dialogo`, `.salida-velo`, `.entrada-deleite`), y la lista de `prefers-reduced-motion` extendida. Los componentes sólo **aplican** esas clases; ninguno declara `cubic-bezier`, `transition` ni `@keyframes` propios. Las tres salidas animadas (toast, dropdown, diálogo) usan el mismo patrón de cierre en dos tiempos: un state de "saliendo/cerrando" activa la clase de salida y un `setTimeout` de la misma duración ejecuta el desmontaje real.

**Tech Stack:** React 19 + TypeScript + Vite, Tailwind v4 (`@tailwindcss/vite`), Radix (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`), Vitest + Testing Library (jsdom). **Sin librería de animación** — CSS puro.

**Spec:** [`2026-08-14-animaciones-feedback-deleite-frontend-design.md`](../specs/2026-08-14-animaciones-feedback-deleite-frontend-design.md) — catálogo A/B/C/D, valores exactos y sección "Rechazado". Los tokens de easing y las reglas de uso están en [ADR 0026](../../decisions/0026-tokens-motion-frontend.md). **Ninguna task de este plan reabre una decisión de diseño**: el "por qué" vive en esos dos documentos y no se repite aquí.

## Global Constraints

- **Comandos** (siempre desde `frontend/`): test puntual `npx vitest run <ruta>`; suite completa `npm test` (= `vitest run`); build `npm run build` (= `tsc -b && vite build`); lint `npm run lint` (= `oxlint`). Verificado contra `frontend/package.json`.
- **Sin dependencias nuevas.** No se instala framer-motion/motion/react-spring ni `@radix-ui/react-toast`.
- **Este plan está escrito contra `dev` @ `63e1ad0`**, donde el plan [`2026-08-14-minors-navegacion-y-botonvolver-frontend-plan.md`](2026-08-14-minors-navegacion-y-botonvolver-frontend-plan.md) **todavía no está aplicado**. Por eso cada edición se ancla en el **string verbatim** que aparece en el archivo, no sólo en el número de línea: si los números corrieron, busca el string.
- **`@testing-library/user-event` NO está instalado.** Todos los tests usan `fireEvent` de `@testing-library/react`.
- **`noUnusedLocals` y `noUnusedParameters` están en `true`** (`tsconfig.app.json`): si una task deja un import, una variable o un parámetro sin usar, `npm run build` falla. Las tasks que corren ese riesgo lo dicen explícitamente.
- **No se testea la temporización visual de una animación.** No existe una aserción del tipo "esta animación dura 160 ms". Lo único testeable de un state machine nuevo es: (a) qué clase lleva el elemento en cada fase, (b) que el elemento sigue montado inmediatamente después de pedir el cierre, y (c) que tras `vi.advanceTimersByTime(<ms>)` el elemento desaparece o el callback se invoca. Patrón de timers falsos ya presente en el repo: `src/auth/google.test.ts:95,100`.
- **`vi.restoreAllMocks()` no restaura timers.** Todo test que llame `vi.useFakeTimers()` necesita `afterEach(() => vi.useRealTimers())` en su `describe`, y `act()` de `@testing-library/react` alrededor de cada `vi.advanceTimersByTime(...)` que dispare un `setState`.
- **`@media (hover: hover) and (pointer: fine)`** para todo `hover:` nuevo (ADR 0026). Los tres `hover:bg-surface-container-high` inline existentes migran a `.fila-interactiva` al tocarse.
- **Toda clase de animación nueva entra al bloque `@media (prefers-reduced-motion: reduce)`** en el mismo commit que la introduce. En este plan eso ocurre una sola vez, en la Task 1.
- **No se toca la API ni los hooks de datos.** Ningún cambio en `features/*/api.ts`, `api/client.ts` ni `api/types.ts`.
- **Sin ADR ni ítem de deuda nuevos.** ADR 0026 ya cubre la única decisión de arquitectura; el resto es catálogo, ya aprobado en el spec.
- **Fuera de alcance, por decisión explícita del spec (sección "Rechazado"):** transiciones de ruta SPA en `App.tsx`, indicador deslizante en `components/ui/tabs.tsx`, parallax/mouse-tracking en `Landing.tsx`, animación de datos leídos. Ninguna task puede introducirlos.
- **Commits** atómicos, formato `[type][scope] resumen` + lista de cambios + `Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>` ([ADR 0007](../../decisions/0007-commit-message-convention.md), [`docs/development/commit-conventions.md`](../../development/commit-conventions.md)). Cada task trae su comando de commit literal.

---

## File Structure

| Archivo | Responsabilidad | Acción | Task |
|---|---|---|---|
| `frontend/src/index.css` | Tokens de easing + todas las clases y keyframes de motion + lista de `prefers-reduced-motion` | Modificar | 1 |
| `frontend/src/components/ui/Boton.tsx` | Botón base de la app | Modificar: `.presionable` | 2 |
| `frontend/src/components/ui/Boton.test.tsx` | Tests del botón | Modificar: 1 caso nuevo | 2 |
| `frontend/src/components/ui/Dialogo.tsx` | Botones de acción de diálogos (`BASE_BOTON`) | Modificar: `.presionable` | 2 |
| `frontend/src/screens/Home.tsx` | Tile "Asesorías · SAE" (A2) + grid de servicios (C3) | Modificar | 3, 11 |
| `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx` | Tarjeta de asesoría clicable | Modificar: `.fila-interactiva` | 4 |
| `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx` | Wizard de agendado: filas de asesor/día/bloque, error, listas | Modificar | 4, 9, 11 |
| `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx` | Listado de la oferta | Modificar | 4, 11 |
| `frontend/src/features/asesorias/screens/MisMaterias.tsx` | Materias del asesor: fila + botón quitar + lista | Modificar | 4, 11 |
| `frontend/src/features/asesorias/screens/MiHorario.tsx` | Horario del asesor: slot clicable + lista de slots | Modificar | 4, 12 |
| `frontend/src/features/asesorias/screens/AdminAsesorias.tsx` | Resultados de búsqueda de asesor/alumno (SAE) | Modificar | 5, 12 |
| `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx` | Botón de asesor seleccionable (SAE) | Modificar: `.fila-interactiva` | 5 |
| `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx` | Lista de materias del diálogo | Modificar | 5, 12 |
| `frontend/src/components/ui/Retroalimentacion.tsx` | Hook + toast: salida animada (`saliendo`) | Modificar | 6 |
| `frontend/src/components/ui/Retroalimentacion.test.tsx` | Tests del toast | Crear | 6 |
| `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx` | Consumidor del toast | Modificar: pasa `saliendo` | 6 |
| `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx` | Consumidor del toast + errores + notas previas | Modificar | 6, 9, 12 |
| `frontend/src/components/MenuUsuario.tsx` | Dropdown del header: salida animada | Modificar | 7 |
| `frontend/src/components/MenuUsuario.test.tsx` | Tests del dropdown | Modificar: 2 casos adaptados + 1 nuevo | 7 |
| `frontend/src/components/ui/dialog.tsx` | Wrapper Radix: intercepta `onOpenChange(false)` y anima la salida | Modificar | 8 |
| `frontend/src/components/ui/dialog.test.tsx` | Tests del wrapper | Modificar: 1 caso adaptado | 8 |
| `frontend/src/components/ui/Dialogo.test.tsx` | Tests del diálogo compartido | Modificar: 1 caso partido en 2 | 8 |
| `frontend/src/screens/Login.tsx` | Mensaje de error del formulario | Modificar: `.entrada-lista` | 9 |
| `frontend/src/screens/Landing.tsx` | Mensaje de error (C1) + entrada de deleite (D2) | Modificar | 9, 14 |
| `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx` | Swap skeleton → contenido real | Modificar: `.entrada-lista` | 10 |
| `frontend/src/screens/NoEncontrado.tsx` | Pantalla 404 | Modificar: `.entrada-deleite` ×5 | 13 |

**Orden de dependencias:**

- **Task 1 es prerrequisito de TODAS las demás.** Ninguna clase (`.presionable`, `.fila-interactiva`, `.salida-toast`, `.entrada-menu`, `.salida-menu`, `.salida-dialogo`, `.salida-velo`, `.entrada-deleite`) ni variable (`--ease-out`, `--ease-in-out`, `--ease-drawer`) existe antes de esa task.
- **Tasks 2–14 se ejecutan en orden numérico, una a la vez, no en paralelo.** Varias comparten archivo (`Home.tsx` en 3 y 11; `MisMaterias.tsx` en 4 y 11; `MiHorario.tsx` en 4 y 12; `AgendarAsesoria.tsx` en 4, 9 y 11; `AdminAsesorias.tsx` en 5 y 12; `DialogoAgregarMateria.tsx` en 5 y 12; `DetalleAsesoria.tsx` en 6, 9 y 12; `Landing.tsx` en 9 y 14). Las ediciones no se solapan en el mismo string, pero sí corren los números de línea.
- Salvo por eso, las tasks 2–14 son independientes entre sí: cada una puede revisarse y revertirse sola.

**Decisiones de alcance registradas aquí** (resoluciones conservadoras de puntos donde el spec no encaja con el código real; ninguna reinterpreta el propósito de un ítem):

1. **Los tres tokens de easing se declaran en un bloque `:root`, no dentro de `@theme`.** ADR 0026 admite las dos formas ("el bloque `@theme`/`:root`"). Se elige `:root` porque garantiza que las variables se emitan aunque ninguna utilidad de Tailwind las use — todo su consumo en este plan es vía `var()` dentro del propio `index.css`. Al ir después de los `@theme`, el bloque también redefine los `--ease-out`/`--ease-in-out` que Tailwind trae de fábrica, que es exactamente el efecto que ADR 0026 busca ("un único lugar fija el feel de toda la app").
2. **El state `cerrando` de `MenuUsuario.tsx:18` NO está sin usar.** El spec dice que sí ("ya tiene un state `cerrando` sin usar"); verificado en el código, `cerrando` es el guard de doble disparo del cierre de sesión (`setCerrando(true)` en `cerrarSesion`, `disabled={cerrando}` en el botón "Cerrar sesión"). Reusarlo para la animación del panel rompería el logout. La Task 7 introduce un state **nuevo y distinto**, `cerrandoMenu`, y deja `cerrando` intacto.
3. **`Login` no recibe animación de entrada de pantalla.** La tabla de decisiones del spec dice que "`Login` usa `.entrada-lista` existente", pero el catálogo D no tiene fila para `Login`: no hay elementos ni stagger especificados. Sin valores exactos que copiar, la lectura conservadora es que esa fila sólo excluye a `Login` de `.entrada-deleite`. `Login` recibe únicamente el ítem C1 (Task 9), que sí está especificado.
4. **`OfertaAsesorias.tsx:67` queda fuera de C3.** Ese `.map()` produce elementos `<option>` dentro de un `<select>`; los `<option>` no son animables por CSS en ningún navegador. Se omite.
5. **`MiHorario.tsx:201` y `:208` quedan fuera de C3.** `:201` es el `.map()` de los `TabsTrigger` (la barra de pestañas, chrome siempre visible, no una lista que aparece) y `:208` es el `.map()` que devuelve los `TabsContent` (paneles contenedores, uno por día, no ítems de lista). C3 se aplica en `MiHorario` sólo a `:227` (`slots.map`), que es la lista real.
6. **C2 se reduce a `AdminAsesorDetalle.tsx`.** De los seis sitios que lista el spec, cuatro ya quedan cubiertos sin tocarlos: `Asesorias.tsx:148` y `AdminAsesores.tsx:45` porque su contenido real ya entra con `.entrada-lista` (`TarjetaAsesoria.tsx:82` y `AdminAsesores.tsx:58`), y `OfertaAsesorias.tsx:87` y `MiHorario.tsx:219` porque su contenido real recibe el stagger de C3 en las Tasks 11 y 12. Sólo `AdminAsesorDetalle.tsx:47,87` queda descubierto, y es lo que hace la Task 10.
7. **En los dos controles con estado "seleccionado" (`DialogoAgregarMateria.tsx:71`, `AdminOfertaMateria.tsx:130`), `.fila-interactiva` se aplica sólo en la rama NO seleccionada.** `.fila-interactiva:hover { background-color: … }` tiene mayor especificidad que la utilidad `bg-primary-container` de Tailwind: aplicada sin condición, borraría el resaltado del ítem seleccionado al pasar el mouse. El costo es que el ítem seleccionado no tiene press feedback — es el compromiso que menos código no relacionado toca.
8. **`Dialogo.tsx:106` (el `<p role="alert">` de error del diálogo) queda fuera de C1.** El spec enumera cinco ubicaciones concretas y ésa no está entre ellas; no se amplía la lista.
9. **`TarjetaAsesoria.tsx:95` (la variante no interactiva) no recibe `.fila-interactiva`.** Comparte la constante `clasesBase` con el botón de `:88`, pero es un `<div tabIndex={-1}` sin `onClick`: darle hover y press feedback anunciaría una interacción que no existe. La clase se aplica en el `className` del botón, no en `clasesBase`.
10. **En `MiHorario.tsx` el índice del `.map()` nuevo se llama `indiceSlot`, no `indice`.** Ya existe un `indice` en el scope exterior (`DIAS_CORTOS.map((_, indice)`, línea 208) que se usa **dentro** del callback interno (`slotsDelDia(indice, bloques)`, `tocarSlot(indice, …)`). Nombrar `indice` al parámetro interno lo sombrearía y rompería el horario.

---

## Task 1: Vocabulario de motion en `index.css` (tokens + clases compartidas)

**Depends on:** nada. **Es prerrequisito de las Tasks 2–14.**

**Files:**
- Modify: `frontend/src/index.css`

**Interfaces:**
- Produces (consumidos por las Tasks 2–14): variables `--ease-out`, `--ease-in-out`, `--ease-drawer`; clases `.presionable`, `.fila-interactiva`, `.salida-toast`, `.entrada-menu`, `.salida-menu`, `.salida-dialogo`, `.salida-velo`, `.entrada-deleite`.
- No consume nada. No toca ninguna clase existente.

- [ ] **Step 1: Declarar los tokens de easing**

En `frontend/src/index.css`, buscar este bloque (líneas 66-69) y reemplazarlo:

```css
body {
  background-color: var(--color-background);
  color: var(--color-on-background);
}
```

por:

```css
/* Tokens de motion — ADR 0026. Se declaran en `:root` y no dentro de `@theme`
   para garantizar que se emitan siempre: todo su consumo en este archivo es
   vía `var()`, no vía utilidades de Tailwind. Al ir después de los bloques
   `@theme`, este bloque también redefine los `--ease-out`/`--ease-in-out` que
   Tailwind trae de fábrica: un solo lugar fija el "feel" de la app. */
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
}

body {
  background-color: var(--color-background);
  color: var(--color-on-background);
}
```

- [ ] **Step 2: Añadir las keyframes nuevas**

Buscar este bloque (líneas 96-99) y reemplazarlo:

```css
@keyframes entrada-velo {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

por:

```css
@keyframes entrada-velo {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes salida-toast {
  from { opacity: 1; transform: translateY(0); }
  to   { opacity: 0; transform: translateY(8px); }
}

@keyframes entrada-menu {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}

@keyframes salida-menu {
  from { opacity: 1; transform: scale(1); }
  to   { opacity: 0; transform: scale(0.95); }
}

@keyframes salida-dialogo {
  from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  to   { opacity: 0; transform: translate(-50%, -48%) scale(0.97); }
}

@keyframes salida-velo {
  from { opacity: 1; }
  to   { opacity: 0; }
}

@keyframes entrada-deleite {
  from { opacity: 0; transform: translateY(12px) scale(0.95); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
```

- [ ] **Step 3: Añadir las clases nuevas**

Buscar este bloque (líneas 136-138) y reemplazarlo:

```css
.entrada-velo {
  animation: entrada-velo 180ms ease-out;
}
```

por:

```css
.entrada-velo {
  animation: entrada-velo 180ms ease-out;
}

/* Salidas simétricas. Cada una es más rápida que su entrada: el sistema debe
   sentirse responsivo al descartar aunque haya sido deliberado al abrir.
   `forwards` mantiene el estado final durante los milisegundos que quedan
   entre el fin de la animación y el desmontaje. */
.salida-toast {
  animation: salida-toast 200ms var(--ease-out) forwards;
}

/* `transform-origin: top right` porque el panel está anclado al disparador
   (`absolute right-0 top-12`), no centrado en viewport como `.entrada-dialogo`. */
.entrada-menu {
  transform-origin: top right;
  animation: entrada-menu 180ms var(--ease-drawer);
}

.salida-menu {
  transform-origin: top right;
  animation: salida-menu 140ms var(--ease-out) forwards;
}

.salida-dialogo {
  animation: salida-dialogo 150ms var(--ease-out) forwards;
}

.salida-velo {
  animation: salida-velo 150ms var(--ease-out) forwards;
}

.entrada-deleite {
  animation: entrada-deleite 400ms var(--ease-out) backwards;
}

/* Press feedback compartido. Mismo criterio que `.foco-visible` de abajo: el
   comportamiento lo comparten 15+ sitios, así que se declara una vez aquí en
   vez de repetir utilidades `active:` en cada componente.
   `.presionable` — botones y tiles independientes.
   `.fila-interactiva` — filas y tarjetas de ancho completo: scale más sutil
   para que el borde no "salte", más el hover que antes vivía inline. */
.presionable {
  transition: transform 160ms var(--ease-out);
}

.presionable:active:not(:disabled) {
  transform: scale(0.97);
}

.fila-interactiva {
  transition: transform 160ms var(--ease-out), background-color 150ms ease;
}

.fila-interactiva:active:not(:disabled) {
  transform: scale(0.99);
}

@media (hover: hover) and (pointer: fine) {
  .fila-interactiva:hover {
    background-color: var(--color-surface-container-high);
  }
}
```

- [ ] **Step 4: Extender el bloque de `prefers-reduced-motion`**

Buscar el bloque final del archivo (líneas 149-160) y reemplazarlo completo:

```css
@media (prefers-reduced-motion: reduce) {
  .skeleton,
  .entrada-lista,
  .salida-lista,
  .pulso-exito,
  .spinner,
  .entrada-dialogo,
  .entrada-velo {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

por:

```css
@media (prefers-reduced-motion: reduce) {
  .skeleton,
  .entrada-lista,
  .salida-lista,
  .pulso-exito,
  .spinner,
  .entrada-dialogo,
  .entrada-velo,
  .salida-toast,
  .entrada-menu,
  .salida-menu,
  .salida-dialogo,
  .salida-velo,
  .entrada-deleite {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }

  /* `.presionable` y `.fila-interactiva` usan `transition`, no `animation`:
     necesitan su propia regla en el mismo checklist. */
  .presionable,
  .fila-interactiva {
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 5: Verificar que las 8 clases y los 3 tokens existen**

Run: `grep -n -e '--ease-out:' -e '--ease-in-out:' -e '--ease-drawer:' -e '^\.presionable {' -e '^\.fila-interactiva {' -e '^\.salida-toast {' -e '^\.entrada-menu {' -e '^\.salida-menu {' -e '^\.salida-dialogo {' -e '^\.salida-velo {' -e '^\.entrada-deleite {' src/index.css | wc -l`
Expected: `11` — una línea por declaración. Si sale menos, falta alguna de los Steps 1-3; el mismo `grep` sin `| wc -l` muestra cuáles sí están.

- [ ] **Step 6: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS. Esta task no cambia comportamiento: si algún test falla aquí, no es por este cambio (CSS puro, sin clases nuevas aplicadas todavía). Si `npm run build` falla, la causa más probable es una llave `}` desbalanceada en alguno de los bloques pegados.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/index.css
git commit -m "[feat][frontend] vocabulario de motion: tokens de easing y clases compartidas

- tres variables de easing de ADR 0026 en :root: --ease-out, --ease-in-out, --ease-drawer
- clases de press feedback compartidas: .presionable y .fila-interactiva, con hover gateado
- keyframes y clases de salida: salida-toast, entrada-menu, salida-menu, salida-dialogo, salida-velo
- clase de entrada de deleite: entrada-deleite
- las ocho clases nuevas entran al bloque de prefers-reduced-motion

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 2: Press feedback en el botón base y en los botones de diálogo (A1)

**Depends on:** Task 1 (`.presionable`).

**Files:**
- Modify: `frontend/src/components/ui/Boton.tsx:18`
- Modify: `frontend/src/components/ui/Boton.test.tsx` (1 caso nuevo)
- Modify: `frontend/src/components/ui/Dialogo.tsx:38-39` (constante `BASE_BOTON`)

- [ ] **Step 1: Añadir el caso de test**

En `frontend/src/components/ui/Boton.test.tsx`, buscar:

```tsx
  it('muestra el spinner y queda deshabilitado mientras carga', () => {
```

e insertar **antes** de esa línea:

```tsx
  it('lleva la clase de press feedback compartida', () => {
    render(<Boton>Entrar</Boton>)

    expect(screen.getByRole('button', { name: 'Entrar' })).toHaveClass('presionable')
  })

```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/components/ui/Boton.test.tsx`
Expected: FAIL sólo en el caso nuevo — el botón todavía no lleva `presionable`. Los otros 4 casos pasan.

- [ ] **Step 3: Aplicar `.presionable` al botón base**

En `frontend/src/components/ui/Boton.tsx`, reemplazar:

```tsx
      className={`flex h-11 items-center justify-center gap-2 rounded-full text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60 ${VARIANTES[variante]} ${className}`}
```

por:

```tsx
      className={`presionable flex h-11 items-center justify-center gap-2 rounded-full text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60 ${VARIANTES[variante]} ${className}`}
```

- [ ] **Step 4: Aplicar `.presionable` a los botones de acción de diálogos**

En `frontend/src/components/ui/Dialogo.tsx`, reemplazar:

```tsx
const BASE_BOTON =
  'foco-visible flex min-h-11 min-w-0 items-center justify-center gap-2 whitespace-normal rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60'
```

por:

```tsx
const BASE_BOTON =
  'presionable foco-visible flex min-h-11 min-w-0 items-center justify-center gap-2 whitespace-normal rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60'
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/ui/Boton.test.tsx src/components/ui/Dialogo.test.tsx`
Expected: PASS (5 casos en `Boton`, los existentes de `Dialogo` sin cambio). Si falla el caso de `Dialogo` que recorre `screen.getAllByRole('button')` verificando `foco-visible`, la causa más probable es haber **sustituido** `foco-visible` en vez de anteponerle `presionable`.

- [ ] **Step 6: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ui/Boton.tsx frontend/src/components/ui/Boton.test.tsx frontend/src/components/ui/Dialogo.tsx
git commit -m "[feat][frontend] press feedback en el boton base y en los botones de dialogo

- Boton.tsx y BASE_BOTON de Dialogo.tsx llevan la clase .presionable
- el control mas reusado de la app ya da señal de 'te escuche' al presionar
- test: el boton base declara la clase compartida

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 3: Press feedback en el tile SAE de Home (A2)

**Depends on:** Task 1 (`.presionable`).

**Files:**
- Modify: `frontend/src/screens/Home.tsx:28`

- [ ] **Step 1: Aplicar `.presionable`**

En `frontend/src/screens/Home.tsx`, reemplazar:

```tsx
            className="foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl bg-secondary-container p-3 text-center text-on-secondary-container"
```

por:

```tsx
            className="presionable foco-visible flex min-h-11 flex-col items-center gap-2 rounded-2xl bg-secondary-container p-3 text-center text-on-secondary-container"
```

- [ ] **Step 2: Verificar**

Run: `npx vitest run src/screens/Home.test.tsx && npm run build && npm run lint`
Expected: PASS. Los tiles del `.map()` de `services` **no** se tocan aquí: no son interactivos (son `<div>` sin `onClick`); su animación de entrada es la Task 11.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/screens/Home.tsx
git commit -m "[feat][frontend] press feedback en el tile de Asesorias SAE de Home

- el unico tile clicable del grid lleva .presionable

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 4: `.fila-interactiva` en las filas de alumno y asesor (A3 + A4, parte 1 de 2)

**Depends on:** Task 1 (`.fila-interactiva`).

**Files:**
- Modify: `frontend/src/features/asesorias/components/TarjetaAsesoria.tsx:87-88`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx:141`, `:166`, `:236`
- Modify: `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx:104`
- Modify: `frontend/src/features/asesorias/screens/MisMaterias.tsx:74-76`, `:88`
- Modify: `frontend/src/features/asesorias/screens/MiHorario.tsx:238`

**Nota:** en `MisMaterias.tsx` y `MiHorario.tsx` el cambio **retira** la utilidad `hover:bg-surface-container-high`: el hover ahora lo da `.fila-interactiva`, con transición y gateado bajo `@media (hover: hover) and (pointer: fine)` (ADR 0026). No dejes la utilidad y la clase juntas: la utilidad de Tailwind no está gateada y duplicaría la regla.

- [ ] **Step 1: Línea base verde antes de tocar nada**

Run: `npx vitest run src/features/asesorias`
Expected: PASS. Si algo está rojo aquí, para y repórtalo: no es culpa de esta task.

- [ ] **Step 2: `TarjetaAsesoria.tsx`**

Reemplazar este par de líneas (son el ancla único: el mismo `className` aparece también en la variante `<div>` de abajo, que **no** se toca):

```tsx
          onClick={irAlDetalle}
          className={`foco-visible ${clasesBase}`}
```

por:

```tsx
          onClick={irAlDetalle}
          className={`fila-interactiva foco-visible ${clasesBase}`}
```

- [ ] **Step 3: `AgendarAsesoria.tsx` — las tres filas**

Reemplazar (línea 141, con **20** espacios de indentación):

```tsx
                    className="foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
```

por:

```tsx
                    className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
```

Reemplazar (línea 166, con **18** espacios de indentación):

```tsx
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
```

por:

```tsx
                  className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
```

Reemplazar (línea 236, dentro de `BotonAsesor`):

```tsx
      className="foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg bg-surface-container px-4 py-3 text-left"
```

por:

```tsx
      className="fila-interactiva foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg bg-surface-container px-4 py-3 text-left"
```

- [ ] **Step 4: `OfertaAsesorias.tsx`**

Reemplazar:

```tsx
                className="foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
```

por:

```tsx
                className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-lg bg-surface-container px-4 py-3 text-left"
```

- [ ] **Step 5: `MisMaterias.tsx` — la fila de materia y el botón de quitar**

Reemplazar:

```tsx
              className={`foco-visible min-h-11 min-w-0 flex-1 rounded-md px-2 py-2 text-left text-sm text-on-surface ${
                expandida === id ? '' : 'truncate'
              }`}
```

por:

```tsx
              className={`fila-interactiva foco-visible min-h-11 min-w-0 flex-1 rounded-md px-2 py-2 text-left text-sm text-on-surface ${
                expandida === id ? '' : 'truncate'
              }`}
```

Y reemplazar:

```tsx
                className="foco-visible flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-high"
```

por:

```tsx
                className="fila-interactiva foco-visible flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-on-surface-variant"
```

- [ ] **Step 6: `MiHorario.tsx`**

Reemplazar:

```tsx
                        className="foco-visible flex min-h-11 w-full items-center gap-2 border-b border-outline-variant px-2 text-sm text-on-surface hover:bg-surface-container-high"
```

por:

```tsx
                        className="fila-interactiva foco-visible flex min-h-11 w-full items-center gap-2 border-b border-outline-variant px-2 text-sm text-on-surface"
```

- [ ] **Step 7: Verificar que los tests siguen verdes y que no quedan hovers inline en estos archivos**

Run: `npx vitest run src/features/asesorias`
Expected: PASS — los mismos casos del Step 1, sin haber modificado ningún `.test.tsx`.

Run: `grep -n "hover:bg-surface-container-high" src/features/asesorias/screens/MisMaterias.tsx src/features/asesorias/screens/MiHorario.tsx`
Expected: sin resultados (exit code 1).

- [ ] **Step 8: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/features/asesorias/components/TarjetaAsesoria.tsx frontend/src/features/asesorias/screens/AgendarAsesoria.tsx frontend/src/features/asesorias/screens/OfertaAsesorias.tsx frontend/src/features/asesorias/screens/MisMaterias.tsx frontend/src/features/asesorias/screens/MiHorario.tsx
git commit -m "[feat][frontend] press feedback en las filas de asesorias de alumno y asesor

- .fila-interactiva en las 8 filas y tarjetas clicables de ancho completo
- MisMaterias y MiHorario dejan de usar hover:bg-surface-container-high inline
- el hover ahora va gateado bajo (hover: hover) and (pointer: fine), con transicion

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 5: `.fila-interactiva` en las filas del área SAE y del diálogo (A3 + A4, parte 2 de 2)

**Depends on:** Task 1 (`.fila-interactiva`).

**Files:**
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorias.tsx:114`, `:168`
- Modify: `frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx:130-132`
- Modify: `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx:71-75`

**Nota (decisión de alcance 7):** en los dos controles con estado "seleccionado" la clase entra **sólo en la rama no seleccionada**. `.fila-interactiva:hover` gana en especificidad a `bg-primary-container` y borraría el resaltado del ítem elegido.

- [ ] **Step 1: `AdminAsesorias.tsx` — las dos listas de resultados**

Las dos ocurrencias son **idénticas** (misma indentación de 18 espacios): usa un reemplazo global (`replace_all`).

Reemplazar:

```tsx
                  className="foco-visible flex min-h-11 w-full items-center justify-between rounded-md bg-surface-container px-3 text-left text-sm text-on-surface"
```

por:

```tsx
                  className="fila-interactiva foco-visible flex min-h-11 w-full items-center justify-between rounded-md bg-surface-container px-3 text-left text-sm text-on-surface"
```

Verificación puntual: `grep -c "fila-interactiva" src/features/asesorias/screens/AdminAsesorias.tsx` debe dar `2`.

- [ ] **Step 2: `AdminOfertaMateria.tsx`**

Reemplazar:

```tsx
      className={`foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg px-4 py-3 text-left ${
        seleccionado ? 'bg-primary-container text-on-primary-container' : 'bg-surface-container'
      }`}
```

por:

```tsx
      className={`foco-visible flex min-h-11 w-full flex-col items-start gap-0.5 rounded-lg px-4 py-3 text-left ${
        seleccionado
          ? 'bg-primary-container text-on-primary-container'
          : 'fila-interactiva bg-surface-container'
      }`}
```

- [ ] **Step 3: `DialogoAgregarMateria.tsx`**

Reemplazar:

```tsx
                className={`foco-visible min-h-11 w-full rounded-md px-2 py-2 text-left text-sm ${
                  seleccionada === materia.id
                    ? 'bg-primary-container text-on-primary-container'
                    : 'text-on-surface hover:bg-surface-container-high'
                }`}
```

por:

```tsx
                className={`foco-visible min-h-11 w-full rounded-md px-2 py-2 text-left text-sm ${
                  seleccionada === materia.id
                    ? 'bg-primary-container text-on-primary-container'
                    : 'fila-interactiva text-on-surface'
                }`}
```

- [ ] **Step 4: Verificar**

Run: `npx vitest run src/features/asesorias`
Expected: PASS, sin modificar ningún `.test.tsx`.

Run: `grep -rn "hover:bg-surface-container-high" src/`
Expected: sin resultados (exit code 1) — los tres usos inline que enumeraba ADR 0026 ya migraron (dos en la Task 4, uno aquí).

- [ ] **Step 5: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminAsesorias.tsx frontend/src/features/asesorias/screens/AdminOfertaMateria.tsx frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx
git commit -m "[feat][frontend] press feedback en las filas del area SAE y del dialogo de materias

- .fila-interactiva en los resultados de busqueda de asesor y alumno
- en los controles con estado seleccionado la clase va solo en la rama no seleccionada
- DialogoAgregarMateria deja de usar hover:bg-surface-container-high inline
- ya no queda ningun hover inline sin gatear en src/

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 6: Salida animada del toast (B1)

**Depends on:** Task 1 (`.salida-toast`).

**Files:**
- Modify: `frontend/src/components/ui/Retroalimentacion.tsx` (reescritura completa)
- Create: `frontend/src/components/ui/Retroalimentacion.test.tsx`
- Modify: `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx:17,56`
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx:106,162,246`
- Modify: `frontend/src/features/asesorias/screens/MisMaterias.tsx:28,172`
- Modify: `frontend/src/features/asesorias/screens/MiHorario.tsx:101,310`

**Interfaces:**
- Produces: `useRetroalimentacion(): { mensaje: Mensaje | null; saliendo: boolean; mostrar: (texto: string, tipo?: TipoMensaje) => void }` y `Retroalimentacion({ mensaje, saliendo }: { mensaje: Mensaje | null; saliendo: boolean })`. **`saliendo` es un prop obligatorio**: así, cualquier consumidor que no se actualice rompe `npm run build` en vez de degradarse en silencio. Hay exactamente 5 render sites en 4 archivos.

**Qué SÍ se testea:** que el toast aparece con `.entrada-lista`, que a los 2700 ms cambia a `.salida-toast` sin desmontarse, y que a los 2900 ms ya no está en el DOM. **Qué NO se testea:** que la animación CSS de salida dure realmente 200 ms.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/components/ui/Retroalimentacion.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { Retroalimentacion, useRetroalimentacion } from './Retroalimentacion'

/** Arnés mínimo: el hook y el componente sólo tienen sentido juntos. */
function Arnes() {
  const { mensaje, saliendo, mostrar } = useRetroalimentacion()
  return (
    <>
      <button type="button" onClick={() => mostrar('Materia agregada')}>
        disparar
      </button>
      <Retroalimentacion mensaje={mensaje} saliendo={saliendo} />
    </>
  )
}

describe('Retroalimentacion', () => {
  afterEach(() => vi.useRealTimers())

  it('entra, marca su salida y termina desmontado', () => {
    vi.useFakeTimers()
    render(<Arnes />)

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    const toast = screen.getByRole('status')
    expect(toast).toHaveTextContent('Materia agregada')
    expect(toast).toHaveClass('entrada-lista')

    // A los 2700 ms el toast sigue montado, ya con la clase de salida: es lo
    // observable del cierre en dos tiempos. La duración visual de la
    // animación CSS no se testea.
    act(() => {
      vi.advanceTimersByTime(2700)
    })
    expect(screen.getByRole('status')).toHaveClass('salida-toast')

    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('un mensaje nuevo cancela el estado de salida del anterior', () => {
    vi.useFakeTimers()
    render(<Arnes />)

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))
    act(() => {
      vi.advanceTimersByTime(2700)
    })
    expect(screen.getByRole('status')).toHaveClass('salida-toast')

    fireEvent.click(screen.getByRole('button', { name: 'disparar' }))

    expect(screen.getByRole('status')).toHaveClass('entrada-lista')
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `npx vitest run src/components/ui/Retroalimentacion.test.tsx`
Expected: FAIL — el hook todavía no devuelve `saliendo` y el componente no acepta ese prop (error de tipo en tiempo de test, o `toHaveClass('salida-toast')` sin cumplirse).

- [ ] **Step 3: Reescribir `Retroalimentacion.tsx`**

Reemplazar el contenido completo de `frontend/src/components/ui/Retroalimentacion.tsx` por:

```tsx
import { useCallback, useState } from 'react'

type TipoMensaje = 'exito' | 'error'
interface Mensaje {
  texto: string
  tipo: TipoMensaje
}

/** Debe coincidir con la duración de `.salida-toast` en `index.css`. */
const SALIDA_MS = 200
/** Tiempo con el toast completamente visible antes de empezar a salir. */
const VISIBLE_MS = 2700

export function useRetroalimentacion() {
  const [mensaje, setMensaje] = useState<Mensaje | null>(null)
  const [saliendo, setSaliendo] = useState(false)

  const mostrar = useCallback((texto: string, tipo: TipoMensaje = 'exito') => {
    // Cierre en dos tiempos: primero se marca la salida (que aplica
    // `.salida-toast`), y sólo cuando esa animación terminó se desmonta. Antes
    // el toast desaparecía de golpe al limpiar `mensaje`.
    setSaliendo(false)
    setMensaje({ texto, tipo })
    setTimeout(() => setSaliendo(true), VISIBLE_MS)
    setTimeout(() => {
      setMensaje(null)
      setSaliendo(false)
    }, VISIBLE_MS + SALIDA_MS)
  }, [])

  return { mensaje, saliendo, mostrar }
}

export function Retroalimentacion({
  mensaje,
  saliendo,
}: {
  mensaje: Mensaje | null
  saliendo: boolean
}) {
  if (!mensaje) return null
  const color = mensaje.tipo === 'exito' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-error-container text-on-error-container'
  return (
    <div
      role="status"
      className={`${saliendo ? 'salida-toast' : 'entrada-lista'} fixed inset-x-0 bottom-6 mx-auto w-fit rounded-full px-4 py-2 text-sm font-medium shadow-lg ${color}`}
    >
      {mensaje.texto}
    </div>
  )
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/components/ui/Retroalimentacion.test.tsx`
Expected: PASS (2 casos). Si falla con un warning de `act(...)`, la causa más probable es haber omitido el `act()` alrededor de `vi.advanceTimersByTime`.

- [ ] **Step 5: Actualizar los 4 consumidores**

En **cada uno** de estos archivos, reemplazar:

```tsx
  const { mensaje, mostrar } = useRetroalimentacion()
```

por:

```tsx
  const { mensaje, saliendo, mostrar } = useRetroalimentacion()
```

- `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx`
- `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`
- `frontend/src/features/asesorias/screens/MisMaterias.tsx`
- `frontend/src/features/asesorias/screens/MiHorario.tsx`

Y en los **5 render sites** reemplazar `<Retroalimentacion mensaje={mensaje} />` por `<Retroalimentacion mensaje={mensaje} saliendo={saliendo} />`, respetando la indentación de cada uno:

| Archivo | Indentación |
|---|---|
| `SinRegistroAsesor.tsx:56` | 6 espacios |
| `DetalleAsesoria.tsx:162` | 8 espacios |
| `DetalleAsesoria.tsx:246` | 6 espacios |
| `MisMaterias.tsx:172` | 6 espacios |
| `MiHorario.tsx:310` | 6 espacios |

- [ ] **Step 6: Verificar que no quedó ningún consumidor sin migrar**

Run: `grep -rn "<Retroalimentacion mensaje={mensaje} />" src/`
Expected: sin resultados (exit code 1).

Run: `npm run build`
Expected: PASS. Si falla con `Property 'saliendo' is missing`, quedó un render site sin actualizar. Si falla con `'saliendo' is declared but its value is never read`, un archivo desestructuró `saliendo` pero no lo pasó al componente.

- [ ] **Step 7: Suite + lint**

Run: `npm test && npm run lint`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/ui/Retroalimentacion.tsx frontend/src/components/ui/Retroalimentacion.test.tsx frontend/src/features/asesorias/components/SinRegistroAsesor.tsx frontend/src/features/asesorias/screens/DetalleAsesoria.tsx frontend/src/features/asesorias/screens/MisMaterias.tsx frontend/src/features/asesorias/screens/MiHorario.tsx
git commit -m "[feat][frontend] salida animada del toast de retroalimentacion

- el hook expone saliendo: marca la salida a los 2700ms y desmonta a los 2900ms
- el toast aplica .salida-toast en esa ventana en vez de desaparecer de golpe
- saliendo es prop obligatorio: los 5 render sites se actualizan en el mismo commit
- test: fases entrada / salida / desmontaje con timers falsos

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 7: Salida animada del dropdown de usuario (B2)

**Depends on:** Task 1 (`.entrada-menu`, `.salida-menu`).

**Files:**
- Modify: `frontend/src/components/MenuUsuario.tsx`
- Modify: `frontend/src/components/MenuUsuario.test.tsx` (2 casos adaptados + 1 nuevo)

**Nota crítica (decisión de alcance 2):** el state `cerrando` que ya existe en `MenuUsuario.tsx:18` **está en uso** — es el guard de doble disparo del cierre de sesión (`disabled={cerrando}`). Esta task introduce un state **nuevo**, `cerrandoMenu`, y no toca `cerrando` ni `cerrarSesion`.

**Qué SÍ se testea:** que tras pedir el cierre el panel sigue montado con `.salida-menu`, y que tras avanzar 140 ms ya no está. **Qué NO se testea:** la duración visual real de la animación.

- [ ] **Step 1: Adaptar los tests existentes y añadir el nuevo**

En `frontend/src/components/MenuUsuario.test.tsx`, reemplazar la línea 2:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
```

por:

```tsx
import { render, screen, fireEvent, act } from '@testing-library/react'
```

Reemplazar:

```tsx
  afterEach(() => vi.restoreAllMocks())
```

por:

```tsx
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  /** El panel se desmonta cuando termina `.salida-menu` (140 ms). */
  function terminarSalida() {
    act(() => {
      vi.advanceTimersByTime(140)
    })
  }
```

Reemplazar el caso de Escape completo:

```tsx
  it('Escape lo cierra y devuelve el foco al disparador', () => {
    montar()
    abrir()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
    expect(disparador()).toHaveFocus()
  })
```

por:

```tsx
  it('Escape lo cierra y devuelve el foco al disparador', () => {
    vi.useFakeTimers()
    montar()
    abrir()
    fireEvent.keyDown(document, { key: 'Escape' })

    // El foco vuelve de inmediato; el panel espera a que corra su salida.
    expect(disparador()).toHaveFocus()
    terminarSalida()

    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })

  it('el panel sigue montado mientras corre la animación de salida', () => {
    vi.useFakeTimers()
    montar()
    abrir()
    fireEvent.keyDown(document, { key: 'Escape' })

    const panel = screen.getByRole('button', { name: 'Cerrar sesión' }).parentElement
    expect(panel).toHaveClass('salida-menu')
    expect(panel).not.toHaveClass('entrada-menu')

    terminarSalida()

    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })
```

Reemplazar el caso de click fuera:

```tsx
  it('un click fuera lo cierra', () => {
    montar()
    abrir()
    fireEvent.mouseDown(document.body)
    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })
```

por:

```tsx
  it('un click fuera lo cierra', () => {
    vi.useFakeTimers()
    montar()
    abrir()
    fireEvent.mouseDown(document.body)
    terminarSalida()

    expect(screen.queryByRole('button', { name: 'Cerrar sesión' })).not.toBeInTheDocument()
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx`
Expected: FAIL en el caso nuevo (`salida-menu` no existe: el panel todavía usa `.entrada-dialogo`). Los dos adaptados **pasan igual** por ahora, porque hoy el cierre es inmediato y avanzar timers no cambia nada.

- [ ] **Step 3: Implementar el cierre en dos tiempos**

En `frontend/src/components/MenuUsuario.tsx`:

**(a)** Reemplazar:

```tsx
import { useAuth } from '../auth/AuthContext'
```

por:

```tsx
import { useAuth } from '../auth/AuthContext'

/** Debe coincidir con la duración de `.salida-menu` en `index.css`. */
const SALIDA_MENU_MS = 140
```

**(b)** Reemplazar:

```tsx
  const [cerrando, setCerrando] = useState(false)
```

por:

```tsx
  // `cerrando` es el guard de doble disparo del logout; `cerrandoMenu` es otra
  // cosa: la fase de salida del panel, que lo mantiene montado 140 ms para que
  // corra `.salida-menu` antes de desmontarlo.
  const [cerrando, setCerrando] = useState(false)
  const [cerrandoMenu, setCerrandoMenu] = useState(false)
```

**(c)** Insertar la función de cierre justo **antes** del `useEffect`. Reemplazar:

```tsx
  useEffect(() => {
    if (!abierto) return
```

por:

```tsx
  function cerrarMenu() {
    if (cerrandoMenu) return
    setCerrandoMenu(true)
    setTimeout(() => {
      setCerrandoMenu(false)
      setAbierto(false)
    }, SALIDA_MENU_MS)
  }

  useEffect(() => {
    if (!abierto) return
```

**(d)** Reemplazar el handler de Escape:

```tsx
    function alPresionarTecla(evento: KeyboardEvent) {
      if (evento.key !== 'Escape') return
      setAbierto(false)
      // Escape devuelve el foco al disparador; un click fuera no, porque el
      // foco ya se fue a donde el usuario apuntó.
      disparadorRef.current?.focus()
    }
```

por:

```tsx
    function alPresionarTecla(evento: KeyboardEvent) {
      if (evento.key !== 'Escape') return
      cerrarMenu()
      // Escape devuelve el foco al disparador; un click fuera no, porque el
      // foco ya se fue a donde el usuario apuntó.
      disparadorRef.current?.focus()
    }
```

**(e)** Reemplazar el handler de click fuera:

```tsx
    function alApuntarFuera(evento: MouseEvent) {
      if (contenedorRef.current?.contains(evento.target as Node) === true) return
      setAbierto(false)
    }
```

por:

```tsx
    function alApuntarFuera(evento: MouseEvent) {
      if (contenedorRef.current?.contains(evento.target as Node) === true) return
      cerrarMenu()
    }
```

**(f)** Reemplazar la lista de dependencias del efecto (para que el guard `if (cerrandoMenu) return` vea el valor vigente):

```tsx
  }, [abierto])
```

por:

```tsx
  }, [abierto, cerrandoMenu])
```

**(g)** Reemplazar el `onClick` del disparador:

```tsx
        onClick={() => setAbierto((previo) => !previo)}
```

por:

```tsx
        onClick={() => (abierto ? cerrarMenu() : setAbierto(true))}
```

**(h)** Reemplazar el `className` del panel:

```tsx
          className="entrada-dialogo absolute right-0 top-12 z-10 flex w-60 flex-col gap-1 rounded-2xl bg-surface-container p-3 text-left shadow-lg"
```

por:

```tsx
          className={`${cerrandoMenu ? 'salida-menu' : 'entrada-menu'} absolute right-0 top-12 z-10 flex w-60 flex-col gap-1 rounded-2xl bg-surface-container p-3 text-left shadow-lg`}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/MenuUsuario.test.tsx`
Expected: PASS (7 casos: los 6 previos, dos de ellos adaptados, más el nuevo). Si falla `toHaveClass('salida-menu')` con `null`, la causa más probable es que `.parentElement` del botón "Cerrar sesión" no sea el panel — verifica que el `<div id={idPanel}>` sigue siendo el padre directo.

- [ ] **Step 5: Verificar que `.entrada-dialogo` ya no se usa en el menú**

Run: `grep -n "entrada-dialogo" src/components/MenuUsuario.tsx`
Expected: sin resultados (exit code 1). Esa clase estaba diseñada para un elemento centrado en viewport (`translate(-50%,-50%)`) y el panel está anclado al disparador.

- [ ] **Step 6: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/MenuUsuario.tsx frontend/src/components/MenuUsuario.test.tsx
git commit -m "[feat][frontend] salida animada del dropdown de usuario

- state cerrandoMenu nuevo: mantiene el panel montado 140ms para .salida-menu
- las tres rutas de cierre (toggle, Escape, click fuera) pasan por cerrarMenu()
- el panel deja de usar .entrada-dialogo, pensada para elementos centrados, y
  usa .entrada-menu/.salida-menu con transform-origin: top right
- tests: fase de salida observable y desmontaje tras avanzar los timers

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 8: Salida animada del diálogo modal (B3)

**Depends on:** Task 1 (`.salida-dialogo`, `.salida-velo`).

**Files:**
- Modify: `frontend/src/components/ui/dialog.tsx`
- Modify: `frontend/src/components/ui/dialog.test.tsx` (1 caso adaptado)
- Modify: `frontend/src/components/ui/Dialogo.test.tsx` (1 caso partido en 2)

**Interfaces:**
- `Dialog` conserva su firma pública (`React.ComponentProps<typeof DialogPrimitive.Root>`). Cambia su comportamiento observable: `onOpenChange(false)` ya **no** se propaga de inmediato — se difiere 150 ms mientras corren `.salida-dialogo`/`.salida-velo`. `onOpenChange(true)` se propaga sin cambio.
- Un `React.createContext` interno (no exportado) comunica la fase de cierre a `DialogContent` y `DialogOverlay`.

**Qué SÍ se testea:** que `onOpenChange` no se llama al instante, que el contenido sigue montado con `.salida-dialogo`, y que tras avanzar 150 ms el callback sí se invoca con `false`. **Qué NO se testea:** la duración visual de la animación.

- [ ] **Step 1: Adaptar `dialog.test.tsx`**

Reemplazar la línea 2:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
```

por:

```tsx
import { render, screen, fireEvent, act } from '@testing-library/react'
```

Reemplazar:

```tsx
describe('dialog', () => {
  it('expone el contenido como diálogo con nombre accesible tomado del título', () => {
```

por:

```tsx
describe('dialog', () => {
  afterEach(() => vi.useRealTimers())

  it('expone el contenido como diálogo con nombre accesible tomado del título', () => {
```

Reemplazar la línea 1:

```tsx
import { describe, it, expect, vi } from 'vitest'
```

por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
```

Y reemplazar el caso de Escape completo:

```tsx
  it('cierra con Escape sin que el componente intercepte el teclado', () => {
    const onOpenChange = abrirDialogo()

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
```

por:

```tsx
  it('cierra con Escape, propagando el cierre cuando termina la salida', () => {
    vi.useFakeTimers()
    const onOpenChange = abrirDialogo()

    fireEvent.keyDown(document, { key: 'Escape' })

    // El cierre no se propaga de inmediato: el contenido sigue montado con la
    // clase de salida. La duración visual de la animación no se testea.
    expect(onOpenChange).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog', { name: 'Título de prueba' })).toHaveClass('salida-dialogo')

    act(() => {
      vi.advanceTimersByTime(150)
    })

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
```

- [ ] **Step 2: Adaptar `Dialogo.test.tsx`**

Reemplazar la línea 1:

```tsx
import { describe, it, expect, vi } from 'vitest'
```

por:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
```

Reemplazar la línea 2:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
```

por:

```tsx
import { render, screen, fireEvent, act } from '@testing-library/react'
```

Y reemplazar el caso de cierre completo:

```tsx
describe('Dialogo — comportamiento', () => {
  it('cerrar con Escape o con el botón de salir llama a onCerrar', () => {
    const onCerrar = vi.fn()
    render(<Dialogo abierto titulo="Salir" onCerrar={onCerrar} acciones={[]} etiquetaSalir="Cerrar" />)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onCerrar).toHaveBeenCalledTimes(2)
  })
```

por:

```tsx
describe('Dialogo — comportamiento', () => {
  afterEach(() => vi.useRealTimers())

  it('el botón de salir llama a onCerrar de inmediato', () => {
    const onCerrar = vi.fn()
    render(<Dialogo abierto titulo="Salir" onCerrar={onCerrar} acciones={[]} etiquetaSalir="Cerrar" />)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))

    // El botón invoca `onCerrar` directo, sin pasar por Radix: no hay salida
    // que esperar. Escape sí pasa por Radix, y ese camino se prueba abajo.
    expect(onCerrar).toHaveBeenCalledTimes(1)
  })

  it('Escape llama a onCerrar cuando termina la animación de salida', () => {
    vi.useFakeTimers()
    const onCerrar = vi.fn()
    render(<Dialogo abierto titulo="Salir" onCerrar={onCerrar} acciones={[]} etiquetaSalir="Cerrar" />)

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onCerrar).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(150)
    })

    expect(onCerrar).toHaveBeenCalledTimes(1)
  })
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `npx vitest run src/components/ui/dialog.test.tsx src/components/ui/Dialogo.test.tsx`
Expected: FAIL en los casos nuevos de Escape de ambos archivos — hoy `onOpenChange`/`onCerrar` se invocan de inmediato y la clase es `entrada-dialogo`, no `salida-dialogo`. El resto de los casos pasa.

- [ ] **Step 4: Implementar la interceptación en `dialog.tsx`**

**(a)** Reemplazar:

```tsx
function Dialog({ ...props }: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />
}
```

por:

```tsx
/** Debe coincidir con la duración de `.salida-dialogo`/`.salida-velo` en `index.css`. */
const SALIDA_DIALOGO_MS = 150

/**
 * Fase de cierre, de `Dialog` a `Content`/`Overlay`. Radix desmonta ambos en
 * cuanto `open` pasa a false, así que la salida se anima interceptando
 * `onOpenChange(false)`: se marca `cerrando`, corren las clases de salida
 * durante SALIDA_DIALOGO_MS, y sólo entonces se invoca el `onOpenChange(false)`
 * real que el consumidor pasó por props.
 */
const ContextoCerrando = React.createContext(false)

function Dialog({ onOpenChange, ...props }: React.ComponentProps<typeof DialogPrimitive.Root>) {
  const [cerrando, setCerrando] = React.useState(false)

  function alCambiarApertura(abierto: boolean) {
    if (abierto) {
      onOpenChange?.(true)
      return
    }
    setCerrando(true)
    setTimeout(() => {
      setCerrando(false)
      onOpenChange?.(false)
    }, SALIDA_DIALOGO_MS)
  }

  return (
    <ContextoCerrando.Provider value={cerrando}>
      <DialogPrimitive.Root data-slot="dialog" onOpenChange={alCambiarApertura} {...props} />
    </ContextoCerrando.Provider>
  )
}
```

**(b)** Reemplazar `DialogOverlay` completo:

```tsx
function DialogOverlay({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      data-slot="dialog-overlay"
      className={cn('entrada-velo fixed inset-0 z-50 bg-scrim/50', className)}
      {...props}
    />
  )
}
```

por:

```tsx
function DialogOverlay({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  const cerrando = React.useContext(ContextoCerrando)
  return (
    <DialogPrimitive.Overlay
      data-slot="dialog-overlay"
      className={cn(cerrando ? 'salida-velo' : 'entrada-velo', 'fixed inset-0 z-50 bg-scrim/50', className)}
      {...props}
    />
  )
}
```

**(c)** Reemplazar la firma y el `className` de `DialogContent`:

```tsx
function DialogContent({ className, children, ...props }: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          'entrada-dialogo fixed left-1/2 top-1/2 z-50 flex max-h-[calc(100svh-2rem)] w-[calc(100%-2rem)] max-w-sm',
```

por:

```tsx
function DialogContent({ className, children, ...props }: React.ComponentProps<typeof DialogPrimitive.Content>) {
  const cerrando = React.useContext(ContextoCerrando)
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          cerrando ? 'salida-dialogo' : 'entrada-dialogo',
          'fixed left-1/2 top-1/2 z-50 flex max-h-[calc(100svh-2rem)] w-[calc(100%-2rem)] max-w-sm',
```

**(d)** Actualizar el comentario de cabecera del archivo. Reemplazar:

```tsx
 * - Sin `tw-animate-css`: la animación de entrada usa las clases
 *   `.entrada-dialogo`/`.entrada-velo` de `index.css`, que sí están
 *   registradas en el bloque de `prefers-reduced-motion` (paso 7).
```

por:

```tsx
 * - Sin `tw-animate-css`: la animación de entrada usa las clases
 *   `.entrada-dialogo`/`.entrada-velo` de `index.css`, y la de salida
 *   `.salida-dialogo`/`.salida-velo`; las cuatro están registradas en el
 *   bloque de `prefers-reduced-motion`.
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/ui/dialog.test.tsx src/components/ui/Dialogo.test.tsx`
Expected: PASS (3 casos en `dialog`, los de `Dialogo` con uno partido en dos). Si falla con `onOpenChange` invocado dos veces, la causa más probable es haber dejado `onOpenChange` dentro de `{...props}` (debe estar destructurado fuera, para que el spread no lo reintroduzca).

- [ ] **Step 6: Suite + build + lint**

Run: `npm test && npm run build && npm run lint`
Expected: PASS. Los diálogos de features (`DialogoCancelar`, `DialogoNuevoBloque`, `DialogoBloqueActivo`, `DialogoDesactivarConSesiones`, `DialogoAgregarMateria`) cierran llamando a su `onCerrar`/`onConfirmar` directo, no por Radix, así que sus tests no cambian. Si alguno falla, revisa si dispara `Escape` o un click en el velo.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ui/dialog.tsx frontend/src/components/ui/dialog.test.tsx frontend/src/components/ui/Dialogo.test.tsx
git commit -m "[feat][frontend] salida animada del dialogo modal

- Dialog intercepta onOpenChange(false) y lo difiere 150ms
- Content y Overlay leen la fase de cierre por contexto y aplican
  .salida-dialogo/.salida-velo en vez de desmontarse de golpe
- tests: el cierre por Escape se observa en dos fases, sin asertar duraciones

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 9: Transición de entrada en los mensajes de error (C1)

**Depends on:** Task 1 (no estrictamente — usa `.entrada-lista`, que ya existía — pero se mantiene el orden para no adelantar commits).

**Files:**
- Modify: `frontend/src/screens/Login.tsx:103`
- Modify: `frontend/src/screens/Landing.tsx:51`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx:106`
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx:159`, `:215`

Ninguna clase nueva: se antepone la `.entrada-lista` existente (300 ms, sin `animationDelay`). **`Dialogo.tsx:106` queda fuera** (decisión de alcance 8).

- [ ] **Step 1: `Login.tsx`**

Reemplazar:

```tsx
          <p role="alert" className="text-sm text-error">
```

por:

```tsx
          <p role="alert" className="entrada-lista text-sm text-error">
```

- [ ] **Step 2: `Landing.tsx`**

Reemplazar:

```tsx
          <p role="alert" className="text-center text-sm text-error">
```

por:

```tsx
          <p role="alert" className="entrada-lista text-center text-sm text-error">
```

- [ ] **Step 3: `AgendarAsesoria.tsx`**

Reemplazar (6 espacios de indentación):

```tsx
      {error && <p role="alert" className="text-xs text-error">{error}</p>}
```

por:

```tsx
      {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}
```

- [ ] **Step 4: `DetalleAsesoria.tsx` — las dos ocurrencias**

Tienen **indentación distinta**, así que son dos reemplazos separados (no uses `replace_all`).

Reemplazar (línea 159, **12** espacios):

```tsx
            {error && <p role="alert" className="text-xs text-error">{error}</p>}
```

por:

```tsx
            {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}
```

Reemplazar (línea 215, **10** espacios):

```tsx
          {error && <p role="alert" className="text-xs text-error">{error}</p>}
```

por:

```tsx
          {error && <p role="alert" className="entrada-lista text-xs text-error">{error}</p>}
```

- [ ] **Step 5: Verificar**

Run: `grep -rn 'role="alert"' src/screens/ src/features/ | grep -v "entrada-lista"`
Expected: sin resultados (exit code 1). Los 5 sitios del spec quedan cubiertos; `Dialogo.tsx` no aparece porque el grep se limita a `screens/` y `features/`.

Run: `npm test && npm run build && npm run lint`
Expected: PASS. Los tests que buscan `screen.findByRole('alert')` no dependen del `className`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/screens/Login.tsx frontend/src/screens/Landing.tsx frontend/src/features/asesorias/screens/AgendarAsesoria.tsx frontend/src/features/asesorias/screens/DetalleAsesoria.tsx
git commit -m "[feat][frontend] los mensajes de error entran con transicion

- los 5 <p role=alert> de Login, Landing, AgendarAsesoria y DetalleAsesoria
  llevan la clase .entrada-lista ya existente, sin animationDelay
- ninguna clase ni token nuevos

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 10: Suavizar el swap skeleton → contenido en `AdminAsesorDetalle` (C2)

**Depends on:** Task 1 (orden; usa `.entrada-lista` existente).

**Files:**
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx:50`, `:90-98`

**Nota (decisión de alcance 6):** de los seis sitios que lista C2, éste es el único descubierto. `Asesorias.tsx:148` y `AdminAsesores.tsx:45` ya entran con `.entrada-lista`; `OfertaAsesorias.tsx:87` y `MiHorario.tsx:219` quedan cubiertos por el stagger de las Tasks 11 y 12. No los toques.

- [ ] **Step 1: El bloque de identidad del asesor**

Reemplazar:

```tsx
        <div className="flex items-start justify-between gap-3">
```

por:

```tsx
        <div className="entrada-lista flex items-start justify-between gap-3">
```

- [ ] **Step 2: El bloque de materias + horario**

El fragmento `<>` no puede llevar `className`. Se sustituye por un `<div>` con el mismo `gap-4` que el `<main>` padre, de modo que la separación visual entre `MisMaterias` y `MiHorario` (y respecto al `<select>` de arriba) no cambia.

Reemplazar:

```tsx
        <>
          <MisMaterias
            soloLectura
            materias={detalle.materias}
            semestre={detalle.semestre}
          />

          <MiHorario soloLectura disponibilidades={detalle.disponibilidades} />
        </>
```

por:

```tsx
        <div className="entrada-lista flex flex-col gap-4">
          <MisMaterias
            soloLectura
            materias={detalle.materias}
            semestre={detalle.semestre}
          />

          <MiHorario soloLectura disponibilidades={detalle.disponibilidades} />
        </div>
```

- [ ] **Step 3: Verificar**

Run: `npx vitest run src/features/asesorias/screens/AdminAsesorDetalle.test.tsx`
Expected: PASS sin modificar el test. Si falla una consulta por estructura del DOM, es por el `<div>` nuevo del Step 2 — repórtalo antes de tocar el test.

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/asesorias/screens/AdminAsesorDetalle.tsx
git commit -m "[feat][frontend] suavizar el swap de skeleton a contenido en el detalle de asesor SAE

- los dos bloques que reemplazan a un Skeleton entran con .entrada-lista
- el fragmento del bloque de materias/horario pasa a div con el mismo gap-4
  del main, para poder llevar la clase sin cambiar el layout

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 11: Stagger de listas — Home, oferta, agendado y materias (C3, parte 1 de 2)

**Depends on:** Task 1 (orden; usa `.entrada-lista` existente).

**Files:**
- Modify: `frontend/src/screens/Home.tsx:34-37`
- Modify: `frontend/src/features/asesorias/screens/OfertaAsesorias.tsx:99-100`
- Modify: `frontend/src/features/asesorias/screens/AgendarAsesoria.tsx:117-118`, `:136-137`
- Modify: `frontend/src/features/asesorias/screens/MisMaterias.tsx:68-69`

Patrón exacto a replicar, tal cual está en `TarjetaAsesoria.tsx:82`: `className="entrada-lista"` + `style={{ animationDelay: \`${Math.min(indice, 10) * 30}ms\` }}`. Cada `.map()` necesita además el segundo parámetro `indice` en su callback.

- [ ] **Step 1: `Home.tsx` — grid de servicios**

Reemplazar:

```tsx
        {services.map(({ id, label, Icon, containerClassName, onContainerClassName }) => (
          <div
            key={id}
            className={`flex flex-col items-center gap-2 rounded-2xl p-3 text-center ${containerClassName} ${onContainerClassName}`}
          >
```

por:

```tsx
        {services.map(({ id, label, Icon, containerClassName, onContainerClassName }, indice) => (
          <div
            key={id}
            style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}
            className={`entrada-lista flex flex-col items-center gap-2 rounded-2xl p-3 text-center ${containerClassName} ${onContainerClassName}`}
          >
```

- [ ] **Step 2: `OfertaAsesorias.tsx`**

Reemplazar:

```tsx
          {filtradas.map((m) => (
            <li key={m.materia_id}>
```

por:

```tsx
          {filtradas.map((m, indice) => (
            <li key={m.materia_id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

- [ ] **Step 3: `AgendarAsesoria.tsx` — lista de asesores**

Reemplazar:

```tsx
              {asesores.map((a) => (
                <li key={a.registro_id}>
```

por:

```tsx
              {asesores.map((a, indice) => (
                <li key={a.registro_id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

- [ ] **Step 4: `AgendarAsesoria.tsx` — lista de días**

Reemplazar:

```tsx
              {dias.map((d) => (
                <li key={d.fecha}>
```

por:

```tsx
              {dias.map((d, indice) => (
                <li key={d.fecha} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

**Nota:** la tercera lista del wizard (`slotsDelDia.map`, paso "bloque") **no** está en el catálogo C3 del spec y no se toca.

- [ ] **Step 5: `MisMaterias.tsx`**

Reemplazar:

```tsx
        {materiasAMostrar.map(({ id, nombre }) => (
          <li key={id} className="flex items-center gap-2 border-b border-outline-variant">
```

por:

```tsx
        {materiasAMostrar.map(({ id, nombre }, indice) => (
          <li key={id} className="entrada-lista flex items-center gap-2 border-b border-outline-variant" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

- [ ] **Step 6: Verificar**

Run: `npx vitest run src/screens/Home.test.tsx src/features/asesorias`
Expected: PASS sin modificar ningún `.test.tsx`.

Run: `npm test && npm run build && npm run lint`
Expected: PASS. Si el build falla con `'indice' is declared but its value is never read`, quedó un `.map()` con el parámetro añadido pero sin el `animationDelay` que lo usa.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/screens/Home.tsx frontend/src/features/asesorias/screens/OfertaAsesorias.tsx frontend/src/features/asesorias/screens/AgendarAsesoria.tsx frontend/src/features/asesorias/screens/MisMaterias.tsx
git commit -m "[feat][frontend] entrada escalonada en las listas de Home, oferta, agendado y materias

- se replica el patron de TarjetaAsesoria: .entrada-lista + animationDelay
  de Math.min(indice, 10) * 30ms por item
- sin clases ni tokens nuevos

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 12: Stagger de listas — horario, área SAE, notas y diálogo (C3, parte 2 de 2)

**Depends on:** Task 1 (orden), Task 5 (toca `AdminAsesorias.tsx` y `DialogoAgregarMateria.tsx`, ya modificados ahí).

**Files:**
- Modify: `frontend/src/features/asesorias/screens/MiHorario.tsx:227-228`
- Modify: `frontend/src/features/asesorias/screens/AdminAsesorias.tsx:109-110`, `:163-164`
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx:90-91`
- Modify: `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx:65-66`

- [ ] **Step 1: `MiHorario.tsx` — lista de slots**

**El parámetro se llama `indiceSlot`, no `indice`** (decisión de alcance 10): ya hay un `indice` en el scope exterior que se usa dentro de este mismo callback (`tocarSlot(indice, …)`); sombrearlo rompe el horario.

Reemplazar:

```tsx
                {slots.map((slot) => (
                  <li key={slot.clave}>
```

por:

```tsx
                {slots.map((slot, indiceSlot) => (
                  <li key={slot.clave} className="entrada-lista" style={{ animationDelay: `${Math.min(indiceSlot, 10) * 30}ms` }}>
```

**No** toques `DIAS_CORTOS.map` (líneas 201 y 208): son la barra de pestañas y los paneles contenedores, no listas (decisión de alcance 5).

- [ ] **Step 2: `AdminAsesorias.tsx` — las dos listas de resultados**

Los dos bloques son **idénticos** (misma indentación): usa un reemplazo global (`replace_all`).

Reemplazar:

```tsx
            {resultados.map((a) => (
              <li key={a.perfil_id}>
```

por:

```tsx
            {resultados.map((a, indice) => (
              <li key={a.perfil_id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

Verificación puntual: `grep -c "entrada-lista" src/features/asesorias/screens/AdminAsesorias.tsx` debe dar `2`.

- [ ] **Step 3: `DetalleAsesoria.tsx` — notas de sesiones previas**

Reemplazar:

```tsx
            {previas.map((previa) => (
              <li key={previa.id} className="rounded-lg bg-surface-container-low p-3 text-sm">
```

por:

```tsx
            {previas.map((previa, indice) => (
              <li key={previa.id} className="entrada-lista rounded-lg bg-surface-container-low p-3 text-sm" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

- [ ] **Step 4: `DialogoAgregarMateria.tsx`**

Reemplazar:

```tsx
          {filtradas.map((materia) => (
            <li key={materia.id}>
```

por:

```tsx
          {filtradas.map((materia, indice) => (
            <li key={materia.id} className="entrada-lista" style={{ animationDelay: `${Math.min(indice, 10) * 30}ms` }}>
```

- [ ] **Step 5: Verificar**

Run: `npx vitest run src/features/asesorias`
Expected: PASS sin modificar ningún `.test.tsx`. Si `MiHorario.test.tsx` falla con horarios que se activan en el día equivocado, la causa es haber nombrado `indice` (y no `indiceSlot`) al parámetro del Step 1.

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/asesorias/screens/MiHorario.tsx frontend/src/features/asesorias/screens/AdminAsesorias.tsx frontend/src/features/asesorias/screens/DetalleAsesoria.tsx frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx
git commit -m "[feat][frontend] entrada escalonada en horario, resultados SAE, notas previas y dialogo

- mismo patron .entrada-lista + animationDelay escalonado de 30ms
- en MiHorario el indice del map interno se llama indiceSlot para no sombrear
  el indice del dia, que el callback ya usaba

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 13: Entrada de deleite en la pantalla 404 (D1)

**Depends on:** Task 1 (`.entrada-deleite`).

**Files:**
- Modify: `frontend/src/screens/NoEncontrado.tsx:15-23`

Cinco elementos, stagger de 70 ms: `0, 70, 140, 210, 280`. El primero no lleva `style` (delay 0) — conveniente además porque `Logo` sólo acepta `className`, no `style`.

- [ ] **Step 1: Aplicar la clase a los cinco elementos**

Reemplazar el bloque completo:

```tsx
      <Logo className="h-16 w-16 text-primary" />
      <p className="text-5xl font-semibold text-primary">404</p>
      <h1 className="text-lg font-semibold text-on-background">Página no encontrada</h1>
      <p className="max-w-[28ch] text-sm text-on-surface-variant">
        La dirección que abriste no existe o cambió de lugar.
      </p>
      <Boton type="button" onClick={() => navigate('/')} className="px-6">
        Volver al inicio
      </Boton>
```

por:

```tsx
      <Logo className="entrada-deleite h-16 w-16 text-primary" />
      <p className="entrada-deleite text-5xl font-semibold text-primary" style={{ animationDelay: '70ms' }}>404</p>
      <h1 className="entrada-deleite text-lg font-semibold text-on-background" style={{ animationDelay: '140ms' }}>
        Página no encontrada
      </h1>
      <p className="entrada-deleite max-w-[28ch] text-sm text-on-surface-variant" style={{ animationDelay: '210ms' }}>
        La dirección que abriste no existe o cambió de lugar.
      </p>
      <Boton type="button" onClick={() => navigate('/')} className="entrada-deleite px-6" style={{ animationDelay: '280ms' }}>
        Volver al inicio
      </Boton>
```

- [ ] **Step 2: Verificar**

Run: `npx vitest run src/screens/NoEncontrado.test.tsx`
Expected: PASS (3 casos) sin modificar el test. El heading pasa a estar en dos líneas de JSX, pero su texto accesible sigue siendo `Página no encontrada`. Si falla `getByRole('heading', { name: 'Página no encontrada' })`, revisa que no quedó espacio duplicado dentro del `<h1>`.

Run: `npm run build && npm run lint`
Expected: PASS. `Boton` extiende `ButtonHTMLAttributes`, así que acepta `style` sin cambios de tipos.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/screens/NoEncontrado.tsx
git commit -m "[feat][frontend] entrada escalonada de deleite en la pantalla 404

- los 5 elementos entran con .entrada-deleite y stagger de 70ms (0..280)
- unica superficie, junto con Landing, donde el presupuesto de duracion
  puede exceder 300ms segun ADR 0026

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Task 14: Entrada de deleite en la Landing (D2)

**Depends on:** Task 1 (`.entrada-deleite`), Task 9 (toca `Landing.tsx`).

**Files:**
- Modify: `frontend/src/screens/Landing.tsx:39-46`, `:49`

Mismo stagger de 70 ms. **Nota:** el spec describe D2 como "Logo → título → subtítulo → botones" (4 pasos), pero `Landing` tiene **dos** párrafos de subtítulo ("Secretaría de Asuntos Estudiantiles" y "Facultad de Ciencias, UNAM"). Se aplican 5 pasos (`0, 70, 140, 210, 280`), idéntico a D1: es la extensión literal del patrón, sin inventar valores.

- [ ] **Step 1: Logo, título y los dos subtítulos**

Reemplazar el bloque completo (los dos `<p>` tienen la misma etiqueta de apertura, por eso se reemplaza el bloque entero y no línea por línea):

```tsx
        <Logo className="h-20 w-20 text-primary" />
        <h1 className="text-2xl font-semibold">Atenea</h1>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Secretaría de Asuntos Estudiantiles
        </p>
        <p className="max-w-[26ch] text-sm text-on-surface-variant">
          Facultad de Ciencias, UNAM
        </p>
```

por:

```tsx
        <Logo className="entrada-deleite h-20 w-20 text-primary" />
        <h1 className="entrada-deleite text-2xl font-semibold" style={{ animationDelay: '70ms' }}>Atenea</h1>
        <p className="entrada-deleite max-w-[26ch] text-sm text-on-surface-variant" style={{ animationDelay: '140ms' }}>
          Secretaría de Asuntos Estudiantiles
        </p>
        <p className="entrada-deleite max-w-[26ch] text-sm text-on-surface-variant" style={{ animationDelay: '210ms' }}>
          Facultad de Ciencias, UNAM
        </p>
```

- [ ] **Step 2: El bloque de CTA**

Reemplazar:

```tsx
      <div className="flex w-full max-w-xs flex-col gap-3">
```

por:

```tsx
      <div className="entrada-deleite flex w-full max-w-xs flex-col gap-3" style={{ animationDelay: '280ms' }}>
```

- [ ] **Step 3: Verificar**

Run: `npx vitest run src/screens/Landing.test.tsx`
Expected: PASS sin modificar el test.

Run: `npm test && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/screens/Landing.tsx
git commit -m "[feat][frontend] entrada escalonada de deleite en la landing

- Logo, titulo, los dos subtitulos y el bloque de CTA entran con
  .entrada-deleite y stagger de 70ms (0..280)
- mismo tratamiento que la 404: son las dos superficies de tier rare/first-time

Signed-off-by: Héctor Olvera Vital <yogsototh@gmail.com>"
```

---

## Verificación final

- [ ] **Suite completa, build y lint desde `frontend/`**

Run: `npm test && npm run build && npm run lint`
Expected: PASS, sin tests saltados.

- [ ] **Ninguna curva de easing suelta fuera de `index.css`**

Run: `grep -rn "cubic-bezier" src/ --include=*.tsx --include=*.ts`
Expected: sin resultados (exit code 1). Todo el easing vive en las tres variables de `index.css`.

- [ ] **Ningún `hover:` sin gatear entre los tres usos que ADR 0026 mandó migrar**

Run: `grep -rn "hover:bg-surface-container-high" src/`
Expected: sin resultados (exit code 1).

- [ ] **Las ocho clases nuevas están en el bloque de `prefers-reduced-motion`**

Run: `sed -n '/prefers-reduced-motion/,$p' src/index.css`
Expected: el selector agrupado lista `.salida-toast`, `.entrada-menu`, `.salida-menu`, `.salida-dialogo`, `.salida-velo` y `.entrada-deleite` junto a las siete clases previas, y debajo existe la regla aparte de `transition-duration` para `.presionable` y `.fila-interactiva`.

- [ ] **Nada de lo rechazado por el spec se coló**

Run: `grep -rn "entrada-deleite\|salida-menu\|fila-interactiva\|presionable" src/App.tsx src/components/ui/tabs.tsx`
Expected: sin resultados (exit code 1). Ni transiciones de ruta SPA ni indicador deslizante de tabs.

- [ ] **Repaso manual** (con `npm run dev`):
  1. Presionar cualquier `Boton` (Login, diálogos, 404): se hunde ligeramente y vuelve, sin rebote.
  2. Presionar una fila de asesoría, un día del wizard, un resultado de búsqueda SAE: hundimiento más sutil que el del botón.
  3. Pasar el mouse por una materia de `Mis materias`, un slot de `Mi horario` y una materia del diálogo de agregar: el fondo cambia con transición, no de golpe. En un dispositivo táctil, el hover no se queda "pegado".
  4. Agregar una materia y esperar el toast: entra desde abajo y **sale** desvaneciéndose hacia abajo, no desaparece de golpe.
  5. Abrir el menú de la hamburguesa y cerrarlo (click en el disparador, Escape y click fuera): las tres rutas encogen el panel hacia su esquina superior derecha antes de desmontarlo.
  6. Abrir un diálogo (p. ej. "Cancelar asesoría") y cerrarlo con Escape o con el velo: contenido y velo se desvanecen, no desaparecen en un frame.
  7. Provocar un error de login (contraseña mala): el mensaje entra con fade, no aparece de golpe.
  8. Entrar a `/home`, a la oferta y al detalle de un asesor SAE: las listas y el swap de skeleton entran escalonados y apenas perceptibles.
  9. Abrir `/ruta-inventada` y `/` sin sesión: los cinco elementos entran escalonados.
  10. Activar "Reducir movimiento" en el SO y repetir 1, 4, 5, 6 y 9: nada se mueve, todo aparece y desaparece de inmediato, y ningún control queda inutilizable.

---

## Self-review

**1. Cobertura del catálogo del spec**

| Ítem | Task | Steps |
|---|---|---|
| Tokens `--ease-out` / `--ease-in-out` / `--ease-drawer` (ADR 0026) | 1 | 1 |
| A1 — `.presionable` en `Boton.tsx` y `Dialogo.tsx:39` | 1, 2 | 1 Step 3; 2 Steps 3-4 |
| A2 — `.presionable` en el tile de `Home.tsx:25` | 1, 3 | 1 Step 3; 3 Step 1 |
| A3 — `.fila-interactiva` en las 11 filas/tarjetas | 1, 4, 5 | 4 Steps 2-6; 5 Steps 1-3 |
| A4 — hover con transición y gateado en los 3 sitios | 1, 4, 5 | 1 Step 3; 4 Steps 5-6; 5 Step 3 |
| B1 — `.salida-toast` + state `saliendo` | 1, 6 | 1 Steps 2-3; 6 Steps 3, 5 |
| B2 — `.entrada-menu`/`.salida-menu` + state `cerrandoMenu` | 1, 7 | 1 Steps 2-3; 7 Step 3 |
| B3 — `.salida-dialogo`/`.salida-velo` en el wrapper de Radix | 1, 8 | 1 Steps 2-3; 8 Step 4 |
| C1 — `.entrada-lista` en los 5 `<p role="alert">` | 9 | 1-4 |
| C2 — swap skeleton → contenido | 10 | 1-2 (+ decisión de alcance 6 para los 4 ya cubiertos) |
| C3 — stagger en las listas que faltaban | 11, 12 | 11 Steps 1-5; 12 Steps 1-4 |
| D1 — `.entrada-deleite` en `NoEncontrado` | 1, 13 | 1 Steps 2-3; 13 Step 1 |
| D2 — `.entrada-deleite` en `Landing` | 1, 14 | 1 Steps 2-3; 14 Steps 1-2 |
| `prefers-reduced-motion` extendido en el mismo commit que introduce las clases | 1 | 4 |
| Rechazados (rutas SPA, tabs, parallax, datos leídos) | — | Global Constraints + Verificación final |

Sin huecos: cada fila A1-A4, B1-B3, C1-C3, D1-D2 del catálogo tiene task, y las cinco ubicaciones del spec que no encajaban con el código real están resueltas en "Decisiones de alcance" (4, 5, 6, 7, 10) sin inventar valores nuevos.

**2. Sin placeholders**

Cada step trae el string verbatim de origen y el de destino, verificados contra `dev` @ `63e1ad0` — incluida la indentación exacta, que es lo que distingue `AgendarAsesoria.tsx:141` de `:166` y `DetalleAsesoria.tsx:159` de `:215`. Los dos sitios donde el string se repite idéntico (`AdminAsesorias.tsx` en las Tasks 5 y 12) llevan instrucción explícita de reemplazo global y un `grep -c` de comprobación.

**3. Consistencia de nombres y contratos**

- Clases CSS declaradas en la Task 1 y usadas con el mismo nombre después: `presionable` (Tasks 2, 3), `fila-interactiva` (4, 5), `salida-toast` (6), `entrada-menu`/`salida-menu` (7), `salida-dialogo`/`salida-velo` (8), `entrada-deleite` (13, 14).
- Variables de easing: `--ease-out` (todas las clases nuevas menos `.entrada-menu`), `--ease-drawer` (`.entrada-menu`), `--ease-in-out` declarada por ADR 0026 y sin consumidor en este plan — es intencional, queda disponible para movimiento en pantalla futuro.
- Constantes de duración que deben espejar el CSS: `SALIDA_MS = 200` / `VISIBLE_MS = 2700` (`Retroalimentacion.tsx`, Task 6), `SALIDA_MENU_MS = 140` (`MenuUsuario.tsx`, Task 7), `SALIDA_DIALOGO_MS = 150` (`dialog.tsx`, Task 8) — cada una con comentario que apunta a su clase en `index.css`, y cada una es el número que los tests avanzan con `vi.advanceTimersByTime`.
- States nuevos, todos con nombre distinto de los existentes: `saliendo` (hook del toast), `cerrandoMenu` (`MenuUsuario`, junto al `cerrando` preexistente del logout), `cerrando` local de `dialog.tsx` (otro archivo, sin colisión).
- Parámetros de `.map()` añadidos: `indice` en todos salvo `MiHorario.tsx`, donde es `indiceSlot` para no sombrear el `indice` del día.
- Prop nuevo: `Retroalimentacion.saliendo: boolean`, obligatorio, con los 5 render sites enumerados en la Task 6 Step 5 y un `grep` de comprobación en el Step 6.
