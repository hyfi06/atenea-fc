# Sistema de componentes — adopción de shadcn/ui y rediseño de Disponibilidad — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ejecutar en `frontend/` lo que las specs de los pasos 3, 6 y 7 ya decidieron: adoptar el patrón shadcn/ui sobre los tokens M3 existentes, consolidar los 4 diálogos duplicados de asesorías en un componente compartido que codifica la convención de botones una sola vez, y reemplazar la grilla de `DisponibilidadAsesor` por las pantallas "Mis materias" y "Mi horario".

**Architecture:** Cuatro capas, de abajo hacia arriba. (1) Infraestructura: `components.json`, alias `@/` de imports, `src/lib/utils.ts` (`cn`), y un bloque de alias en `src/index.css` que declara el vocabulario de color de shadcn como tokens de Tailwind que apuntan a los roles M3 de [ADR 0014](../../decisions/0014-tokens-logo-iconos-frontend.md) — cero valores de color duplicados. (2) Primitivos generados por el CLI y curados (`dialog.tsx`, `tabs.tsx`) en la carpeta plana `components/ui/`, sin dependencias de íconos ni de animación de terceros. (3) `components/ui/Dialogo.tsx`, componente propio que envuelve `dialog.tsx` y codifica la convención de orden de botones del paso 3 (2 acciones = fila, 3+ = columna) — los 4 diálogos de `features/asesorias/` pasan a componerlo en vez de reconstruir Radix. (4) Las dos pantallas nuevas, con su núcleo de lógica pura en `logica.ts` (testeable sin render) y su capa de datos en `api.ts`.

**Tech Stack:** React 19, TypeScript 6, Vite 8, Tailwind CSS v4.3 (CSS-first, sin `tailwind.config.js`), Radix UI (`react-dialog` 1.1.23, `react-tabs` 1.1.21 — ya instalados), TanStack Query 5, Vitest 4 + Testing Library, `pnpm` 11, `oxlint`.

## Global Constraints

- **Todos los comandos de este plan se corren desde `frontend/`.** `pnpm test <ruta>` corre un archivo; `pnpm test` corre la suite completa; `pnpm build` es `tsc -b && vite build`; `pnpm lint` es `oxlint`.
- **No se toca `backend/`.** Este plan es exclusivamente frontend.
- **Tres pantallas nuevas dependen de endpoints que todavía no existen** en `dev-frontend`: `POST /api/asesorias/registros/{id}/materias/quitar/`, `GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/` y `POST /api/asesorias/disponibilidades/{id}/desactivar/`. Están planeados (tasks 6, 7 y 8 de `docs/superpowers/plans/2026-08-04-login-oauth-backend.md`, ya escrito, aún sin ejecutar). Este plan implementa el frontend contra esos contratos exactos; **los tests no tocan red**, así que la suite pasa igual, pero esas dos acciones fallarán en runtime hasta que el plan de backend se ejecute y se integre. No inventes un fallback ni cambies el contrato.
- **`Boton.tsx`, `InsigniaEstado.tsx`, `Retroalimentacion.tsx` y `Skeleton.tsx` no se tocan.** Decisión 5 de la [spec del paso 6](../specs/2026-08-04-sistema-componentes-design.md): no están duplicados, migrarlos sería refactor no relacionado. Si un task parece necesitar cambiarlos, la solución correcta está en otro lado (ver Decisión 5 de la sección final).
- **`components/ui/` es plana** ([ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)): los primitivos generados por shadcn conservan el nombre en minúsculas que trae el CLI (`dialog.tsx`, `tabs.tsx`) y conviven sin subcarpeta con los componentes propios en PascalCase y español (`Boton.tsx`, `Dialogo.tsx`).
- **Cero paleta paralela.** Ningún archivo de este plan escribe un valor de color literal. El único lugar donde aparece el vocabulario de shadcn es el bloque de alias de `index.css`, y ahí cada nombre apunta con `var()` a un rol M3 ya definido.
- **Cero dependencias de UI de terceros más allá de las tres que fija ADR 0020** (`class-variance-authority`, `clsx`, `tailwind-merge`). En particular: **no se queda `lucide-react` ni `tw-animate-css`**, que el CLI de shadcn instala por default (ver Decisiones 3 y 4 al final).
- **Accesibilidad, checklist del paso 7** (`docs/development/contribuir-componentes.md`), obligatorio en todo elemento interactivo que este plan cree o toque: clase `.foco-visible` (definida en la Task 1), área de toque ≥ 44px en botones de ícono, `aria-label` en controles sin texto, `aria-hidden` en SVG decorativos, y **no** interceptar teclado que Radix ya maneja (`Esc`, foco atrapado, flechas en tabs).
- **TDD estricto, commits atómicos.** Cada task escribe el test primero, lo corre para verlo fallar, implementa lo mínimo, lo corre para verlo pasar, y comitea.
- **Convención de commits del repo** (`docs/development/commit-conventions.md`, ADR 0007): `[type][scope] resumen` en la primera línea, bullets de detalle en el cuerpo, `Signed-off-by` generado con `git commit -s`. Tipos usados aquí: `chore`, `feat`, `refactor`, `test`, `docs`.
- **Imports:** el alias `@/` que introduce la Task 1 se usa **solo** en archivos nuevos y en los primitivos generados. Los imports relativos existentes no se reescriben en masa (ver Decisión 2).

---

## File Structure

**Infraestructura (Task 1)**

- **Crear** `frontend/components.json` — configuración del CLI de shadcn (estilo, ruta del CSS, alias).
- **Crear** `frontend/src/lib/utils.ts` — `cn()`, la única utilidad que todos los primitivos de shadcn importan.
- **Crear** `frontend/src/lib/utils.test.ts`.
- **Modificar** `frontend/src/index.css` — bloque de alias shadcn→M3, keyframes del diálogo, clase `.foco-visible`.
- **Modificar** `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json` — alias `@/` → `src/`.
- **Modificar** `frontend/package.json` / `pnpm-lock.yaml` — tres dependencias nuevas.

**Primitivos de shadcn (Tasks 2 y 6)**

- **Crear** `frontend/src/components/ui/dialog.tsx` + `dialog.test.tsx`.
- **Crear** `frontend/src/components/ui/tabs.tsx` + `tabs.test.tsx`.

**Componente compartido (Task 3)**

- **Crear** `frontend/src/components/ui/Dialogo.tsx` + `Dialogo.test.tsx` — el único lugar donde vive la convención de orden de botones.

**Diálogos de asesorías migrados (Tasks 4 y 5)**

- **Modificar** `frontend/src/features/asesorias/components/DialogoCancelar.tsx`, `DialogoAgregarMateria.tsx`, `DialogoNuevoBloque.tsx`, `DialogoBloqueActivo.tsx` + un archivo de test junto a cada uno.

**Cimientos de las pantallas nuevas (Task 7)**

- **Crear** `frontend/src/api/errores.ts` + `errores.test.ts` — `primerMensajeDeError`, hoy duplicado en dos pantallas.
- **Crear** `frontend/src/components/icons/UiIcons.tsx` — `IconVirtual`, `IconPresencial`, `IconBasura`.
- **Crear** `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx` + test.
- **Modificar** `frontend/src/features/asesorias/api.ts` — `useRegistroDelSemestre`.
- **Modificar** `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx` — usa `errores.ts` en vez de su copia local.

**Pantallas nuevas (Tasks 8, 9, 10)**

- **Crear** `frontend/src/features/asesorias/screens/MisMaterias.tsx` + test.
- **Crear** `frontend/src/features/asesorias/components/DialogoQuitarMateria.tsx`.
- **Modificar** `frontend/src/features/asesorias/logica.ts` + `logica.test.ts` — `horasDelDia`, `slotsDelDia`, `diaSemanaHoy`.
- **Modificar** `frontend/src/api/types.ts`, `frontend/src/features/asesorias/api.ts` — tipos y hooks de la superficie nueva.
- **Crear** `frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.tsx` + test.
- **Crear** `frontend/src/features/asesorias/screens/MiHorario.tsx` + test.

**Retiro de la grilla (Task 11)**

- **Borrar** `frontend/src/features/asesorias/screens/DisponibilidadAsesor.tsx`, `frontend/src/features/asesorias/components/GrillaDisponibilidad.tsx`.
- **Modificar** `frontend/src/App.tsx`, `frontend/src/features/asesorias/screens/SesionesAsesor.tsx` (+ su test), `frontend/src/features/asesorias/logica.ts` / `logica.test.ts`.

**Documentación (Task 12)**

- **Modificar** `docs/development/contribuir-componentes.md`, `docs/decisions/0020-sistema-componentes-shadcn.md`, `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`.

---

### Task 1: Inicializar shadcn/ui y mapear su vocabulario de color a los tokens M3

Implementa las decisiones 2, 3 y 6 de la [spec del paso 6](../specs/2026-08-04-sistema-componentes-design.md). Al terminar, el CLI de shadcn puede agregar componentes al repo y esos componentes consumen la paleta de ADR 0014 sin introducir una segunda.

**Files:**
- Create: `frontend/components.json`
- Create: `frontend/src/lib/utils.ts`
- Test: `frontend/src/lib/utils.test.ts`
- Modify: `frontend/src/index.css`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/tsconfig.json`
- Modify: `frontend/tsconfig.app.json`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: el bloque `@theme` existente de `index.css` (tokens `--color-{rol}` de ADR 0014) y los `@keyframes`/clases de motion ya definidos ahí.
- Produces:
  - `@/lib/utils` → `cn(...inputs: ClassValue[]): string`. Lo consumen las Tasks 2, 3, 6, 8 y 10.
  - Alias de imports `@/*` → `frontend/src/*`, resuelto por Vite, Vitest y `tsc`.
  - Tokens de Tailwind nuevos, todos apuntando a roles M3: `foreground`, `card`, `card-foreground`, `popover`, `popover-foreground`, `primary-foreground`, `secondary-foreground`, `muted`, `muted-foreground`, `accent`, `accent-foreground`, `destructive`, `destructive-foreground`, `border`, `input`, `ring`.
  - Clases CSS `.foco-visible`, `.entrada-dialogo`, `.entrada-velo`.

- [ ] **Step 1: Escribir el test de `cn` — RED**

Crear `frontend/src/lib/utils.test.ts`. Importa por el alias a propósito: si el alias no está bien configurado, este test no resuelve el módulo y falla.

```ts
import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

describe('cn', () => {
  it('resuelve conflictos de clases de Tailwind conservando la última', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4')
  })

  it('descarta los valores condicionales falsos', () => {
    expect(cn('rounded-full', false && 'hidden', undefined, null)).toBe('rounded-full')
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pnpm test src/lib/utils.test.ts`

Expected: FAIL — `Failed to resolve import "@/lib/utils"`. Ni el alias ni el módulo existen todavía.

- [ ] **Step 3: Correr el init de shadcn**

Run:
```bash
pnpm dlx shadcn@latest init --base-color neutral --yes
```

Qué hace y qué esperar: detecta Tailwind v4 + Vite, instala `class-variance-authority`, `clsx`, `tailwind-merge` (y probablemente `tw-animate-css`), crea `components.json` y `src/lib/utils.ts`, y **reescribe `src/index.css` agregando su propia paleta** (`:root`/`.dark` en oklch + un bloque `@theme inline`). Puede además tocar `vite.config.ts` y los `tsconfig`.

El `--base-color` es irrelevante: la paleta generada se descarta entera en el Step 4. Se pasa solo para que el comando no sea interactivo.

**Si no hay red o el comando falla:** no es bloqueante. Corre `pnpm add class-variance-authority clsx tailwind-merge` y escribe a mano `components.json` (Step 5) y `src/lib/utils.ts` (Step 6) con el contenido exacto que este task muestra; los Steps 4, 7 y 8 son idénticos en ambos caminos.

- [ ] **Step 4: Descartar la paleta que generó el init y quitar `tw-animate-css`**

El init duplica la paleta con nombres de shadcn, exactamente lo que la decisión 2 de la spec prohíbe. Se descarta completa:

```bash
git checkout -- src/index.css
pnpm remove tw-animate-css 2>/dev/null || true
git diff --stat
```

Después de esto, `git diff --stat` debe mostrar `package.json` y `pnpm-lock.yaml` modificados (y quizá `vite.config.ts`/`tsconfig*.json`), **no** `src/index.css`. Verifica que `package.json` tenga exactamente tres dependencias nuevas — `class-variance-authority`, `clsx`, `tailwind-merge` — y ninguna de `lucide-react` o `tw-animate-css`.

- [ ] **Step 5: Fijar `components.json`**

Reemplazar el archivo completo `frontend/components.json` por:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "aliases": {
    "components": "@/components",
    "ui": "@/components/ui",
    "utils": "@/lib/utils",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

`"config": ""` es lo correcto para Tailwind v4 (no hay `tailwind.config.js`, ADR 0014). `"iconLibrary": "lucide"` queda declarado porque es lo que el CLI espera, pero **ningún ícono de lucide entra al repo**: cada componente generado que traiga uno se cura a mano (Task 2). `"ui": "@/components/ui"` mantiene la carpeta plana de ADR 0020.

- [ ] **Step 6: Fijar `src/lib/utils.ts`**

Reemplazar el archivo completo `frontend/src/lib/utils.ts` por:

```ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Combina clases condicionales y resuelve conflictos de Tailwind.
 *  Es la utilidad que todos los primitivos generados por shadcn importan. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
```

El `import { clsx, type ClassValue }` inline es obligatorio: `tsconfig.app.json` tiene `verbatimModuleSyntax: true`, que exige marcar los imports de tipo.

- [ ] **Step 7: Configurar el alias `@/` en Vite y en TypeScript**

Reemplazar `frontend/vite.config.ts` completo por:

```ts
/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

`fileURLToPath(new URL(...))` en vez del `path.resolve(__dirname, ...)` que sugiere la guía de shadcn: `package.json` declara `"type": "module"`, así que `__dirname` no existe en este archivo. Vitest hereda `resolve.alias` de esta misma config, sin configuración extra.

En `frontend/tsconfig.json`, agregar `compilerOptions` (el CLI de shadcn lee este archivo para resolver los alias; hoy solo tiene `files` y `references`):

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

En `frontend/tsconfig.app.json`, agregar dentro de `compilerOptions` (después de `"jsx": "react-jsx",`):

```json
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },
```

- [ ] **Step 8: Escribir el bloque de alias de tokens, el motion del diálogo y la clase de foco**

En `frontend/src/index.css`, insertar el bloque de alias **inmediatamente después** del `@theme` existente (es decir, después de la línea `}` que cierra el bloque con `--color-surface-container-high`, antes de la regla `body`):

```css
/* Alias de shadcn/ui → tokens M3 de ADR 0014.
   Los componentes que genera el CLI de shadcn usan su propio vocabulario de
   color (bg-popover, text-muted-foreground, border-border, ring-ring...).
   Aquí cada uno de esos nombres se declara como token de Tailwind que apunta
   con var() al rol M3 equivalente ya definido arriba: no hay una segunda
   paleta, ningún valor de color se repite en este bloque. ADR 0014 sigue
   siendo la fuente canónica de color.
   Los nombres que shadcn comparte con ADR 0014 (background, primary,
   secondary) ya existen arriba y por eso no aparecen aquí. */
@theme {
  --color-foreground: var(--color-on-surface);
  --color-card: var(--color-surface-container);
  --color-card-foreground: var(--color-on-surface);
  --color-popover: var(--color-surface-container);
  --color-popover-foreground: var(--color-on-surface);
  --color-primary-foreground: var(--color-on-primary);
  --color-secondary-foreground: var(--color-on-secondary);
  --color-muted: var(--color-surface-container-high);
  --color-muted-foreground: var(--color-on-surface-variant);
  --color-accent: var(--color-surface-container-high);
  --color-accent-foreground: var(--color-on-surface);
  --color-destructive: var(--color-error);
  --color-destructive-foreground: var(--color-on-error);
  --color-border: var(--color-outline-variant);
  --color-input: var(--color-outline);
  --color-ring: var(--color-primary);
}
```

Se usa `@theme` normal, no `@theme inline`: la paleta de ADR 0014 es dark-only y estática (no se redefine en ningún selector anidado tipo `.dark`), así que dejar la referencia `var()` en el `:root` emitido es correcto y además hace el mapeo legible en devtools.

En el mismo archivo, agregar después del bloque `@keyframes girar { ... }`:

```css
@keyframes entrada-dialogo {
  from { opacity: 0; transform: translate(-50%, -48%) scale(0.97); }
  to   { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

@keyframes entrada-velo {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

y después de la clase `.spinner { ... }`:

```css
.entrada-dialogo {
  animation: entrada-dialogo 180ms ease-out;
}

.entrada-velo {
  animation: entrada-velo 180ms ease-out;
}

/* Checklist de accesibilidad del paso 7: todo elemento interactivo nuevo
   necesita un foco perceptible, no solo la ausencia del outline del
   navegador. Se declara una vez aquí, como .skeleton/.spinner, en vez de
   repetir el mismo grupo de utilidades en cada componente. */
.foco-visible:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

y finalmente extender el bloque de motion reducido — reemplazar la lista de selectores de `@media (prefers-reduced-motion: reduce)` por:

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

- [ ] **Step 9: Correr el test y confirmar que pasa**

Run: `pnpm test src/lib/utils.test.ts`

Expected: PASS — los 2 casos.

- [ ] **Step 10: Verificar que el build y la suite completa siguen sanos**

Run: `pnpm build && pnpm test && pnpm lint`

Expected: los tres en verde. El `build` prueba que `tsc -b` acepta el `paths` nuevo en los dos tsconfig y que Vite resuelve el alias.

- [ ] **Step 11: Commit**

```bash
git add frontend/components.json frontend/src/lib/utils.ts frontend/src/lib/utils.test.ts \
        frontend/src/index.css frontend/vite.config.ts frontend/tsconfig.json \
        frontend/tsconfig.app.json frontend/package.json frontend/pnpm-lock.yaml
git commit -s -m "[chore][frontend] inicializar shadcn/ui sobre los tokens M3 existentes" \
  -m "- components.json con la carpeta plana components/ui y el CSS de
    Tailwind v4 (sin tailwind.config.js), mas alias @/ resuelto en Vite,
    Vitest y los dos tsconfig.
- Bloque de alias en index.css: el vocabulario de color de shadcn
    (foreground, popover, muted, destructive, border, ring...) se declara
    apuntando con var() a los roles M3 de ADR 0014, sin duplicar un solo
    valor de color.
- Motion propio para el dialogo (entrada-dialogo/entrada-velo) y clase
    .foco-visible del checklist del paso 7, ambas registradas en el bloque
    de prefers-reduced-motion; se descarto tw-animate-css que el init
    instala por default.
- Dependencias nuevas: class-variance-authority, clsx, tailwind-merge
    (ADR 0020). cn() en src/lib/utils.ts con su test."
```

---

### Task 2: Primitivo `dialog.tsx` de shadcn, curado

Trae el primer componente del CLI y lo deja consistente con las restricciones del proyecto: sin `lucide-react` (ADR 0014 decidió íconos a mano), sin `tw-animate-css` (el motion vive en `index.css` y respeta `prefers-reduced-motion`, paso 7).

**Files:**
- Create: `frontend/src/components/ui/dialog.tsx`
- Test: `frontend/src/components/ui/dialog.test.tsx`

**Interfaces:**
- Consumes: `@/lib/utils` (`cn`, Task 1); `@radix-ui/react-dialog` 1.1.23 (ya instalado); clases `.entrada-dialogo`/`.entrada-velo` (Task 1).
- Produces: `@/components/ui/dialog` exporta `Dialog`, `DialogPortal`, `DialogClose`, `DialogOverlay`, `DialogContent`, `DialogTitle`, `DialogDescription`. La Task 3 los consume; ninguna feature los importa directo.

- [ ] **Step 1: Escribir el test del primitivo — RED**

Crear `frontend/src/components/ui/dialog.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from './dialog'

function abrirDialogo(onOpenChange = vi.fn()) {
  render(
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>Título de prueba</DialogTitle>
        <DialogDescription>Descripción de prueba</DialogDescription>
      </DialogContent>
    </Dialog>,
  )
  return onOpenChange
}

describe('dialog', () => {
  it('expone el contenido como diálogo con nombre accesible tomado del título', () => {
    abrirDialogo()

    expect(screen.getByRole('dialog', { name: 'Título de prueba' })).toBeInTheDocument()
    expect(screen.getByText('Descripción de prueba')).toBeInTheDocument()
  })

  it('cierra con Escape sin que el componente intercepte el teclado', () => {
    const onOpenChange = abrirDialogo()

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('no renderiza nada cuando está cerrado', () => {
    render(
      <Dialog open={false}>
        <DialogContent>
          <DialogTitle>Oculto</DialogTitle>
        </DialogContent>
      </Dialog>,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pnpm test src/components/ui/dialog.test.tsx`

Expected: FAIL — `Failed to resolve import "./dialog"`.

- [ ] **Step 3: Generar el componente con el CLI**

Run:
```bash
pnpm dlx shadcn@latest add dialog --yes
```

Escribe `src/components/ui/dialog.tsx`. Ojo con dos cosas que el Step 4 corrige: importa `XIcon` de `lucide-react` (y probablemente instaló el paquete) y usa utilidades de animación de `tw-animate-css` (`animate-in`, `fade-in-0`, `zoom-in-95`).

Si no hay red, salta al Step 4 y escribe el archivo completo a mano — el contenido está abajo íntegro.

- [ ] **Step 4: Curar el archivo generado**

Reemplazar `frontend/src/components/ui/dialog.tsx` completo por:

```tsx
import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'

import { cn } from '@/lib/utils'

/**
 * Primitivo `dialog` de shadcn/ui (ADR 0020), curado para este proyecto:
 *
 * - Sin el botón "X" de cierre que trae el original: venía con un ícono de
 *   `lucide-react`, y ADR 0014 decidió íconos a mano sin librería. Además
 *   sería redundante — `Dialogo.tsx` siempre renderiza una acción de salir
 *   explícita, según la convención de botones del paso 3.
 * - Sin `tw-animate-css`: la animación de entrada usa las clases
 *   `.entrada-dialogo`/`.entrada-velo` de `index.css`, que sí están
 *   registradas en el bloque de `prefers-reduced-motion` (paso 7).
 * - Los colores usan el vocabulario de shadcn (`bg-popover`, `border`,
 *   `text-muted-foreground`), que el bloque de alias de `index.css` mapea a
 *   los roles M3 de ADR 0014.
 *
 * Las features no importan este archivo: componen `Dialogo.tsx`.
 */

function Dialog({ ...props }: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />
}

function DialogPortal({ ...props }: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />
}

function DialogClose({ ...props }: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

function DialogOverlay({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      data-slot="dialog-overlay"
      className={cn('entrada-velo fixed inset-0 z-50 bg-black/50', className)}
      {...props}
    />
  )
}

function DialogContent({ className, children, ...props }: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          'entrada-dialogo fixed left-1/2 top-1/2 z-50 flex max-h-[calc(100svh-2rem)] w-[calc(100%-2rem)] max-w-sm',
          '-translate-x-1/2 -translate-y-1/2 flex-col gap-4 overflow-y-auto rounded-lg border border-border',
          'bg-popover p-5 text-popover-foreground shadow-lg',
          className,
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPortal>
  )
}

function DialogTitle({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn('text-sm font-semibold text-foreground', className)}
      {...props}
    />
  )
}

function DialogDescription({ className, ...props }: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn('text-xs text-muted-foreground', className)}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogPortal,
  DialogClose,
  DialogOverlay,
  DialogContent,
  DialogTitle,
  DialogDescription,
}
```

- [ ] **Step 5: Confirmar que no quedó ninguna dependencia de terceros colada**

Run:
```bash
grep -rn "lucide\|tw-animate" src/ package.json || echo "LIMPIO"
```

Expected: imprime `LIMPIO`. Si aparece algo en `package.json`, corre `pnpm remove lucide-react tw-animate-css` y repite.

- [ ] **Step 6: Correr el test y confirmar que pasa**

Run: `pnpm test src/components/ui/dialog.test.tsx`

Expected: PASS — los 3 casos.

- [ ] **Step 7: Verificar que el mapeo de tokens llega al CSS compilado**

Este es el chequeo real del bloque de alias de la Task 1: hasta ahora ningún archivo usaba el vocabulario de shadcn, así que Tailwind no emitía esas variables (comportamiento JIT normal, ADR 0014).

Run:
```bash
pnpm build && grep -o -- "--color-popover:[^;]*" dist/assets/*.css | head -3
```

Expected: la salida contiene `--color-popover: var(--color-surface-container)` (o el mismo par con el orden de propiedades que emita Tailwind). Si la variable no aparece, el bloque de alias no está siendo leído — revisa que quedó dentro de un `@theme` y después del `@theme` original.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/ui/dialog.tsx frontend/src/components/ui/dialog.test.tsx \
        frontend/package.json frontend/pnpm-lock.yaml
git commit -s -m "[feat][frontend] agregar el primitivo dialog de shadcn/ui" \
  -m "- components/ui/dialog.tsx generado con el CLI y curado: sin el boton X
    de lucide-react (ADR 0014 decidio iconos a mano) y sin utilidades de
    tw-animate-css; la entrada usa las clases de motion de index.css, que
    si respetan prefers-reduced-motion.
- Colores via el vocabulario de shadcn mapeado a los roles M3 en el bloque
    de alias de index.css; verificado en el CSS compilado.
- Test de comportamiento: nombre accesible tomado del titulo, cierre con
    Escape sin interceptar el teclado que Radix ya maneja, y nada
    renderizado cuando esta cerrado."
```

---

### Task 3: `Dialogo.tsx` — la convención de orden de botones, codificada una sola vez

El corazón del plan. La convención del [paso 3](../specs/2026-08-04-revision-vistas-asesorias-design.md) (2 acciones = fila; 3+ = columna con orden fijo; `min-width: 0` contra el overflow) deja de ser algo que cada diálogo copia a mano y pasa a ser el comportamiento de un componente.

Forma de la API, con su razón: **la acción de salir nunca se pasa como dato**. `Dialogo` la construye siempre a partir de `onCerrar` y `etiquetaSalir`, porque dónde va y con qué estilo es precisamente la convención. Lo que el consumidor pasa es `acciones`, ordenadas de menor a mayor consecuencia. De ahí sale todo lo demás:

| `acciones.length` | Botones totales | Layout | Estilos |
|---|---|---|---|
| 1 | 2 | fila | salir a la izquierda en contorno, la acción a la derecha rellena con su tono |
| ≥ 2 | ≥ 3 | columna, ancho completo | `acciones[0]` (la reversible) rellena; el resto en contorno; salir al final como texto plano |

**Files:**
- Create: `frontend/src/components/ui/Dialogo.tsx`
- Test: `frontend/src/components/ui/Dialogo.test.tsx`

**Interfaces:**
- Consumes: `@/components/ui/dialog` (Task 2), `@/lib/utils` (Task 1), clase `.foco-visible` y `.spinner` de `index.css`.
- Produces:
  - `AccionDialogo` — `{ etiqueta: string; onClick: () => void; tono?: 'primario' | 'peligro'; cargando?: boolean; deshabilitada?: boolean }`
  - `Dialogo` — props `{ abierto: boolean; titulo: string; descripcion?: string; error?: string | null; acciones: AccionDialogo[]; etiquetaSalir?: string; onCerrar: () => void; children?: ReactNode }`. `etiquetaSalir` default `'Volver'`. Lo consumen las Tasks 4, 5, 8 y 10.

- [ ] **Step 1: Escribir los tests de la convención — RED**

Crear `frontend/src/components/ui/Dialogo.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dialogo } from './Dialogo'

function etiquetasDeBotones() {
  return screen.getAllByRole('button').map((boton) => boton.textContent)
}

describe('Dialogo — convención de orden de botones (paso 3)', () => {
  it('con una sola acción pone salir a la izquierda y la acción a la derecha', () => {
    render(
      <Dialogo
        abierto
        titulo="Cancelar asesoría"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Confirmar cancelación', tono: 'peligro', onClick: vi.fn() }]}
      />,
    )

    expect(etiquetasDeBotones()).toEqual(['Volver', 'Confirmar cancelación'])
  })

  it('con dos o más acciones pasa a columna, respeta el orden y deja salir al final', () => {
    render(
      <Dialogo
        abierto
        titulo="Este horario tiene sesiones agendadas"
        onCerrar={vi.fn()}
        acciones={[
          { etiqueta: 'Solo dejar de recibir nuevas', onClick: vi.fn() },
          { etiqueta: 'Cancelar esas sesiones y desactivar', tono: 'peligro', onClick: vi.fn() },
        ]}
      />,
    )

    expect(etiquetasDeBotones()).toEqual([
      'Solo dejar de recibir nuevas',
      'Cancelar esas sesiones y desactivar',
      'Volver',
    ])
  })

  it('en columna la acción consecuente va en contorno, nunca rellena', () => {
    render(
      <Dialogo
        abierto
        titulo="Bloque activo"
        onCerrar={vi.fn()}
        acciones={[
          { etiqueta: 'Desactivar', onClick: vi.fn() },
          { etiqueta: 'Eliminar', tono: 'peligro', onClick: vi.fn() },
        ]}
      />,
    )

    const consecuente = screen.getByRole('button', { name: 'Eliminar' })
    expect(consecuente).toHaveClass('bg-transparent')
    expect(consecuente).toHaveClass('border-error')
  })

  it('los botones no se desbordan con etiquetas largas (min-w-0 + salto de línea)', () => {
    render(
      <Dialogo
        abierto
        titulo="Quitar materia"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Quitar Aplicación de las Ciencias de la Tierra', tono: 'peligro', onClick: vi.fn() }]}
      />,
    )

    for (const boton of screen.getAllByRole('button')) {
      expect(boton).toHaveClass('min-w-0')
      expect(boton).toHaveClass('whitespace-normal')
    }
  })

  it('todo botón del diálogo lleva el estado de foco visible del paso 7', () => {
    render(
      <Dialogo abierto titulo="Con foco" onCerrar={vi.fn()} acciones={[{ etiqueta: 'Aceptar', onClick: vi.fn() }]} />,
    )

    for (const boton of screen.getAllByRole('button')) {
      expect(boton).toHaveClass('foco-visible')
    }
  })
})

describe('Dialogo — comportamiento', () => {
  it('cerrar con Escape o con el botón de salir llama a onCerrar', () => {
    const onCerrar = vi.fn()
    render(<Dialogo abierto titulo="Salir" onCerrar={onCerrar} acciones={[]} etiquetaSalir="Cerrar" />)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onCerrar).toHaveBeenCalledTimes(2)
  })

  it('una acción deshabilitada no dispara su onClick', () => {
    const onClick = vi.fn()
    render(
      <Dialogo
        abierto
        titulo="Agregar materia"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Agregar', deshabilitada: true, onClick }]}
      />,
    )

    const boton = screen.getByRole('button', { name: 'Agregar' })
    expect(boton).toBeDisabled()
    fireEvent.click(boton)
    expect(onClick).not.toHaveBeenCalled()
  })

  it('una acción cargando se deshabilita sola', () => {
    render(
      <Dialogo
        abierto
        titulo="Creando"
        onCerrar={vi.fn()}
        acciones={[{ etiqueta: 'Crear', cargando: true, onClick: vi.fn() }]}
      />,
    )

    expect(screen.getByRole('button', { name: 'Crear' })).toBeDisabled()
  })

  it('el error se anuncia como alerta', () => {
    render(
      <Dialogo abierto titulo="Con error" error="No se pudo guardar." onCerrar={vi.fn()} acciones={[]} />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo guardar.')
  })

  it('renderiza el contenido propio del consumidor', () => {
    render(
      <Dialogo abierto titulo="Con formulario" onCerrar={vi.fn()} acciones={[]}>
        <label htmlFor="campo">Motivo</label>
        <input id="campo" />
      </Dialogo>,
    )

    expect(screen.getByLabelText('Motivo')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/components/ui/Dialogo.test.tsx`

Expected: FAIL — `Failed to resolve import "./Dialogo"` en los 10 casos.

- [ ] **Step 3: Escribir el componente**

Crear `frontend/src/components/ui/Dialogo.tsx`:

```tsx
import type { ReactNode } from 'react'

import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

type TonoAccion = 'primario' | 'peligro'

export interface AccionDialogo {
  etiqueta: string
  onClick: () => void
  /** `peligro` para acciones destructivas. Default `primario`. */
  tono?: TonoAccion
  cargando?: boolean
  deshabilitada?: boolean
}

interface DialogoProps {
  abierto: boolean
  titulo: string
  descripcion?: string
  /** Mensaje de error de la última acción, se anuncia con role="alert". */
  error?: string | null
  /**
   * Acciones ordenadas de menor a mayor consecuencia. La acción de salir NO
   * va aquí: la construye el componente, porque su posición y su estilo son
   * parte de la convención.
   */
  acciones: AccionDialogo[]
  etiquetaSalir?: string
  onCerrar: () => void
  children?: ReactNode
}

// `min-w-0` + `whitespace-normal` son el fix de overflow del paso 3: sin
// ellos un botón con flex-1 no se encoge por debajo del ancho de su propio
// texto y el par se desborda. Por eso también `min-h-11` en vez de una
// altura fija: el botón tiene que poder crecer a dos líneas.
const BASE_BOTON =
  'foco-visible flex min-h-11 min-w-0 items-center justify-center gap-2 whitespace-normal rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60'

const RELLENO: Record<TonoAccion, string> = {
  primario: 'bg-primary text-on-primary',
  peligro: 'bg-error-container text-on-error-container',
}

const CONTORNO: Record<TonoAccion, string> = {
  primario: 'border border-outline bg-transparent text-primary',
  peligro: 'border border-error bg-transparent text-error',
}

const TEXTO_PLANO = 'bg-transparent text-primary'

function BotonDialogo({ accion, className }: { accion: AccionDialogo; className?: string }) {
  return (
    <button
      type="button"
      onClick={accion.onClick}
      disabled={accion.deshabilitada === true || accion.cargando === true}
      className={cn(BASE_BOTON, className)}
    >
      {accion.cargando === true && <span className="spinner h-4 w-4" aria-hidden />}
      {accion.etiqueta}
    </button>
  )
}

/**
 * Diálogo compartido de Atenea. Envuelve el primitivo `dialog` de shadcn y
 * codifica **una sola vez** la convención de orden de botones fijada en el
 * paso 3 del rediseño:
 *
 * - 2 acciones (una `accion` + salir) → fila: salir a la izquierda, la
 *   acción de confirmación a la derecha con su estilo semántico.
 * - 3+ acciones → columna a ancho completo: la reversible arriba (única que
 *   puede ir rellena), las consecuentes en contorno (nunca rellenas, para
 *   que la destructiva no se lea como la opción fácil), y salir al final
 *   como texto plano.
 *
 * Los diálogos específicos de un feature componen este componente; no
 * vuelven a montar `Dialog.Root`/`Portal`/`Overlay` por su cuenta.
 */
export function Dialogo({
  abierto,
  titulo,
  descripcion,
  error,
  acciones,
  etiquetaSalir = 'Volver',
  onCerrar,
  children,
}: DialogoProps) {
  const enColumna = acciones.length > 1
  const accionSalir: AccionDialogo = { etiqueta: etiquetaSalir, onClick: onCerrar }

  return (
    <Dialog open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <DialogContent>
        <div className="flex flex-col gap-1">
          <DialogTitle>{titulo}</DialogTitle>
          {descripcion !== undefined && <DialogDescription>{descripcion}</DialogDescription>}
        </div>

        {children}

        {error != null && error !== '' && (
          <p role="alert" className="text-xs text-error">
            {error}
          </p>
        )}

        <div className={cn('flex gap-2', enColumna ? 'flex-col' : 'flex-row')}>
          {enColumna ? (
            <>
              {acciones.map((accion, indice) => (
                <BotonDialogo
                  key={accion.etiqueta}
                  accion={accion}
                  className={indice === 0 ? RELLENO[accion.tono ?? 'primario'] : CONTORNO[accion.tono ?? 'primario']}
                />
              ))}
              <BotonDialogo accion={accionSalir} className={cn(TEXTO_PLANO, 'mt-1')} />
            </>
          ) : (
            <>
              <BotonDialogo accion={accionSalir} className={cn(CONTORNO.primario, 'flex-1')} />
              {acciones.map((accion) => (
                <BotonDialogo
                  key={accion.etiqueta}
                  accion={accion}
                  className={cn(RELLENO[accion.tono ?? 'primario'], 'flex-1')}
                />
              ))}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pnpm test src/components/ui/Dialogo.test.tsx`

Expected: PASS — los 10 casos.

- [ ] **Step 5: Correr la suite completa y el lint**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: todo en verde.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/Dialogo.tsx frontend/src/components/ui/Dialogo.test.tsx
git commit -s -m "[feat][frontend] agregar Dialogo compartido con la convencion de botones" \
  -m "- components/ui/Dialogo.tsx envuelve el primitivo dialog de shadcn y
    codifica una sola vez la convencion del paso 3: 1 accion + salir en
    fila (salir a la izquierda), 2+ acciones en columna con la reversible
    arriba, las consecuentes en contorno y salir al final como texto plano.
- La accion de salir no es un dato que pase el consumidor: la construye el
    componente a partir de onCerrar, porque su posicion y estilo SON la
    convencion.
- Incluye el fix de overflow del paso 3 (min-w-0 + whitespace-normal +
    min-h-11 en vez de altura fija) y la clase .foco-visible del paso 7 en
    todos sus botones, verificado por test."
```

---

### Task 4: Migrar los dos diálogos de una acción (`DialogoCancelar`, `DialogoAgregarMateria`)

Primeros dos consumidores del componente compartido. Ambos son de 2 botones (fila), y ambos hoy reconstruyen `Dialog.Root`/`Portal`/`Overlay`/`Content` a mano. Su comportamiento visible no cambia; lo que desaparece es el wiring duplicado.

**Files:**
- Modify: `frontend/src/features/asesorias/components/DialogoCancelar.tsx`
- Modify: `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx`
- Test: `frontend/src/features/asesorias/components/DialogoCancelar.test.tsx` (crear)
- Test: `frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx` (crear)

**Interfaces:**
- Consumes: `Dialogo`/`AccionDialogo` (Task 3); `useMaterias` de `features/catalogo/api` (existente).
- Produces: los dos componentes conservan **exactamente** las props que ya tenían — `DetalleAsesoria.tsx` y las pantallas nuevas los usan sin cambios.

- [ ] **Step 1: Escribir los tests de comportamiento — RED**

Crear `frontend/src/features/asesorias/components/DialogoCancelar.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoCancelar } from './DialogoCancelar'

describe('DialogoCancelar', () => {
  it('confirma con el motivo que escribió el asesor', () => {
    const onConfirmar = vi.fn()
    render(
      <DialogoCancelar abierto cargando={false} error={null} onConfirmar={onConfirmar} onCerrar={vi.fn()} />,
    )

    fireEvent.change(screen.getByLabelText(/Motivo/), { target: { value: 'Junta académica.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar cancelación' }))

    expect(onConfirmar).toHaveBeenCalledWith('Junta académica.')
  })

  it('sigue la convención de 2 acciones: salir a la izquierda', () => {
    render(<DialogoCancelar abierto cargando={false} error={null} onConfirmar={vi.fn()} onCerrar={vi.fn()} />)

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'Volver',
      'Confirmar cancelación',
    ])
  })

  it('muestra el error del backend como alerta', () => {
    render(
      <DialogoCancelar
        abierto
        cargando={false}
        error="No se pudo cancelar."
        onConfirmar={vi.fn()}
        onCerrar={vi.fn()}
      />,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo cancelar.')
  })
})
```

Crear `frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoAgregarMateria } from './DialogoAgregarMateria'
import * as catalogo from '../../catalogo/api'
import type { Materia } from '../../../api/types'

function crearMateria(overrides: Partial<Materia>): Materia {
  return {
    id: 1, clave: '0001', nombre: 'Cálculo I', carrera: 1, nivel: null,
    plan: 1, habilitada_asesorias: true, ...overrides,
  }
}

function montar(materias: Materia[]) {
  vi.spyOn(catalogo, 'useMaterias').mockReturnValue({
    data: materias,
  } as ReturnType<typeof catalogo.useMaterias>)
  const onConfirmar = vi.fn()
  render(
    <DialogoAgregarMateria abierto cargando={false} error={null} onConfirmar={onConfirmar} onCerrar={vi.fn()} />,
  )
  return onConfirmar
}

describe('DialogoAgregarMateria', () => {
  afterEach(() => vi.restoreAllMocks())

  it('oculta las materias no habilitadas para asesorías', () => {
    montar([
      crearMateria({ id: 1, nombre: 'Cálculo I' }),
      crearMateria({ id: 2, nombre: 'Álgebra', habilitada_asesorias: false }),
    ])

    expect(screen.getByRole('button', { name: 'Cálculo I' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Álgebra' })).not.toBeInTheDocument()
  })

  it('filtra por la búsqueda sin distinguir mayúsculas', () => {
    montar([crearMateria({ id: 1, nombre: 'Cálculo I' }), crearMateria({ id: 2, nombre: 'Física' })])

    fireEvent.change(screen.getByLabelText('Buscar materia'), { target: { value: 'fís' } })

    expect(screen.getByRole('button', { name: 'Física' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cálculo I' })).not.toBeInTheDocument()
  })

  it('mantiene Agregar deshabilitado hasta que hay una materia seleccionada', () => {
    const onConfirmar = montar([crearMateria({ id: 7, nombre: 'Física' })])

    expect(screen.getByRole('button', { name: 'Agregar' })).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Física' }))
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }))

    expect(onConfirmar).toHaveBeenCalledWith(7)
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/features/asesorias/components/DialogoCancelar.test.tsx src/features/asesorias/components/DialogoAgregarMateria.test.tsx`

Expected: FAIL.
- `DialogoCancelar` → `TestingLibraryElementError: Unable to find a label with the text of: /Motivo/`. Hoy el `<label>` envuelve al `<textarea>` pero también contiene el texto del propio label junto a otros nodos; el `getByLabelText` falla hasta que el campo tenga `id`/`htmlFor` explícitos (requisito de "Labels" del checklist del paso 7).
- `DialogoAgregarMateria` → los 3 casos fallan: `Unable to find a label with the text of: Buscar materia` (hoy el input solo tiene `placeholder`, que el paso 7 prohíbe como único label) y el orden de botones todavía no está garantizado por nada compartido.

- [ ] **Step 3: Migrar `DialogoCancelar`**

Reemplazar `frontend/src/features/asesorias/components/DialogoCancelar.tsx` completo por:

```tsx
import { useState } from 'react'

import { Dialogo } from '../../../components/ui/Dialogo'

interface DialogoCancelarProps {
  abierto: boolean
  cargando: boolean
  error: string | null
  onConfirmar: (motivo: string) => void
  onCerrar: () => void
}

export function DialogoCancelar({ abierto, cargando, error, onConfirmar, onCerrar }: DialogoCancelarProps) {
  const [motivo, setMotivo] = useState('')

  return (
    <Dialogo
      abierto={abierto}
      titulo="Cancelar asesoría"
      descripcion="Se notificará al alumno por correo. Esta acción no se puede deshacer."
      error={error}
      onCerrar={onCerrar}
      acciones={[
        {
          etiqueta: 'Confirmar cancelación',
          tono: 'peligro',
          cargando,
          onClick: () => onConfirmar(motivo),
        },
      ]}
    >
      <div className="flex flex-col gap-1">
        <label htmlFor="motivo-cancelacion" className="text-xs text-on-surface-variant">
          Motivo (opcional)
        </label>
        <textarea
          id="motivo-cancelacion"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          rows={3}
          className="foco-visible rounded-md border border-outline bg-transparent px-2 py-1.5 text-sm text-on-surface"
        />
      </div>
    </Dialogo>
  )
}
```

- [ ] **Step 4: Migrar `DialogoAgregarMateria`**

Reemplazar `frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx` completo por:

```tsx
import { useMemo, useState } from 'react'

import { Dialogo } from '../../../components/ui/Dialogo'
import { useMaterias } from '../../catalogo/api'

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
          {filtradas.map((materia) => (
            <li key={materia.id}>
              <button
                type="button"
                onClick={() => setSeleccionada(materia.id)}
                aria-pressed={seleccionada === materia.id}
                className={`foco-visible min-h-11 w-full rounded-md px-2 py-2 text-left text-sm ${
                  seleccionada === materia.id
                    ? 'bg-primary-container text-on-primary-container'
                    : 'text-on-surface hover:bg-surface-container-high'
                }`}
              >
                {materia.nombre}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </Dialogo>
  )
}
```

- [ ] **Step 5: Correr los tests y confirmar que pasan**

Run: `pnpm test src/features/asesorias/components/DialogoCancelar.test.tsx src/features/asesorias/components/DialogoAgregarMateria.test.tsx`

Expected: PASS — los 6 casos.

- [ ] **Step 6: Verificar que ya no queda Radix crudo en estos dos archivos**

Run:
```bash
grep -rn "@radix-ui/react-dialog" src/features/ || echo "SIN RADIX DIRECTO EN FEATURES"
```

Expected: todavía aparecen `DialogoNuevoBloque.tsx` y `DialogoBloqueActivo.tsx` (los migra la Task 5); **no** deben aparecer `DialogoCancelar.tsx` ni `DialogoAgregarMateria.tsx`.

- [ ] **Step 7: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde. `DetalleAsesoria.tsx` consume `DialogoCancelar` con las mismas props; no requiere cambios.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/asesorias/components/DialogoCancelar.tsx \
        frontend/src/features/asesorias/components/DialogoCancelar.test.tsx \
        frontend/src/features/asesorias/components/DialogoAgregarMateria.tsx \
        frontend/src/features/asesorias/components/DialogoAgregarMateria.test.tsx
git commit -s -m "[refactor][frontend] migrar los dialogos de una accion al Dialogo compartido" \
  -m "- DialogoCancelar y DialogoAgregarMateria dejan de montar Dialog.Root/
    Portal/Overlay/Content de Radix por su cuenta y componen
    components/ui/Dialogo; el orden de botones ya no se copia a mano.
- Checklist del paso 7 aplicado de paso: label explicito con htmlFor en el
    motivo y en la busqueda (el placeholder deja de ser el unico label),
    .foco-visible en textarea, input y filas seleccionables, y area de
    toque minima en las filas de materia.
- Tests de comportamiento nuevos para ambos: motivo que viaja al confirmar,
    filtrado por busqueda y por habilitada_asesorias, y Agregar bloqueado
    hasta que hay seleccion."
```

---

### Task 5: Migrar los diálogos restantes (`DialogoNuevoBloque`, `DialogoBloqueActivo`)

`DialogoNuevoBloque` ejercita la rama de fila con formulario; `DialogoBloqueActivo` es el primer consumidor real de la rama de columna, y su orden actual (Desactivar → Eliminar → Cerrar) ya coincide con la convención: la reversible arriba, la destructiva en medio, salir al final. Lo que cambia es que ahora eso lo garantiza el componente, no la buena suerte.

**Files:**
- Modify: `frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx`
- Modify: `frontend/src/features/asesorias/components/DialogoBloqueActivo.tsx`
- Test: `frontend/src/features/asesorias/components/DialogoNuevoBloque.test.tsx` (crear)
- Test: `frontend/src/features/asesorias/components/DialogoBloqueActivo.test.tsx` (crear)

**Interfaces:**
- Consumes: `Dialogo` (Task 3); tipos `FormatoAsesoria` y `Disponibilidad` de `api/types` (existentes).
- Produces: ambos conservan sus props actuales. La Task 10 (`MiHorario`) los monta tal cual.

- [ ] **Step 1: Escribir los tests — RED**

Crear `frontend/src/features/asesorias/components/DialogoNuevoBloque.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoNuevoBloque } from './DialogoNuevoBloque'

function montar() {
  const onConfirmar = vi.fn()
  render(
    <DialogoNuevoBloque
      abierto
      diaSemana={0}
      horaInicio="09:00:00"
      nombreDia="Lunes"
      cargando={false}
      error={null}
      onConfirmar={onConfirmar}
      onCerrar={vi.fn()}
    />,
  )
  return onConfirmar
}

describe('DialogoNuevoBloque', () => {
  it('pide la liga cuando el formato es virtual y la ubicación cuando es presencial', () => {
    montar()

    expect(screen.getByLabelText('Liga de la sesión')).toBeInTheDocument()
    expect(screen.queryByLabelText('Ubicación')).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Formato'), { target: { value: 'presencial' } })

    expect(screen.getByLabelText('Ubicación')).toBeInTheDocument()
    expect(screen.queryByLabelText('Liga de la sesión')).not.toBeInTheDocument()
  })

  it('confirma con el formato y los datos capturados', () => {
    const onConfirmar = montar()

    fireEvent.change(screen.getByLabelText('Formato'), { target: { value: 'presencial' } })
    fireEvent.change(screen.getByLabelText('Ubicación'), { target: { value: 'Salón O-221' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear' }))

    expect(onConfirmar).toHaveBeenCalledWith({
      formato: 'presencial',
      ubicacion: 'Salón O-221',
      liga_virtual: '',
    })
  })

  it('no renderiza nada sin celda seleccionada', () => {
    render(
      <DialogoNuevoBloque
        abierto
        diaSemana={null}
        horaInicio={null}
        nombreDia=""
        cargando={false}
        error={null}
        onConfirmar={vi.fn()}
        onCerrar={vi.fn()}
      />,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
```

Crear `frontend/src/features/asesorias/components/DialogoBloqueActivo.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoBloqueActivo } from './DialogoBloqueActivo'
import type { Disponibilidad } from '../../../api/types'

const BLOQUE: Disponibilidad = {
  id: 1,
  registro: 1,
  dia_semana: 0,
  hora_inicio: '09:00:00',
  formato: 'virtual',
  ubicacion: '',
  liga_virtual: 'https://meet.example/x',
  activa: true,
}

function montar() {
  const onDesactivar = vi.fn()
  const onEliminar = vi.fn()
  const onCerrar = vi.fn()
  render(
    <DialogoBloqueActivo
      abierto
      disponibilidad={BLOQUE}
      cargando={false}
      onDesactivar={onDesactivar}
      onEliminar={onEliminar}
      onCerrar={onCerrar}
    />,
  )
  return { onDesactivar, onEliminar, onCerrar }
}

describe('DialogoBloqueActivo', () => {
  it('presenta las 3 acciones en el orden de la convención', () => {
    montar()

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'Desactivar',
      'Eliminar',
      'Volver',
    ])
  })

  it('la acción destructiva va en contorno, no rellena', () => {
    montar()

    expect(screen.getByRole('button', { name: 'Eliminar' })).toHaveClass('bg-transparent')
  })

  it('cada botón dispara su callback', () => {
    const { onDesactivar, onEliminar, onCerrar } = montar()

    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Volver' }))

    expect(onDesactivar).toHaveBeenCalledTimes(1)
    expect(onEliminar).toHaveBeenCalledTimes(1)
    expect(onCerrar).toHaveBeenCalledTimes(1)
  })

  it('no renderiza nada sin disponibilidad', () => {
    render(
      <DialogoBloqueActivo
        abierto
        disponibilidad={null}
        cargando={false}
        onDesactivar={vi.fn()}
        onEliminar={vi.fn()}
        onCerrar={vi.fn()}
      />,
    )

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/features/asesorias/components/DialogoNuevoBloque.test.tsx src/features/asesorias/components/DialogoBloqueActivo.test.tsx`

Expected: FAIL.
- `DialogoNuevoBloque` → `Unable to find a label with the text of: Formato` en los 2 primeros casos (hoy el `<label>` envuelve al `<select>` sin `htmlFor`, y su texto convive con el del control). El tercero (`sin celda seleccionada`) pasa ya: es una regresión que se protege, no un cambio.
- `DialogoBloqueActivo` → el primer caso falla con `['Desactivar', 'Eliminar', 'Cerrar']` (la etiqueta de salir), y el segundo con `Expected element to have class bg-transparent` (hoy Eliminar es `variante="peligro"`, rellena).

- [ ] **Step 3: Migrar `DialogoNuevoBloque`**

Reemplazar `frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx` completo por:

```tsx
import { useState } from 'react'

import type { FormatoAsesoria } from '../../../api/types'
import { Dialogo } from '../../../components/ui/Dialogo'

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

const CLASE_CAMPO =
  'foco-visible h-10 rounded-md border border-outline bg-transparent px-2 text-sm text-on-surface'

export function DialogoNuevoBloque({
  abierto,
  diaSemana,
  horaInicio,
  nombreDia,
  cargando,
  error,
  onConfirmar,
  onCerrar,
}: DialogoNuevoBloqueProps) {
  const [formato, setFormato] = useState<FormatoAsesoria>('virtual')
  const [ubicacion, setUbicacion] = useState('')
  const [ligaVirtual, setLigaVirtual] = useState('')

  if (diaSemana === null || horaInicio === null) return null

  return (
    <Dialogo
      abierto={abierto}
      titulo={`Nuevo bloque — ${nombreDia} ${horaInicio.slice(0, 5)}`}
      descripcion="Bloque recurrente de 30 minutos cada semana."
      error={error}
      etiquetaSalir="Cancelar"
      onCerrar={onCerrar}
      acciones={[
        {
          etiqueta: 'Crear',
          cargando,
          onClick: () => onConfirmar({ formato, ubicacion, liga_virtual: ligaVirtual }),
        },
      ]}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label htmlFor="formato-bloque" className="text-xs text-on-surface-variant">
            Formato
          </label>
          <select
            id="formato-bloque"
            value={formato}
            onChange={(e) => setFormato(e.target.value as FormatoAsesoria)}
            className={CLASE_CAMPO}
          >
            <option value="virtual">Virtual</option>
            <option value="presencial">Presencial</option>
          </select>
        </div>

        {formato === 'virtual' ? (
          <div className="flex flex-col gap-1">
            <label htmlFor="liga-bloque" className="text-xs text-on-surface-variant">
              Liga de la sesión
            </label>
            <input
              id="liga-bloque"
              type="url"
              value={ligaVirtual}
              onChange={(e) => setLigaVirtual(e.target.value)}
              required
              className={CLASE_CAMPO}
            />
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            <label htmlFor="ubicacion-bloque" className="text-xs text-on-surface-variant">
              Ubicación
            </label>
            <input
              id="ubicacion-bloque"
              type="text"
              value={ubicacion}
              onChange={(e) => setUbicacion(e.target.value)}
              required
              className={CLASE_CAMPO}
            />
          </div>
        )}
      </div>
    </Dialogo>
  )
}
```

- [ ] **Step 4: Migrar `DialogoBloqueActivo`**

Reemplazar `frontend/src/features/asesorias/components/DialogoBloqueActivo.tsx` completo por:

```tsx
import type { Disponibilidad } from '../../../api/types'
import { Dialogo } from '../../../components/ui/Dialogo'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

interface DialogoBloqueActivoProps {
  abierto: boolean
  disponibilidad: Disponibilidad | null
  cargando: boolean
  onDesactivar: () => void
  onEliminar: () => void
  onCerrar: () => void
}

export function DialogoBloqueActivo({
  abierto,
  disponibilidad,
  cargando,
  onDesactivar,
  onEliminar,
  onCerrar,
}: DialogoBloqueActivoProps) {
  if (!disponibilidad) return null

  return (
    <Dialogo
      abierto={abierto}
      titulo={`${DIAS[disponibilidad.dia_semana]} ${disponibilidad.hora_inicio.slice(0, 5)} — ${disponibilidad.formato}`}
      descripcion="¿Qué quieres hacer con este bloque?"
      onCerrar={onCerrar}
      acciones={[
        { etiqueta: 'Desactivar', cargando, onClick: onDesactivar },
        { etiqueta: 'Eliminar', tono: 'peligro', cargando, onClick: onEliminar },
      ]}
    />
  )
}
```

- [ ] **Step 5: Correr los tests y confirmar que pasan**

Run: `pnpm test src/features/asesorias/components/DialogoNuevoBloque.test.tsx src/features/asesorias/components/DialogoBloqueActivo.test.tsx`

Expected: PASS — los 7 casos.

- [ ] **Step 6: Confirmar que ninguna feature importa Radix directo**

Run:
```bash
grep -rn "@radix-ui/react-dialog" src/features/ || echo "SIN RADIX DIRECTO EN FEATURES"
```

Expected: imprime `SIN RADIX DIRECTO EN FEATURES`. Este es el objetivo entero de ADR 0020 para diálogos: la duplicación de wiring desapareció.

- [ ] **Step 7: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde. `DisponibilidadAsesor.tsx` sigue montando estos dos diálogos con las mismas props (se retira en la Task 11).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/asesorias/components/DialogoNuevoBloque.tsx \
        frontend/src/features/asesorias/components/DialogoNuevoBloque.test.tsx \
        frontend/src/features/asesorias/components/DialogoBloqueActivo.tsx \
        frontend/src/features/asesorias/components/DialogoBloqueActivo.test.tsx
git commit -s -m "[refactor][frontend] migrar los dialogos restantes de asesorias al Dialogo compartido" \
  -m "- DialogoNuevoBloque y DialogoBloqueActivo dejan de montar Radix
    directo: ninguna feature importa ya @radix-ui/react-dialog.
- DialogoBloqueActivo pasa a ser el primer consumidor de la rama de 3
    acciones: Eliminar deja de ir rellena y pasa a contorno, y el boton de
    salir toma la etiqueta y el estilo de texto plano que fija el paso 3.
- Labels explicitos con htmlFor en formato/liga/ubicacion y .foco-visible
    en cada control (checklist del paso 7).
- Tests de comportamiento: el formato conmuta el campo requerido y el
    payload confirmado, y el orden de los 3 botones queda protegido."
```

---

### Task 6: Primitivo `tabs.tsx` de shadcn y migración de `SesionesAsesor`

"Mi horario" (Task 10) necesita tabs. La spec del paso 6 fija que use el `tabs.tsx` de shadcn desde el inicio. `SesionesAsesor` es hoy el único otro consumidor de Radix crudo y se migra en el mismo movimiento — su test existente protege el comportamiento (ver Decisión 6 de la sección final; si el checkpoint la rechaza, borra el Step 5 y su parte del commit, el resto del task no cambia).

**Files:**
- Create: `frontend/src/components/ui/tabs.tsx`
- Test: `frontend/src/components/ui/tabs.test.tsx`
- Modify: `frontend/src/features/asesorias/screens/SesionesAsesor.tsx`

**Interfaces:**
- Consumes: `@/lib/utils` (Task 1); `@radix-ui/react-tabs` 1.1.21 (ya instalado).
- Produces: `@/components/ui/tabs` exporta `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`. El estilo por default es el subrayado que ya usa la app; los consumidores pueden agregar clases vía `className`. La Task 10 lo consume.

- [ ] **Step 1: Escribir el test del primitivo — RED**

Crear `frontend/src/components/ui/tabs.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs'

function montar() {
  render(
    <Tabs defaultValue="lun">
      <TabsList>
        <TabsTrigger value="lun">Lun</TabsTrigger>
        <TabsTrigger value="mar">Mar</TabsTrigger>
      </TabsList>
      <TabsContent value="lun">Contenido de lunes</TabsContent>
      <TabsContent value="mar">Contenido de martes</TabsContent>
    </Tabs>,
  )
}

describe('tabs', () => {
  it('muestra el contenido de la pestaña por default', () => {
    montar()

    expect(screen.getByText('Contenido de lunes')).toBeInTheDocument()
    expect(screen.queryByText('Contenido de martes')).not.toBeInTheDocument()
  })

  it('cambia de panel al seleccionar otra pestaña', () => {
    montar()

    fireEvent.click(screen.getByRole('tab', { name: 'Mar' }))

    expect(screen.getByText('Contenido de martes')).toBeInTheDocument()
    expect(screen.queryByText('Contenido de lunes')).not.toBeInTheDocument()
  })

  it('cada pestaña lleva el estado de foco visible del paso 7', () => {
    montar()

    for (const tab of screen.getAllByRole('tab')) {
      expect(tab).toHaveClass('foco-visible')
    }
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pnpm test src/components/ui/tabs.test.tsx`

Expected: FAIL — `Failed to resolve import "./tabs"`.

- [ ] **Step 3: Generar el componente con el CLI**

Run:
```bash
pnpm dlx shadcn@latest add tabs --yes
```

Escribe `src/components/ui/tabs.tsx` con el estilo "pill" de shadcn (`bg-muted`, `data-[state=active]:bg-background`). El Step 4 lo cambia al subrayado que ya usa la app.

Si no hay red, salta al Step 4: el archivo está completo abajo.

- [ ] **Step 4: Curar el archivo generado**

Reemplazar `frontend/src/components/ui/tabs.tsx` completo por:

```tsx
import * as React from 'react'
import * as TabsPrimitive from '@radix-ui/react-tabs'

import { cn } from '@/lib/utils'

/**
 * Primitivo `tabs` de shadcn/ui (ADR 0020), curado para este proyecto.
 *
 * El estilo por default es el subrayado que la app ya usaba en
 * `SesionesAsesor` (Próximas/Historial), no el "pill" con `bg-muted` que
 * trae shadcn: es el lenguaje visual establecido y evita introducir un
 * segundo patrón de pestañas. Cada consumidor puede afinar el layout con
 * `className` (p. ej. el espaciado de los 7 días en "Mi horario").
 *
 * La navegación con flechas, Home/End y el manejo de foco los resuelve
 * Radix; no se interceptan (checklist del paso 7).
 */

function Tabs({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return <TabsPrimitive.Root data-slot="tabs" className={cn('flex flex-col', className)} {...props} />
}

function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn('mb-4 flex gap-4 border-b border-outline-variant text-sm', className)}
      {...props}
    />
  )
}

function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        'foco-visible min-h-11 px-1 pb-2 text-on-surface-variant',
        'data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:text-primary',
        className,
      )}
      {...props}
    />
  )
}

function TabsContent({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return <TabsPrimitive.Content data-slot="tabs-content" className={cn('outline-none', className)} {...props} />
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
```

- [ ] **Step 5: Migrar `SesionesAsesor` al primitivo**

En `frontend/src/features/asesorias/screens/SesionesAsesor.tsx`, reemplazar el import:

```tsx
import * as Tabs from '@radix-ui/react-tabs'
```

por:

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
```

y reemplazar el bloque JSX que va de `<Tabs.Root defaultValue="proximas">` hasta `</Tabs.Root>` (líneas 27-49) por:

```tsx
      <Tabs defaultValue="proximas">
        <TabsList>
          <TabsTrigger value="proximas">Próximas</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="proximas">
          <ListaAsesorias asesorias={proximas(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="No tienes asesorías próximas." />
        </TabsContent>
        <TabsContent value="historial">
          <ListaAsesorias asesorias={historial(asesorias)} cargando={isPending} nombreMateria={(id) => mapaMaterias.get(id)?.nombre} vacio="Aún no hay historial." />
        </TabsContent>
      </Tabs>
```

Las clases de `TabsList`/`TabsTrigger` que estaban inline ahora viven en el primitivo, idénticas — el resultado visual no cambia.

- [ ] **Step 6: Correr los tests y confirmar que pasan**

Run: `pnpm test src/components/ui/tabs.test.tsx src/features/asesorias/screens/SesionesAsesor.test.tsx`

Expected: PASS — los 3 casos del primitivo y el caso existente de `SesionesAsesor` (que sigue verde sin tocarlo: es la evidencia de que la migración no cambió el comportamiento).

- [ ] **Step 7: Confirmar que no queda Radix de tabs en features y correr todo**

Run:
```bash
grep -rn "@radix-ui/react-tabs" src/features/ || echo "SIN RADIX DIRECTO EN FEATURES"
pnpm test && pnpm lint && pnpm build
```

Expected: imprime `SIN RADIX DIRECTO EN FEATURES` y los tres comandos en verde.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/ui/tabs.tsx frontend/src/components/ui/tabs.test.tsx \
        frontend/src/features/asesorias/screens/SesionesAsesor.tsx
git commit -s -m "[feat][frontend] agregar el primitivo tabs de shadcn/ui y migrar SesionesAsesor" \
  -m "- components/ui/tabs.tsx generado con el CLI y curado: conserva el
    estilo de subrayado que la app ya usaba en vez del pill de shadcn, para
    no introducir un segundo patron de pestanas, y agrega .foco-visible.
- SesionesAsesor deja de importar @radix-ui/react-tabs directo; su test
    existente pasa sin cambios, que es la evidencia de que la migracion no
    altero el comportamiento.
- El primitivo queda listo para Mi horario, que segun la spec del paso 6
    debe usarlo desde el inicio en vez de una implementacion a mano."
```

---

### Task 7: Cimientos compartidos de las dos pantallas nuevas

Piezas que "Mis materias" y "Mi horario" necesitan las dos, extraídas antes de escribir cualquiera de ellas para no duplicarlas: el helper de errores de API (hoy copiado literalmente en dos pantallas), el bloque de "aún no tienes registro de asesor" (hoy embebido en `DisponibilidadAsesor`), el selector del registro del semestre en curso, y los íconos de formato/basura.

**Files:**
- Create: `frontend/src/api/errores.ts`
- Test: `frontend/src/api/errores.test.ts`
- Create: `frontend/src/components/icons/UiIcons.tsx`
- Create: `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx`
- Test: `frontend/src/features/asesorias/components/SinRegistroAsesor.test.tsx`
- Modify: `frontend/src/features/asesorias/api.ts`
- Modify: `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx:17-24`

**Interfaces:**
- Consumes: `ApiError` de `api/client` (existente); `useMisRegistros`, `useCrearRegistro` de `features/asesorias/api` (existentes); `semestreActual` de `features/asesorias/logica` (existente); `Boton` y `Retroalimentacion` (existentes, sin modificar).
- Produces:
  - `api/errores.ts` → `primerMensajeDeError(error: unknown): string`.
  - `components/icons/UiIcons.tsx` → `IconVirtual`, `IconPresencial`, `IconBasura`, todos con la firma `({ className }: IconProps)` de `ServiceIcons.tsx`.
  - `features/asesorias/api.ts` → `useRegistroDelSemestre(semestre?: string): { registro: RegistroAsesor | null; cargando: boolean }`.
  - `features/asesorias/components/SinRegistroAsesor.tsx` → `SinRegistroAsesor({ titulo }: { titulo: string })`.

- [ ] **Step 1: Escribir los tests — RED**

Crear `frontend/src/api/errores.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { ApiError } from './client'
import { primerMensajeDeError } from './errores'

describe('primerMensajeDeError', () => {
  it('toma el primer elemento cuando detail es una lista', () => {
    const error = new ApiError(400, { detail: ['Ya tienes un bloque en ese horario.', 'Otro.'] })
    expect(primerMensajeDeError(error)).toBe('Ya tienes un bloque en ese horario.')
  })

  it('acepta detail como cadena', () => {
    expect(primerMensajeDeError(new ApiError(403, { detail: 'No autorizado.' }))).toBe('No autorizado.')
  })

  it('cae a un mensaje genérico con un cuerpo desconocido', () => {
    expect(primerMensajeDeError(new ApiError(500, null))).toBe('Ocurrió un error inesperado.')
  })

  it('cae a un mensaje genérico con algo que no es un ApiError', () => {
    expect(primerMensajeDeError(new Error('boom'))).toBe('Ocurrió un error inesperado.')
  })
})
```

Crear `frontend/src/features/asesorias/components/SinRegistroAsesor.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SinRegistroAsesor } from './SinRegistroAsesor'
import * as api from '../api'

function montar() {
  const mutate = vi.fn()
  vi.spyOn(api, 'useCrearRegistro').mockReturnValue({
    mutate,
    isPending: false,
  } as unknown as ReturnType<typeof api.useCrearRegistro>)

  render(
    <MemoryRouter>
      <SinRegistroAsesor titulo="Mis materias" />
    </MemoryRouter>,
  )
  return mutate
}

describe('SinRegistroAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('propone el semestre en curso y lo deja editar antes de registrar', () => {
    const mutate = montar()
    const campo = screen.getByLabelText('Semestre (AAAAN)')

    expect(campo).toHaveValue(expect.any(String))

    fireEvent.change(campo, { target: { value: '20271' } })
    fireEvent.click(screen.getByRole('button', { name: /Registrar semestre 20271/ }))

    expect(mutate).toHaveBeenCalledWith('20271', expect.anything())
  })

  it('anuncia el título de la pantalla desde la que se llegó', () => {
    montar()
    expect(screen.getByRole('heading', { name: 'Mis materias' })).toBeInTheDocument()
  })
})
```

> Nota para quien implementa: `expect(campo).toHaveValue(expect.any(String))` solo comprueba que el campo trae un valor precargado; el valor exacto depende de la fecha del sistema y ya está cubierto por los tests de `semestreActual` en `logica.test.ts`.

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/api/errores.test.ts src/features/asesorias/components/SinRegistroAsesor.test.tsx`

Expected: FAIL — `Failed to resolve import "./errores"` y `Failed to resolve import "./SinRegistroAsesor"`.

- [ ] **Step 3: Escribir `api/errores.ts`**

Crear `frontend/src/api/errores.ts`:

```ts
import { ApiError } from './client'

/**
 * Primer mensaje legible de un error de la API.
 *
 * El backend traduce las reglas de negocio que viven en el modelo a
 * `400 {"detail": ["mensaje"]}` — una lista, aun con un solo mensaje — y los
 * errores de permiso a `{"detail": "mensaje"}`. Esta función absorbe las dos
 * formas y garantiza que la UI siempre tenga algo que mostrar.
 */
export function primerMensajeDeError(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: string[] | string } | null
    if (Array.isArray(body?.detail) && body.detail.length > 0) return body.detail[0]
    if (typeof body?.detail === 'string') return body.detail
  }
  return 'Ocurrió un error inesperado.'
}
```

- [ ] **Step 4: Usar el helper compartido en `DetalleAsesoria`**

En `frontend/src/features/asesorias/screens/DetalleAsesoria.tsx`: borrar la función local `primerMensajeDeError` (líneas 17-24), quitar el import de `ApiError` (línea 11, ya no se usa ahí) y agregar junto a los demás imports:

```tsx
import { primerMensajeDeError } from '../../../api/errores'
```

Las cuatro llamadas existentes no cambian.

- [ ] **Step 5: Escribir los íconos**

Crear `frontend/src/components/icons/UiIcons.tsx`:

```tsx
import type { ReactNode, SVGProps } from 'react'

export interface IconProps {
  className?: string
}

/**
 * Íconos de interfaz (no de servicio). `ServiceIcons.tsx` usa `viewBox` 48 y
 * trazo 2.5 porque son ilustraciones de tarjeta; estos son íconos de control
 * a 24px con trazo 2, la métrica que fija la spec del paso 3.
 *
 * Se dibujan a mano, sin librería de íconos (ADR 0014).
 */
function IconBase({ children, ...props }: SVGProps<SVGSVGElement> & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...props}
    >
      {children}
    </svg>
  )
}

/** Monitor — formato virtual. Mismo SVG en "Mi horario" y en el detalle. */
export function IconVirtual({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M8 20h8" />
      <path d="M12 16v4" />
    </IconBase>
  )
}

/** Pin — formato presencial. Mismo SVG en "Mi horario" y en el detalle. */
export function IconPresencial({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <circle cx="12" cy="10" r="3" />
      <path d="M12 21c-4-4.5-7-8-7-11a7 7 0 0 1 14 0c0 3-3 6.5-7 11Z" />
    </IconBase>
  )
}

/** Basura — quitar un elemento de una lista. */
export function IconBasura({ className }: IconProps) {
  return (
    <IconBase className={className}>
      <path d="M4 7h16" />
      <path d="M10 4h4" />
      <path d="M6 7l1 13h10l1-13" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </IconBase>
  )
}
```

- [ ] **Step 6: Agregar `useRegistroDelSemestre`**

En `frontend/src/features/asesorias/api.ts`, agregar el import al inicio del archivo:

```ts
import { semestreActual } from './logica'
```

y agregar después de `useMisRegistros` (línea 10):

```ts
/**
 * El registro de asesor del semestre pedido (el en curso por default).
 * Las dos pantallas de disponibilidad ("Mis materias" y "Mi horario") lo
 * necesitan igual, así que la búsqueda vive aquí y no en cada una.
 */
export function useRegistroDelSemestre(semestre: string = semestreActual()) {
  const { data: registros, isPending } = useMisRegistros()
  return {
    registro: registros?.find((r) => r.semestre === semestre) ?? null,
    cargando: isPending,
  }
}
```

- [ ] **Step 7: Escribir `SinRegistroAsesor`**

Crear `frontend/src/features/asesorias/components/SinRegistroAsesor.tsx`:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Boton } from '../../../components/ui/Boton'
import { Retroalimentacion, useRetroalimentacion } from '../../../components/ui/Retroalimentacion'
import { useCrearRegistro } from '../api'
import { semestreActual } from '../logica'

/**
 * Pantalla de "todavía no tienes registro de asesor para este semestre".
 * Estado compartido por "Mis materias" y "Mi horario": sin registro no hay
 * ni materias ni horario que mostrar.
 */
export function SinRegistroAsesor({ titulo }: { titulo: string }) {
  const navigate = useNavigate()
  const crearRegistro = useCrearRegistro()
  const { mensaje, mostrar } = useRetroalimentacion()
  const [semestre, setSemestre] = useState(semestreActual())

  return (
    <main className="flex min-h-svh flex-col gap-4 px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/asesorias')}
        className="foco-visible w-fit rounded-md text-sm text-primary"
      >
        ← Volver a Asesorías
      </button>
      <h1 className="text-lg font-semibold text-on-background">{titulo}</h1>
      <p className="text-sm text-on-surface-variant">
        Aún no tienes un registro de asesor para este semestre.
      </p>

      <div className="flex flex-col gap-1">
        <label htmlFor="semestre-registro" className="text-xs text-on-surface-variant">
          Semestre (AAAAN)
        </label>
        <input
          id="semestre-registro"
          type="text"
          value={semestre}
          onChange={(e) => setSemestre(e.target.value)}
          className="foco-visible h-11 w-32 rounded-md border border-outline bg-transparent px-3 text-sm text-on-surface"
        />
      </div>

      <Boton
        type="button"
        cargando={crearRegistro.isPending}
        onClick={() => crearRegistro.mutate(semestre, { onSuccess: () => mostrar('Registro creado') })}
        className="w-fit px-6"
      >
        Registrar semestre {semestre}
      </Boton>

      <Retroalimentacion mensaje={mensaje} />
    </main>
  )
}
```

- [ ] **Step 8: Correr los tests y confirmar que pasan**

Run: `pnpm test src/api/errores.test.ts src/features/asesorias/components/SinRegistroAsesor.test.tsx`

Expected: PASS — los 6 casos.

- [ ] **Step 9: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde. `DetalleAsesoria` sigue funcionando con el helper importado.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/api/errores.ts frontend/src/api/errores.test.ts \
        frontend/src/components/icons/UiIcons.tsx \
        frontend/src/features/asesorias/components/SinRegistroAsesor.tsx \
        frontend/src/features/asesorias/components/SinRegistroAsesor.test.tsx \
        frontend/src/features/asesorias/api.ts \
        frontend/src/features/asesorias/screens/DetalleAsesoria.tsx
git commit -s -m "[refactor][frontend] extraer los cimientos compartidos de las pantallas de disponibilidad" \
  -m "- api/errores.ts: primerMensajeDeError deja de estar copiado literal en
    DetalleAsesoria y DisponibilidadAsesor; gana tests de las dos formas de
    detail que produce el backend (lista y cadena).
- components/icons/UiIcons.tsx: monitor, pin y basura dibujados a mano
    (ADR 0014, sin libreria de iconos), a 24px/trazo 2 como fija el paso 3.
    Monitor y pin son los mismos SVG que usara el detalle de asesoria.
- SinRegistroAsesor: el estado de 'aun no tienes registro' sale de
    DisponibilidadAsesor a un componente propio, porque las dos pantallas
    nuevas lo comparten. useRegistroDelSemestre hace lo mismo con la
    busqueda del registro del semestre en curso."
```

---

### Task 8: Pantalla "Mis materias"

Primera de las dos pantallas nuevas del [paso 3](../specs/2026-08-04-revision-vistas-asesorias-design.md). Lista de filas (no chips), truncamiento a una línea con `title` y con el nombre completo accesible al tocar, botón de quitar con área de toque real, y confirmación de 2 acciones con el copy exacto de la spec.

**Files:**
- Create: `frontend/src/features/asesorias/screens/MisMaterias.tsx`
- Test: `frontend/src/features/asesorias/screens/MisMaterias.test.tsx`
- Create: `frontend/src/features/asesorias/components/DialogoQuitarMateria.tsx`
- Modify: `frontend/src/features/asesorias/api.ts`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `useRegistroDelSemestre`, `SinRegistroAsesor`, `primerMensajeDeError`, `IconBasura` (Task 7); `Dialogo` (Task 3); `DialogoAgregarMateria` (Task 4); `useMapaMaterias` (existente); `useAgregarMateria` (existente); `RutaDeAsesor` (existente).
- Produces:
  - `features/asesorias/api.ts` → `useQuitarMateria(registroId: number)` — `mutate(materiaId: number)`.
  - `DialogoQuitarMateria` — props `{ abierto: boolean; nombreMateria: string; cargando: boolean; error: string | null; onConfirmar: () => void; onCerrar: () => void }`.
  - Ruta `/asesorias/materias` → `MisMaterias`.

- [ ] **Step 1: Escribir el test de la pantalla — RED**

Crear `frontend/src/features/asesorias/screens/MisMaterias.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MisMaterias } from './MisMaterias'
import * as api from '../api'
import * as catalogo from '../../catalogo/api'
import type { Materia, RegistroAsesor } from '../../../api/types'

const NOMBRE_LARGO = 'Aplicación de las Ciencias de la Tierra en la Vigilancia de Ensayos Nucleares'

const REGISTRO: RegistroAsesor = { id: 3, semestre: '20262', materias: [1, 2] }

function materia(id: number, nombre: string): Materia {
  return { id, clave: `000${id}`, nombre, carrera: 1, nivel: null, plan: 1, habilitada_asesorias: true }
}

function montar() {
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: REGISTRO, cargando: false })
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([
      [1, materia(1, NOMBRE_LARGO)],
      [2, materia(2, 'Física')],
    ]),
  )
  const quitar = vi.fn()
  vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
    mutate: quitar,
    isPending: false,
  } as unknown as ReturnType<typeof api.useQuitarMateria>)
  vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof api.useAgregarMateria>)

  render(
    <MemoryRouter>
      <MisMaterias />
    </MemoryRouter>,
  )
  return quitar
}

describe('MisMaterias', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista las materias del registro con el nombre completo en title', () => {
    montar()

    const fila = screen.getByRole('button', { name: NOMBRE_LARGO })
    expect(fila).toHaveAttribute('title', NOMBRE_LARGO)
    expect(fila).toHaveClass('truncate')
  })

  it('al tocar la fila deja de truncar, para que el nombre completo sea accesible en móvil', () => {
    montar()

    const fila = screen.getByRole('button', { name: NOMBRE_LARGO })
    fireEvent.click(fila)

    expect(fila).not.toHaveClass('truncate')
  })

  it('quitar pide confirmación con el copy de la spec y luego llama al endpoint', () => {
    const quitar = montar()

    fireEvent.click(screen.getByRole('button', { name: 'Quitar Física' }))

    expect(
      screen.getByText(
        'Ya no aparecerás como asesor de esta materia en búsquedas de alumnos. Las asesorías ya agendadas no se cancelan.',
      ),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('button').map((b) => b.textContent)).toContain('Quitar')

    fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))

    expect(quitar).toHaveBeenCalledWith(2, expect.anything())
  })

  it('sin materias muestra el estado vacío', () => {
    vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({
      registro: { ...REGISTRO, materias: [] },
      cargando: false,
    })
    vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(new Map())
    vi.spyOn(api, 'useQuitarMateria').mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof api.useQuitarMateria>)
    vi.spyOn(api, 'useAgregarMateria').mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof api.useAgregarMateria>)

    render(
      <MemoryRouter>
        <MisMaterias />
      </MemoryRouter>,
    )

    expect(screen.getByText('Todavía no impartes ninguna materia este semestre.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pnpm test src/features/asesorias/screens/MisMaterias.test.tsx`

Expected: FAIL — `Failed to resolve import "./MisMaterias"` en los 4 casos.

- [ ] **Step 3: Agregar el hook de quitar materia**

En `frontend/src/features/asesorias/api.ts`, agregar después de `useAgregarMateria`:

```ts
/**
 * Quita una materia del registro del asesor.
 *
 * Contrato definido en la task 8 del plan de backend
 * (`docs/superpowers/plans/2026-08-04-login-oauth-backend.md`): es POST y no
 * DELETE para no habilitar el método DELETE en un viewset que lo excluye a
 * propósito. Ese endpoint todavía no existe en la rama de backend actual.
 */
export function useQuitarMateria(registroId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (materiaId: number) =>
      apiPost<RegistroAsesor>(`/api/asesorias/registros/${registroId}/materias/quitar/`, {
        materia_id: materiaId,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['registros'] }),
  })
}
```

- [ ] **Step 4: Escribir el diálogo de confirmación**

Crear `frontend/src/features/asesorias/components/DialogoQuitarMateria.tsx`:

```tsx
import { Dialogo } from '../../../components/ui/Dialogo'

interface DialogoQuitarMateriaProps {
  abierto: boolean
  nombreMateria: string
  cargando: boolean
  error: string | null
  onConfirmar: () => void
  onCerrar: () => void
}

export function DialogoQuitarMateria({
  abierto,
  nombreMateria,
  cargando,
  error,
  onConfirmar,
  onCerrar,
}: DialogoQuitarMateriaProps) {
  return (
    <Dialogo
      abierto={abierto}
      titulo={`Quitar ${nombreMateria}`}
      descripcion="Ya no aparecerás como asesor de esta materia en búsquedas de alumnos. Las asesorías ya agendadas no se cancelan."
      error={error}
      etiquetaSalir="Cancelar"
      onCerrar={onCerrar}
      acciones={[{ etiqueta: 'Quitar', tono: 'peligro', cargando, onClick: onConfirmar }]}
    />
  )
}
```

- [ ] **Step 5: Escribir la pantalla**

Crear `frontend/src/features/asesorias/screens/MisMaterias.tsx`:

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

export function MisMaterias() {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()
  const { registro, cargando } = useRegistroDelSemestre()
  const mapaMaterias = useMapaMaterias()

  const agregarMateria = useAgregarMateria(registro?.id ?? 0)
  const quitarMateria = useQuitarMateria(registro?.id ?? 0)

  const [dialogoAgregarAbierto, setDialogoAgregarAbierto] = useState(false)
  const [errorAgregar, setErrorAgregar] = useState<string | null>(null)
  const [materiaAQuitar, setMateriaAQuitar] = useState<number | null>(null)
  const [errorQuitar, setErrorQuitar] = useState<string | null>(null)
  const [expandida, setExpandida] = useState<number | null>(null)

  if (cargando) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!registro) {
    return <SinRegistroAsesor titulo="Mis materias" />
  }

  const nombreDe = (id: number) => mapaMaterias.get(id)?.nombre ?? `Materia #${id}`

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

      <p className="text-xs text-on-surface-variant">Semestre {registro.semestre}</p>

      {registro.materias.length === 0 ? (
        <p className="text-sm text-on-surface-variant">
          Todavía no impartes ninguna materia este semestre.
        </p>
      ) : (
        <ul className="flex flex-col">
          {registro.materias.map((id) => (
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
            </li>
          ))}
        </ul>
      )}

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

- [ ] **Step 6: Registrar la ruta**

En `frontend/src/App.tsx`, agregar el import:

```tsx
import { MisMaterias } from './features/asesorias/screens/MisMaterias'
```

y agregar la ruta antes de la ruta `/asesorias/:id` (el orden importa: `:id` es un comodín que capturaría `materias`):

```tsx
        <Route
          path="/asesorias/materias"
          element={
            <RutaDeAsesor>
              <MisMaterias />
            </RutaDeAsesor>
          }
        />
```

- [ ] **Step 7: Correr el test y confirmar que pasa**

Run: `pnpm test src/features/asesorias/screens/MisMaterias.test.tsx`

Expected: PASS — los 4 casos.

- [ ] **Step 8: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/features/asesorias/screens/MisMaterias.tsx \
        frontend/src/features/asesorias/screens/MisMaterias.test.tsx \
        frontend/src/features/asesorias/components/DialogoQuitarMateria.tsx \
        frontend/src/features/asesorias/api.ts frontend/src/App.tsx
git commit -s -m "[feat][frontend] agregar la pantalla Mis materias" \
  -m "- Primera mitad del rediseno de Disponibilidad (paso 3): materias como
    lista de filas, no chips. Cada fila trunca a una linea con ellipsis y
    lleva el nombre completo en title; al tocarla se expande, para que el
    nombre completo tambien sea accesible sin hover en movil.
- Boton de quitar de 44x44px con aria-label propio, en vez de una 'x'
    diminuta sobre un chip.
- DialogoQuitarMateria compone el Dialogo compartido: 2 acciones en fila
    con el copy exacto de la spec.
- useQuitarMateria contra POST /registros/{id}/materias/quitar/, el
    contrato que fija la task 8 del plan de backend (aun sin implementar en
    dev-backend: esta accion falla en runtime hasta entonces)."
```

---

### Task 9: Núcleo de lógica y datos de "Mi horario"

Todo lo que "Mi horario" necesita y se puede probar sin renderizar: las funciones puras de slots y el diálogo de 3 acciones, más los dos hooks de la superficie nueva de backend. Separado de la pantalla para que la lógica de horario tenga tests directos y rápidos, como ya hace `logica.test.ts` con el resto del feature.

**Files:**
- Modify: `frontend/src/features/asesorias/logica.ts`
- Modify: `frontend/src/features/asesorias/logica.test.ts`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/features/asesorias/api.ts`
- Create: `frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.tsx`
- Test: `frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.test.tsx`

**Interfaces:**
- Consumes: `Disponibilidad` de `api/types`; `claveSlot` de `logica.ts` (existente); `Dialogo` (Task 3); `apiGet`/`apiPost` de `api/client`.
- Produces:
  - `logica.ts` → `horasDelDia(): string[]` (28 entradas, `'07:00:00'`…`'20:30:00'`); `SlotHorario = { hora: string; clave: string; disponibilidad: Disponibilidad | null; activo: boolean }`; `slotsDelDia(diaSemana: number, disponibilidades: Disponibilidad[]): SlotHorario[]`; `diaSemanaHoy(hoy?: Date): number` (0 = lunes).
  - `api/types.ts` → `SesionFutura`, `SesionesFuturas`.
  - `api.ts` → `useSesionesFuturas(disponibilidadId: number | null)`, `useDesactivarDisponibilidad()`.
  - `DialogoDesactivarConSesiones` — props `{ abierto: boolean; total: number; cargando: boolean; error: string | null; onSoloNuevas: () => void; onCancelarYDesactivar: () => void; onCerrar: () => void }`.

- [ ] **Step 1: Escribir los tests de las funciones puras y del diálogo — RED**

Agregar al final de `frontend/src/features/asesorias/logica.test.ts`:

```ts
describe('horasDelDia', () => {
  it('produce los 28 slots de media hora de 07:00 a 20:30', () => {
    const horas = horasDelDia()
    expect(horas).toHaveLength(28)
    expect(horas[0]).toBe('07:00:00')
    expect(horas[1]).toBe('07:30:00')
    expect(horas.at(-1)).toBe('20:30:00')
  })
})

describe('slotsDelDia', () => {
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

  it('devuelve un slot por cada media hora del día', () => {
    expect(slotsDelDia(0, [])).toHaveLength(28)
  })

  it('marca activo el slot con una disponibilidad activa de ese día', () => {
    const slots = slotsDelDia(0, [base])
    const slot = slots.find((s) => s.hora === '09:00:00')

    expect(slot?.activo).toBe(true)
    expect(slot?.disponibilidad).toEqual(base)
  })

  it('un bloque inactivo se reporta como no activo pero conserva su disponibilidad', () => {
    const slots = slotsDelDia(0, [{ ...base, activa: false }])
    const slot = slots.find((s) => s.hora === '09:00:00')

    expect(slot?.activo).toBe(false)
    expect(slot?.disponibilidad?.id).toBe(1)
  })

  it('ignora las disponibilidades de otros días', () => {
    const slots = slotsDelDia(1, [base])

    expect(slots.every((s) => s.disponibilidad === null)).toBe(true)
  })
})

describe('diaSemanaHoy', () => {
  it('traduce el domingo de JavaScript (0) al índice 6 del proyecto', () => {
    expect(diaSemanaHoy(new Date('2026-08-02T10:00:00'))).toBe(6)
  })

  it('traduce el lunes al índice 0', () => {
    expect(diaSemanaHoy(new Date('2026-08-03T10:00:00'))).toBe(0)
  })
})
```

y actualizar la línea 2 del mismo archivo para importar lo nuevo:

```ts
import { semestreActual, claveSlot, mapaDisponibilidades, proximas, historial, sesionesPreviasConNotas, sesionYaOcurrio, puedeGuardarNotas, horasDelDia, slotsDelDia, diaSemanaHoy } from './logica'
```

Crear `frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DialogoDesactivarConSesiones } from './DialogoDesactivarConSesiones'

function montar(total: number) {
  const onSoloNuevas = vi.fn()
  const onCancelarYDesactivar = vi.fn()
  render(
    <DialogoDesactivarConSesiones
      abierto
      total={total}
      cargando={false}
      error={null}
      onSoloNuevas={onSoloNuevas}
      onCancelarYDesactivar={onCancelarYDesactivar}
      onCerrar={vi.fn()}
    />,
  )
  return { onSoloNuevas, onCancelarYDesactivar }
}

describe('DialogoDesactivarConSesiones', () => {
  it('ordena las 3 acciones como fija la convención del paso 3', () => {
    montar(2)

    expect(screen.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'Solo dejar de recibir nuevas',
      'Cancelar esas sesiones y desactivar',
      'Volver',
    ])
  })

  it('la opción destructiva no va rellena', () => {
    montar(2)

    expect(screen.getByRole('button', { name: 'Cancelar esas sesiones y desactivar' })).toHaveClass(
      'bg-transparent',
    )
  })

  it('concuerda el número con el texto', () => {
    montar(1)
    expect(screen.getByText('Hay 1 sesión agendada en este horario.')).toBeInTheDocument()
  })

  it('concuerda el plural', () => {
    montar(3)
    expect(screen.getByText('Hay 3 sesiones agendadas en este horario.')).toBeInTheDocument()
  })

  it('cada opción llama a su callback', () => {
    const { onSoloNuevas, onCancelarYDesactivar } = montar(2)

    fireEvent.click(screen.getByRole('button', { name: 'Solo dejar de recibir nuevas' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar esas sesiones y desactivar' }))

    expect(onSoloNuevas).toHaveBeenCalledTimes(1)
    expect(onCancelarYDesactivar).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pnpm test src/features/asesorias/logica.test.ts src/features/asesorias/components/DialogoDesactivarConSesiones.test.tsx`

Expected: FAIL — `logica.test.ts` falla al importar (`horasDelDia is not exported by ./logica`) y el del diálogo falla con `Failed to resolve import "./DialogoDesactivarConSesiones"`. Los tests preexistentes de `logica.test.ts` no corren hasta que el import se resuelva.

- [ ] **Step 3: Agregar las funciones puras**

En `frontend/src/features/asesorias/logica.ts`, agregar después de `mapaDisponibilidades`:

```ts
/** Los 28 slots de 30 minutos que cubre un día de asesorías: 07:00–20:30. */
export function horasDelDia(): string[] {
  const horas: string[] = []
  for (let h = 7; h <= 20; h++) {
    horas.push(`${String(h).padStart(2, '0')}:00:00`)
    horas.push(`${String(h).padStart(2, '0')}:30:00`)
  }
  return horas
}

export interface SlotHorario {
  hora: string
  clave: string
  /** La disponibilidad registrada en ese slot, activa o no. */
  disponibilidad: Disponibilidad | null
  activo: boolean
}

/**
 * Las 28 filas de un día para la pantalla "Mi horario".
 *
 * Distingue tres situaciones que la UI colapsa en dos chips: sin
 * disponibilidad, con una inactiva (se puede reactivar) y con una activa.
 * Por eso devuelve `disponibilidad` aunque `activo` sea `false` — sin ese
 * dato la pantalla no podría reactivar un bloque y trataría de crear uno
 * nuevo sobre un horario ya ocupado.
 */
export function slotsDelDia(diaSemana: number, disponibilidades: Disponibilidad[]): SlotHorario[] {
  const delDia = new Map<string, Disponibilidad>()
  for (const disponibilidad of disponibilidades) {
    if (disponibilidad.dia_semana === diaSemana) {
      delDia.set(disponibilidad.hora_inicio, disponibilidad)
    }
  }

  return horasDelDia().map((hora) => {
    const disponibilidad = delDia.get(hora) ?? null
    return {
      hora,
      clave: claveSlot(diaSemana, hora),
      disponibilidad,
      activo: disponibilidad?.activa === true,
    }
  })
}

/** Día de la semana de hoy en la convención del backend: 0 = lunes. */
export function diaSemanaHoy(hoy: Date = new Date()): number {
  return (hoy.getDay() + 6) % 7
}
```

- [ ] **Step 4: Agregar los tipos de la superficie nueva**

En `frontend/src/api/types.ts`, agregar al final:

```ts
/** Vista mínima de una asesoría agendada sobre un bloque de disponibilidad.
 *  Contrato de GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/. */
export interface SesionFutura {
  id: number
  fecha: string
  hora_inicio: string
  alumno_nombre: string
  materia_nombre: string
}

export interface SesionesFuturas {
  total: number
  sesiones: SesionFutura[]
}
```

- [ ] **Step 5: Agregar los hooks**

En `frontend/src/features/asesorias/api.ts`, ampliar el import de tipos:

```ts
import type { RegistroAsesor, Disponibilidad, Asesoria, SesionesFuturas } from '../../api/types'
```

y agregar después de `useEliminarDisponibilidad`:

```ts
/**
 * Sesiones agendadas a futuro sobre un bloque. Se consulta al abrir el
 * diálogo del bloque, para saber si desactivarlo requiere la advertencia de
 * 3 opciones. `enabled` evita la petición mientras no hay bloque abierto.
 *
 * Contrato de la task 6 del plan de backend; todavía no existe en
 * dev-backend.
 */
export function useSesionesFuturas(disponibilidadId: number | null) {
  return useQuery({
    queryKey: ['disponibilidades', disponibilidadId, 'sesiones-futuras'],
    queryFn: () =>
      apiGet<SesionesFuturas>(`/api/asesorias/disponibilidades/${disponibilidadId}/sesiones-futuras/`),
    enabled: disponibilidadId !== null,
    staleTime: 0,
  })
}

/**
 * Desactiva un bloque, con o sin cancelar sus sesiones futuras.
 *
 * Las dos opciones del modal de advertencia se sirven con un solo endpoint
 * distinguido por `cancelar_sesiones` (task 7 del plan de backend), así que
 * aquí también son una sola mutación. Invalida `asesorias` además de
 * `disponibilidades` porque la variante que cancela cambia las dos listas.
 */
export function useDesactivarDisponibilidad() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, cancelarSesiones, motivo = '' }: { id: number; cancelarSesiones: boolean; motivo?: string }) =>
      apiPost<{ disponibilidad: Disponibilidad; sesiones_canceladas: number }>(
        `/api/asesorias/disponibilidades/${id}/desactivar/`,
        { cancelar_sesiones: cancelarSesiones, motivo },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['disponibilidades'] })
      queryClient.invalidateQueries({ queryKey: ['asesorias'] })
    },
  })
}
```

- [ ] **Step 6: Escribir el diálogo de 3 acciones**

Crear `frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.tsx`:

```tsx
import { Dialogo } from '../../../components/ui/Dialogo'

interface DialogoDesactivarConSesionesProps {
  abierto: boolean
  total: number
  cargando: boolean
  error: string | null
  onSoloNuevas: () => void
  onCancelarYDesactivar: () => void
  onCerrar: () => void
}

/**
 * Advertencia al desactivar un bloque que tiene sesiones ya agendadas
 * (paso 3). Las tres acciones y su orden los fija la convención; aquí solo
 * se declaran en el orden semántico y `Dialogo` se encarga del resto.
 */
export function DialogoDesactivarConSesiones({
  abierto,
  total,
  cargando,
  error,
  onSoloNuevas,
  onCancelarYDesactivar,
  onCerrar,
}: DialogoDesactivarConSesionesProps) {
  const descripcion =
    total === 1
      ? 'Hay 1 sesión agendada en este horario.'
      : `Hay ${total} sesiones agendadas en este horario.`

  return (
    <Dialogo
      abierto={abierto}
      titulo="Este horario tiene sesiones agendadas"
      descripcion={descripcion}
      error={error}
      onCerrar={onCerrar}
      acciones={[
        { etiqueta: 'Solo dejar de recibir nuevas', cargando, onClick: onSoloNuevas },
        {
          etiqueta: 'Cancelar esas sesiones y desactivar',
          tono: 'peligro',
          cargando,
          onClick: onCancelarYDesactivar,
        },
      ]}
    />
  )
}
```

- [ ] **Step 7: Correr los tests y confirmar que pasan**

Run: `pnpm test src/features/asesorias/logica.test.ts src/features/asesorias/components/DialogoDesactivarConSesiones.test.tsx`

Expected: PASS — los 9 casos nuevos más los 8 preexistentes de `logica.test.ts`.

- [ ] **Step 8: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/features/asesorias/logica.ts frontend/src/features/asesorias/logica.test.ts \
        frontend/src/api/types.ts frontend/src/features/asesorias/api.ts \
        frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.tsx \
        frontend/src/features/asesorias/components/DialogoDesactivarConSesiones.test.tsx
git commit -s -m "[feat][frontend] agregar el nucleo de logica y datos de Mi horario" \
  -m "- logica.ts: horasDelDia (28 slots de 07:00 a 20:30), slotsDelDia (las
    filas de un dia, distinguiendo vacio / inactivo / activo para poder
    reactivar un bloque en vez de intentar crear uno encima) y diaSemanaHoy
    (traduce el domingo=0 de JS al lunes=0 del backend).
- useSesionesFuturas y useDesactivarDisponibilidad contra los contratos que
    fijan las tasks 6 y 7 del plan de backend; las dos opciones del modal
    van por un solo endpoint distinguido por cancelar_sesiones.
- DialogoDesactivarConSesiones: el modal de 3 acciones del paso 3, que solo
    declara sus acciones en orden semantico — el layout y los estilos los
    pone el Dialogo compartido."
```

---

### Task 10: Pantalla "Mi horario"

La segunda pantalla del rediseño y el motivo original de todo: la grilla de 7×28 celdas mostraba ~3 de 7 columnas en un viewport de 390px sin ninguna pista de scroll. Se reemplaza por tabs por día con una lista vertical.

**Files:**
- Create: `frontend/src/features/asesorias/screens/MiHorario.tsx`
- Test: `frontend/src/features/asesorias/screens/MiHorario.test.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent` (Task 6); `slotsDelDia`, `diaSemanaHoy`, `claveSlot` (Task 9); `useSesionesFuturas`, `useDesactivarDisponibilidad` (Task 9); `DialogoDesactivarConSesiones` (Task 9); `DialogoNuevoBloque`, `DialogoBloqueActivo` (Task 5); `useMisDisponibilidades`, `useCrearDisponibilidad`, `useActualizarDisponibilidad`, `useEliminarDisponibilidad`, `useRegistroDelSemestre` (existentes + Task 7); `SinRegistroAsesor`, `primerMensajeDeError`, `IconVirtual`, `IconPresencial` (Task 7); `Skeleton` (existente, sin modificar).
- Produces: ruta `/asesorias/horario` → `MiHorario`.

- [ ] **Step 1: Escribir el test de la pantalla — RED**

Crear `frontend/src/features/asesorias/screens/MiHorario.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MiHorario } from './MiHorario'
import * as api from '../api'
import type { Disponibilidad, RegistroAsesor } from '../../../api/types'

const REGISTRO: RegistroAsesor = { id: 3, semestre: '20262', materias: [1] }

const BLOQUE_LUNES: Disponibilidad = {
  id: 11,
  registro: 3,
  dia_semana: 0,
  hora_inicio: '09:00:00',
  formato: 'presencial',
  ubicacion: 'Salón O-221',
  liga_virtual: '',
  activa: true,
}

function montar({
  disponibilidades = [BLOQUE_LUNES],
  totalSesionesFuturas = 0,
}: { disponibilidades?: Disponibilidad[]; totalSesionesFuturas?: number } = {}) {
  vi.spyOn(api, 'useRegistroDelSemestre').mockReturnValue({ registro: REGISTRO, cargando: false })
  vi.spyOn(api, 'useMisDisponibilidades').mockReturnValue({
    data: disponibilidades,
    isPending: false,
  } as ReturnType<typeof api.useMisDisponibilidades>)
  vi.spyOn(api, 'useSesionesFuturas').mockReturnValue({
    data: { total: totalSesionesFuturas, sesiones: [] },
    isPending: false,
  } as ReturnType<typeof api.useSesionesFuturas>)

  const desactivar = vi.fn()
  const actualizar = vi.fn()
  vi.spyOn(api, 'useDesactivarDisponibilidad').mockReturnValue({
    mutate: desactivar,
    isPending: false,
  } as unknown as ReturnType<typeof api.useDesactivarDisponibilidad>)
  vi.spyOn(api, 'useActualizarDisponibilidad').mockReturnValue({
    mutate: actualizar,
    isPending: false,
  } as unknown as ReturnType<typeof api.useActualizarDisponibilidad>)
  vi.spyOn(api, 'useCrearDisponibilidad').mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof api.useCrearDisponibilidad>)
  vi.spyOn(api, 'useEliminarDisponibilidad').mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof api.useEliminarDisponibilidad>)

  render(
    <MemoryRouter>
      <MiHorario />
    </MemoryRouter>,
  )
  return { desactivar, actualizar }
}

describe('MiHorario', () => {
  beforeEach(() => {
    // Lunes, para que la pestaña por default sea la del bloque de prueba.
    vi.setSystemTime(new Date('2026-08-03T10:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('muestra una pestaña por día y la instrucción fija arriba', () => {
    montar()

    expect(screen.getAllByRole('tab')).toHaveLength(7)
    expect(
      screen.getByText(
        'Cada celda es un horario disponible: toca para activarlo o editarlo. Para cambiar de día, usa las pestañas. Los cambios se autoguardan.',
      ),
    ).toBeInTheDocument()
  })

  it('lista los 28 slots del día seleccionado, sin scroll horizontal', () => {
    montar()

    expect(screen.getAllByRole('button', { name: /^Horario/ })).toHaveLength(28)
  })

  it('un slot activo presencial muestra el salón sin prefijo ni texto de formato repetido', () => {
    montar()

    const slot = screen.getByRole('button', { name: /^Horario 09:00/ })
    expect(within(slot).getByText('Salón O-221')).toBeInTheDocument()
    expect(within(slot).queryByText(/Presencial —/)).not.toBeInTheDocument()
    expect(within(slot).getByText('Activo')).toBeInTheDocument()
  })

  it('desactivar un bloque sin sesiones futuras no pide confirmación extra', () => {
    const { desactivar } = montar({ totalSesionesFuturas: 0 })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }))

    expect(desactivar).toHaveBeenCalledWith(
      { id: 11, cancelarSesiones: false },
      expect.anything(),
    )
  })

  it('con sesiones futuras muestra el modal de 3 acciones antes de desactivar', () => {
    const { desactivar } = montar({ totalSesionesFuturas: 2 })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }))

    expect(desactivar).not.toHaveBeenCalled()
    expect(screen.getByText('Hay 2 sesiones agendadas en este horario.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar esas sesiones y desactivar' }))

    expect(desactivar).toHaveBeenCalledWith({ id: 11, cancelarSesiones: true }, expect.anything())
  })

  it('tocar un bloque inactivo lo reactiva directo, sin diálogo', () => {
    const { actualizar } = montar({ disponibilidades: [{ ...BLOQUE_LUNES, activa: false }] })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))

    expect(actualizar).toHaveBeenCalledWith({ id: 11, activa: true }, expect.anything())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('tocar un slot vacío abre el diálogo de bloque nuevo', () => {
    montar({ disponibilidades: [] })

    fireEvent.click(screen.getByRole('button', { name: /^Horario 09:00/ }))

    expect(screen.getByRole('dialog', { name: /Nuevo bloque — Lunes 09:00/ })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pnpm test src/features/asesorias/screens/MiHorario.test.tsx`

Expected: FAIL — `Failed to resolve import "./MiHorario"` en los 8 casos.

- [ ] **Step 3: Escribir la pantalla**

Crear `frontend/src/features/asesorias/screens/MiHorario.tsx`:

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

export function MiHorario() {
  const navigate = useNavigate()
  const { mensaje, mostrar } = useRetroalimentacion()

  const { registro, cargando: cargandoRegistro } = useRegistroDelSemestre()
  const { data: disponibilidades = [], isPending: cargandoDisponibilidades } = useMisDisponibilidades()

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

  if (cargandoRegistro) {
    return <p className="p-6 text-sm text-on-surface-variant">Cargando…</p>
  }

  if (!registro) {
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
    if (!celdaVacia) return
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
            {cargandoDisponibilidades ? (
              <ul className="flex flex-col gap-1">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-11" />
                ))}
              </ul>
            ) : (
              <ul className="flex flex-col">
                {slotsDelDia(indice, disponibilidades).map((slot) => (
                  <li key={slot.clave}>
                    <button
                      type="button"
                      onClick={() => tocarSlot(indice, slot.hora, slot.disponibilidad)}
                      aria-label={`Horario ${slot.hora.slice(0, 5)}, ${slot.activo ? 'activo' : 'inactivo'}`}
                      className="foco-visible flex min-h-11 w-full items-center gap-2 border-b border-outline-variant px-2 text-sm text-on-surface hover:bg-surface-container-high"
                    >
                      <span className="w-12 shrink-0 text-on-surface-variant">{slot.hora.slice(0, 5)}</span>

                      {slot.activo && slot.disponibilidad !== null && (
                        <span className="flex min-w-0 flex-1 items-center gap-2">
                          {slot.disponibilidad.formato === 'virtual' ? (
                            <IconVirtual className="h-4 w-4 shrink-0" />
                          ) : (
                            <IconPresencial className="h-4 w-4 shrink-0" />
                          )}
                          {slot.disponibilidad.formato === 'presencial' && (
                            <span className="truncate">{slot.disponibilidad.ubicacion}</span>
                          )}
                        </span>
                      )}

                      <span
                        className={`ml-auto shrink-0 rounded-full px-2 py-0.5 text-xs ${
                          slot.activo
                            ? 'bg-primary-container text-on-primary-container'
                            : 'bg-surface-variant text-on-surface-variant'
                        }`}
                      >
                        {slot.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </TabsContent>
        ))}
      </Tabs>

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

- [ ] **Step 4: Registrar la ruta**

En `frontend/src/App.tsx`, agregar el import:

```tsx
import { MiHorario } from './features/asesorias/screens/MiHorario'
```

y la ruta, junto a la de `materias` y antes de `/asesorias/:id`:

```tsx
        <Route
          path="/asesorias/horario"
          element={
            <RutaDeAsesor>
              <MiHorario />
            </RutaDeAsesor>
          }
        />
```

- [ ] **Step 5: Correr el test y confirmar que pasa**

Run: `pnpm test src/features/asesorias/screens/MiHorario.test.tsx`

Expected: PASS — los 8 casos.

- [ ] **Step 6: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/asesorias/screens/MiHorario.tsx \
        frontend/src/features/asesorias/screens/MiHorario.test.tsx frontend/src/App.tsx
git commit -s -m "[feat][frontend] agregar la pantalla Mi horario con pestanas por dia" \
  -m "- Reemplaza la grilla de 7x28 celdas por una lista vertical de 28 slots
    por dia, con pestanas Lun-Dom (tabs.tsx de shadcn): el hallazgo que
    origino el rediseno era que la grilla mostraba ~3 de 7 columnas en un
    viewport de 390px sin ninguna pista de scroll horizontal.
- La pestana por default es el dia de hoy. Instruccion fija y leyenda de
    color/formato arriba; cada fila activa muestra hora, icono de formato y
    el salon directo, sin repetir 'Virtual'/'Presencial' ni el prefijo
    'Presencial —' que la leyenda ya explica una vez.
- Desactivar consulta sesiones futuras primero: sin sesiones desactiva
    directo, con sesiones abre el modal de 3 acciones. Reactivar un bloque
    inactivo se autoguarda sin dialogo, como promete la instruccion."
```

---

### Task 11: Retirar la grilla y `DisponibilidadAsesor`

Con las dos pantallas nuevas en pie, la pantalla vieja y su grilla dejan de tener consumidor. Este task es el que cierra el rediseño: borra el código muerto, redirige la navegación y limpia lo que quedó sin uso en `logica.ts`.

**Files:**
- Delete: `frontend/src/features/asesorias/screens/DisponibilidadAsesor.tsx`
- Delete: `frontend/src/features/asesorias/components/GrillaDisponibilidad.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/features/asesorias/screens/SesionesAsesor.tsx`
- Modify: `frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx`
- Modify: `frontend/src/features/asesorias/logica.ts`
- Modify: `frontend/src/features/asesorias/logica.test.ts`

**Interfaces:**
- Consumes: rutas `/asesorias/materias` (Task 8) y `/asesorias/horario` (Task 10).
- Produces: `SesionesAsesor` deja de tener el link único "Disponibilidad" y expone dos botones. `logica.ts` deja de exportar `mapaDisponibilidades` (su único consumidor era la grilla; `slotsDelDia` lo reemplaza).

- [ ] **Step 1: Escribir el test de navegación — RED**

Reemplazar el archivo completo `frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx` por:

```tsx
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

function montar() {
  vi.spyOn(api, 'useMisAsesorias').mockReturnValue({
    data: [
      crearAsesoria({ id: 1, estado: 'agendada' }),
      crearAsesoria({ id: 2, estado: 'realizada' }),
    ],
    isPending: false,
  } as ReturnType<typeof api.useMisAsesorias>)
  vi.spyOn(catalogo, 'useMapaMaterias').mockReturnValue(
    new Map([[1, { id: 1, nombre: 'Cálculo I' } as never]]),
  )

  render(<SesionesAsesor />, { wrapper: envolver })
}

describe('SesionesAsesor', () => {
  afterEach(() => vi.restoreAllMocks())

  it('la tab Próximas muestra solo agendadas por default', () => {
    montar()

    expect(screen.getAllByText('Cálculo I')).toHaveLength(1)
  })

  it('ofrece las dos pantallas de disponibilidad en vez del link único', () => {
    montar()

    expect(screen.getByRole('button', { name: 'Mis materias' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mi horario' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Disponibilidad' })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pnpm test src/features/asesorias/screens/SesionesAsesor.test.tsx`

Expected: FAIL — el segundo caso falla con `Unable to find an accessible element with the role "button" and name "Mis materias"`. El primero sigue pasando: es la regresión que se protege.

- [ ] **Step 3: Reemplazar el link único por los dos botones**

En `frontend/src/features/asesorias/screens/SesionesAsesor.tsx`, reemplazar el bloque del encabezado (líneas 16-25, el `<div className="flex items-center justify-between">` completo) por:

```tsx
      <h1 className="text-lg font-semibold text-on-background">Asesorías</h1>

      <div className="flex gap-2">
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
      </div>
```

- [ ] **Step 4: Borrar la pantalla vieja y su grilla**

Run:
```bash
git rm src/features/asesorias/screens/DisponibilidadAsesor.tsx \
       src/features/asesorias/components/GrillaDisponibilidad.tsx
```

- [ ] **Step 5: Quitar la ruta vieja**

En `frontend/src/App.tsx`: borrar el import de `DisponibilidadAsesor` y el bloque `<Route path="/asesorias/disponibilidad" ...>` completo.

La ruta no se redirige: la app todavía no está liberada, `/asesorias/disponibilidad` solo se alcanzaba desde el botón que la Step 3 acaba de reemplazar, y un `Navigate` a una de las dos pantallas nuevas tendría que elegir arbitrariamente cuál (ver Decisión 8).

- [ ] **Step 6: Retirar `mapaDisponibilidades`**

En `frontend/src/features/asesorias/logica.ts`, borrar la función `mapaDisponibilidades` completa (líneas 13-21). Su único consumidor era `GrillaDisponibilidad`; `slotsDelDia` cubre el mismo trabajo con las tres situaciones de slot que la pantalla nueva necesita.

En `frontend/src/features/asesorias/logica.test.ts`: quitar `mapaDisponibilidades` del import de la línea 2 y borrar su bloque `describe` completo (líneas 21-39). El tipo `Disponibilidad` sigue importándose: lo usa el `describe` de `slotsDelDia`.

- [ ] **Step 7: Confirmar que no quedó ninguna referencia colgante**

Run:
```bash
grep -rn "DisponibilidadAsesor\|GrillaDisponibilidad\|mapaDisponibilidades" src/ || echo "SIN REFERENCIAS COLGANTES"
```

Expected: imprime `SIN REFERENCIAS COLGANTES`.

- [ ] **Step 8: Correr los tests y confirmar que pasan**

Run: `pnpm test src/features/asesorias/screens/SesionesAsesor.test.tsx src/features/asesorias/logica.test.ts`

Expected: PASS — los 2 casos de `SesionesAsesor` y los 15 de `logica.test.ts` (los 7 preexistentes que quedan más los 8 nuevos de la Task 9).

- [ ] **Step 9: Correr la suite completa**

Run: `pnpm test && pnpm lint && pnpm build`

Expected: verde. `pnpm build` es el que confirma que ningún import quedó apuntando a los archivos borrados.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/App.tsx \
        frontend/src/features/asesorias/screens/SesionesAsesor.tsx \
        frontend/src/features/asesorias/screens/SesionesAsesor.test.tsx \
        frontend/src/features/asesorias/logica.ts \
        frontend/src/features/asesorias/logica.test.ts
git commit -s -m "[refactor][frontend] retirar DisponibilidadAsesor y su grilla semanal" \
  -m "- Se borran DisponibilidadAsesor.tsx y GrillaDisponibilidad.tsx: sus dos
    responsabilidades ahora viven en Mis materias y Mi horario, y la grilla
    era el hallazgo que origino el rediseno del paso 3.
- SesionesAsesor cambia el link de texto 'Disponibilidad' por dos botones,
    consecuencia directa de la separacion en dos pantallas.
- La ruta /asesorias/disponibilidad se retira sin redirect: solo se
    alcanzaba desde el boton que se acaba de reemplazar.
- logica.ts pierde mapaDisponibilidades, cuyo unico consumidor era la
    grilla; slotsDelDia lo reemplaza con las tres situaciones de slot."
```

---

### Task 12: Documentar el resultado

Cierra el paso 8 del ledger. Los documentos de los pasos 6 y 7 se escribieron antes de ejecutar y por eso hablan en futuro de cosas que ya existen ("el componente compartido, nombre exacto a definir en el plan de implementación", "ningún primitivo de `components/ui/` tiene test hoy"). Este task los pone al día. No reabre ninguna decisión.

**Files:**
- Modify: `docs/development/contribuir-componentes.md`
- Modify: `docs/decisions/0020-sistema-componentes-shadcn.md`
- Modify: `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`

**Interfaces:**
- Consumes: el estado final del código después de las Tasks 1-11.
- Produces: documentación consistente con el árbol real de `frontend/src/components/ui/`.

- [ ] **Step 1: Verificar el estado real antes de escribir sobre él**

Run:
```bash
ls frontend/src/components/ui/ && grep -c "it(" frontend/src/components/ui/*.test.tsx
```

Expected: la carpeta lista `Boton.tsx`, `Dialogo.tsx`, `Dialogo.test.tsx`, `InsigniaEstado.tsx`, `Retroalimentacion.tsx`, `Skeleton.tsx`, `dialog.tsx`, `dialog.test.tsx`, `tabs.tsx`, `tabs.test.tsx`. Los tres archivos de test reportan sus casos. Si algo no coincide, una task anterior quedó incompleta — no documentes un estado que no existe.

- [ ] **Step 2: Actualizar el marco de trabajo de componentes**

En `docs/development/contribuir-componentes.md`:

En la sección "`components/ui/` vs específico de feature", reemplazar el tercer bullet por:

```markdown
- Un componente puede vivir en `features/` y **componer** algo de `components/ui/` — es lo esperado, no una excepción. Ejemplo real: los cuatro diálogos de asesorías (`DialogoCancelar`, `DialogoNuevoBloque`, `DialogoAgregarMateria`, `DialogoBloqueActivo`) más los dos nuevos (`DialogoQuitarMateria`, `DialogoDesactivarConSesiones`) componen `components/ui/Dialogo.tsx` y no montan Radix por su cuenta.
```

En la sección "Estructura de un componente nuevo", reemplazar el bullet de **Tests** por:

```markdown
- **Tests:** co-localizados (`Componente.test.tsx` junto al componente) — patrón ya usado en `AuthContext.test.tsx`, `SesionesAsesor.test.tsx`, `Dialogo.test.tsx`. **Todo componente nuevo con lógica propia (estado, validación, efectos) debe llevar al menos un test de comportamiento**; sigue `superpowers:test-driven-development` cuando la lógica lo amerite. Un componente puramente presentacional (sin estado ni ramas) puede quedarse con un smoke test o ninguno si el costo no se justifica — es el caso de `UiIcons.tsx`. Gap conocido que sigue abierto: `Boton.tsx`, `InsigniaEstado.tsx`, `Retroalimentacion.tsx` y `Skeleton.tsx` no tienen test; se cubren el día que se los toque, no retroactivamente.
```

Agregar una sección nueva justo antes de "Lineamientos de diseño":

```markdown
## Diálogos

Cualquier diálogo nuevo compone `components/ui/Dialogo.tsx`; no se monta `Dialog.Root`/`Portal`/`Overlay` de Radix a mano ni se importa `components/ui/dialog.tsx` directo desde un feature.

`Dialogo` recibe `acciones` ordenadas de menor a mayor consecuencia y **construye la acción de salir por su cuenta** a partir de `onCerrar`, porque dónde va y con qué estilo es justamente la convención del paso 3:

| `acciones` | Layout | Estilos |
|---|---|---|
| 1 | fila | salir a la izquierda en contorno, la confirmación a la derecha rellena con su tono |
| 2 o más | columna a ancho completo | la primera (reversible) rellena, las siguientes en contorno, salir al final como texto plano |

El fix de overflow del paso 3 (`min-w-0` + `whitespace-normal` + altura mínima en vez de fija) ya está dentro del componente: no hay que repetirlo por diálogo.
```

Y en la sección "Checklist de accesibilidad", reemplazar el bullet de **Foco visible** por:

```markdown
- **Foco visible:** todo elemento interactivo nuevo lleva la clase `.foco-visible` (definida en `index.css`, ring de 2px en `--color-primary` con offset). No basta con quitar el outline por defecto del navegador. Gap conocido que sigue abierto: `Login.tsx` usa `outline-none focus:border-primary`, sin ring perceptible — se corrige cuando se toque esa pantalla (paso 9).
```

- [ ] **Step 3: Anotar la ejecución en ADR 0020**

En `docs/decisions/0020-sistema-componentes-shadcn.md`, agregar en la sección `## Changelog`, arriba de la entrada existente:

```markdown
- **2026-08-05** — Decisión ejecutada (paso 8, `dev-frontend`). `components.json` + alias `@/`, bloque de alias shadcn→M3 en `index.css` (16 nombres, cero valores de color duplicados), primitivos `dialog.tsx` y `tabs.tsx` generados y curados —sin `lucide-react` ni `tw-animate-css`, que el CLI instala por default y que chocan con ADR 0014 y con el sistema de motion propio—, `components/ui/Dialogo.tsx` como el único lugar donde vive la convención de botones, y los 4 diálogos duplicados migrados: ninguna feature importa ya `@radix-ui/react-dialog` ni `@radix-ui/react-tabs`. Plan: `docs/superpowers/plans/2026-08-04-sistema-componentes.md`.
```

- [ ] **Step 4: Cerrar el paso 8 en el ledger**

En `docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`:

En la tabla "Estado por paso", cambiar la fila 8 de `Pendiente` a `Completo`.

Agregar una sección nueva antes de `## Próximo paso`:

```markdown
## Hallazgos del Paso 8 (implementación de componentes, `dev-frontend`)

- El CLI de shadcn trae dos cosas que este proyecto no puede aceptar tal cual, ninguna anticipada por la spec del paso 6: `lucide-react` (el `dialog.tsx` generado usa un ícono de cierre de esa librería, en conflicto directo con ADR 0014, que decidió íconos a mano y descartó una librería completa "por un solo glyph") y `tw-animate-css` (las clases `animate-in`/`fade-in-0` no pasan por el bloque de `prefers-reduced-motion` que el paso 7 exige). Las dos se descartaron: el botón de cierre desaparece —`Dialogo` siempre renderiza una acción de salir explícita— y la animación usa dos `@keyframes` propios en `index.css`. Las dependencias nuevas quedaron exactamente en las tres que fija ADR 0020.
- El `init` de shadcn reescribe `index.css` con su propia paleta en oklch más un bloque `@theme inline` que colisionaría con `--color-background` de ADR 0014. Se descarta entera con `git checkout -- src/index.css` y el mapeo se escribe a mano en la dirección contraria (`--color-destructive: var(--color-error)`), que es lo que decidió la decisión 2 de la spec. Se usa `@theme` normal y no `@theme inline` porque la paleta es dark-only y estática.
- El componente compartido se llamó `Dialogo` y no `ConfirmDialog` (el ejemplo tentativo de la spec): tres de los cuatro diálogos migrados llevan formulario, no una confirmación, y el propio documento del paso 7 ya lo nombraba así ("un diálogo específico de asesorías que envuelve el `Dialogo` compartido").
- El fix de overflow del paso 3 obligó a que `Dialogo` renderice sus propios botones en vez de componer `Boton`: la altura fija `h-11` de `Boton` no permite las dos líneas que pide `white-space: normal`, y `Boton` no tiene tono destructivo en contorno. Como `Boton` está explícitamente fuera de alcance (decisión 5 de la spec del paso 6), la solución fue interna al diálogo. Queda anotado que cuando el paso 9 necesite el "Cancelar asesoría" en contorno del punto 5 del paso 3, los dos tonos deberían converger.
- Tres acciones de las pantallas nuevas (quitar materia, consultar sesiones futuras, desactivar con cancelación) llaman endpoints que sólo existen en el plan de backend del paso 4, todavía sin ejecutar. Se implementaron contra esos contratos exactos en vez de inventar un fallback; los tests no tocan red, así que la suite pasa, pero esas acciones fallan en runtime hasta que el backend se integre. **Es el bloqueo real más importante que deja este paso.**
- La duplicación que originó ADR 0020 se cerró de forma verificable: `grep -rn "@radix-ui/react-dialog\|@radix-ui/react-tabs" src/features/` no devuelve nada.
```

Reemplazar la sección `## Próximo paso` por:

```markdown
## Próximo paso

Paso 9 (`dev-frontend`, modelo Opus): plan de implementación de login frontend (`docs/superpowers/plans/2026-08-04-login-oauth-frontend.md`). Recibe como insumo la spec del paso 2 y, ya resueltos, el sistema de componentes del paso 8. Trae además los pendientes que el paso 8 dejó anotados a propósito: el "← Home" y los subtabs de semestre de `SesionesAsesor`, el "Cancelar asesoría" en contorno y los íconos de formato en `DetalleAsesoria` (los SVG ya existen en `components/icons/UiIcons.tsx`), la tarjeta condicional de Home, y el foco visible de `Login.tsx`.
```

- [ ] **Step 5: Verificar que ningún enlace quedó roto y que la suite sigue verde**

Run:
```bash
pnpm --dir frontend test && pnpm --dir frontend build
grep -rn "DisponibilidadAsesor\|GrillaDisponibilidad" docs/development/contribuir-componentes.md || echo "DOCS SIN REFERENCIAS A LO BORRADO"
```

Expected: la suite y el build en verde, y el `grep` imprime `DOCS SIN REFERENCIAS A LO BORRADO`. Si aparece alguna línea, actualízala antes de comitear.

- [ ] **Step 6: Commit**

```bash
git add docs/development/contribuir-componentes.md \
        docs/decisions/0020-sistema-componentes-shadcn.md \
        docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md
git commit -s -m "[docs] cerrar paso 8: sistema de componentes implementado" \
  -m "- contribuir-componentes.md: seccion nueva de dialogos con la tabla de
    la convencion ya codificada en Dialogo.tsx, el gap de foco visible
    reformulado como la clase .foco-visible obligatoria, y el gap de tests
    acotado a los cuatro primitivos que siguen sin cubrir.
- Changelog en ADR 0020 con lo que la ejecucion agrego a la decision:
    descartar lucide-react y tw-animate-css que el CLI instala por default.
- Ledger: paso 8 completo, con los hallazgos que condicionan al paso 9 —
    sobre todo que tres acciones de las pantallas nuevas dependen de
    endpoints del plan de backend todavia sin ejecutar."
```

---

## Self-Review

**1. Cobertura de los requisitos**

| Requisito | Fuente | Task |
|---|---|---|
| `pnpm dlx shadcn init` una sola vez, `components.json` | spec paso 6, decisión 6 | 1 |
| Alias de tokens shadcn→M3 en `index.css`, sin duplicar la paleta | spec paso 6, decisión 2 | 1 (Step 8), verificado en 2 (Step 7) |
| `components/ui/` plana, nombres del CLI sin traducir | spec paso 6, decisión 3; ADR 0020 | 2, 3, 6 |
| Instalación on-demand, no el catálogo completo | spec paso 6, decisión 6 | 2 (`dialog`), 6 (`tabs`) — nada más |
| Las 3 dependencias de ADR 0020, ninguna más | spec paso 6, tabla de dependencias | 1 (Step 4), 2 (Step 5) |
| Los 4 diálogos consolidados en un componente compartido | spec paso 6, decisión 4 | 3 (el componente), 4 y 5 (la migración) |
| La convención de botones codificada **una sola vez** | spec paso 3, "Convención de diálogos" | 3 |
| 2 acciones = fila, salir a la izquierda | spec paso 3 | 3 (test), 4 |
| 3+ acciones = columna, reversible arriba / destructiva en contorno / salir al final | spec paso 3 | 3 (test), 5, 9 |
| Fix de overflow `min-width: 0` + `white-space: normal` | spec paso 3 | 3 (test explícito) |
| `Boton`/`InsigniaEstado`/`Retroalimentacion`/`Skeleton` intactos | spec paso 6, decisión 5 | ninguna los modifica; ver Decisión 5 |
| "Mis materias": filas, truncado + `title`, nombre completo accesible al tocar, botón de 36-44px | spec paso 3, §3 | 8 |
| Copy exacto del diálogo de quitar materia | spec paso 3, §3 | 8 |
| "Mi horario": tabs por día, 28 slots verticales, sin scroll horizontal | spec paso 3, §3 | 10 |
| Instrucción fija y leyenda con los iconos de formato | spec paso 3, §3 | 10 |
| Fila limpia: sin "Virtual"/"Presencial" repetido, sin prefijo "Presencial —" | spec paso 3, §3 | 10 (test explícito) |
| Modal de 3 acciones al desactivar con sesiones futuras | spec paso 3, §3 | 9 (componente), 10 (flujo) |
| Mismos SVG de monitor/pin que usará el detalle | spec paso 3, §3 y §5 | 7 (`UiIcons.tsx`) |
| "Mi horario" usa `tabs.tsx` de shadcn desde el inicio | spec paso 6, decisión 4 | 6, 10 |
| Los dos botones que reemplazan el link "Disponibilidad" | spec paso 3, §4 | 11 |
| `:focus-visible` perceptible en todo lo nuevo | paso 7, checklist | 1 (la clase), 3/6 (tests que la exigen), 4, 5, 7, 8, 10, 11 |
| Labels asociados, el placeholder nunca es el único label | paso 7, checklist | 4, 5, 7 |
| `aria-hidden` en SVG decorativos | paso 7, checklist | 7 (`IconBase`) |
| No interceptar el teclado que Radix maneja | paso 7, checklist | 2 y 6 (tests de Escape y de cambio de pestaña) |
| Pares `{rol}`/`on-{rol}` de contraste | paso 7, checklist | 3, 8, 10 |
| Motion reusado / nuevo con `prefers-reduced-motion` | paso 7, lineamientos | 1 (Step 8) |
| Un test de comportamiento por componente con lógica propia | paso 7, estructura | 1-11; los únicos sin test son `UiIcons.tsx` (presentacional puro) y `DialogoQuitarMateria` (cubierto vía `MisMaterias.test.tsx`) |

Fuera de alcance a propósito, sin omisión silenciosa: el "← Home" y los subtabs de semestre de `SesionesAsesor` (§4 del paso 3 — los subtabs necesitan el filtro de backend de la task 9 del plan del paso 4), los cambios de `DetalleAsesoria` del §5 (botón en contorno, íconos de formato, `line-clamp: 2`), el ícono `IconAsesoriasAcademicas` y la tarjeta condicional de Home (§1 y §2 — dependen de que la deuda 0010 se resuelva en el paso 4), el foco de `Login.tsx`, y todo lo de login/OAuth. Todo eso queda anotado como insumo del paso 9 en el Step 4 de la Task 12.

**2. Placeholders**

Sin `TBD` ni "manejar los casos borde". Cada step de código trae el bloque completo listo para pegar; cada step de verificación trae el comando exacto y el resultado esperado, incluida la razón de cada fallo en RED. Las tres únicas instrucciones condicionales son deliberadas y acotadas: el camino alterno sin red en las Tasks 1, 2 y 6 (con el contenido completo del archivo en el mismo step, así que no hay dependencia real del CLI), y el Step 1 de la Task 12, que exige verificar el árbol antes de documentarlo.

**3. Consistencia de tipos y nombres**

- `cn` se define en la Task 1 y se importa con ese nombre desde `@/lib/utils` en las Tasks 2, 3 y 6.
- `AccionDialogo` y `Dialogo` se definen en la Task 3 y se consumen con esa forma exacta (`etiqueta`/`onClick`/`tono`/`cargando`/`deshabilitada`) en las Tasks 4, 5, 8 y 9.
- Los cuatro diálogos migrados (Tasks 4 y 5) conservan sus props actuales, que es lo que permite que `DetalleAsesoria` no cambie y que `MiHorario` (Task 10) los monte tal cual.
- `useRegistroDelSemestre` devuelve `{ registro, cargando }` en la Task 7 y se desestructura así en las Tasks 8 y 10; los mocks de sus tests devuelven ese mismo objeto.
- `slotsDelDia` devuelve `SlotHorario` con `hora`/`clave`/`disponibilidad`/`activo` en la Task 9 y se consume con esos cuatro campos en la Task 10.
- `useDesactivarDisponibilidad` recibe `{ id, cancelarSesiones, motivo? }` en la Task 9 y se llama con esa forma en la Task 10 y en sus tests — camelCase en el frontend, `cancelar_sesiones` solo en el cuerpo HTTP, que es la convención que ya usa `api.ts` (`liga_virtual`, `dia_semana`).
- `.foco-visible` se declara una vez en la Task 1 y se exige por test en las Tasks 3 y 6.
- `IconVirtual`/`IconPresencial`/`IconBasura` se definen en la Task 7 y se importan con esos nombres en las Tasks 8 y 10.

**4. Verificación previa contra el código real**

Antes de escribir el plan se confirmó, no se infirió: `frontend/package.json` no tiene hoy `clsx`, `tailwind-merge` ni `class-variance-authority` (por eso el `init` sí es necesario); `tailwindcss` instalado es 4.3.3 y no hay `tailwind.config.js`, así que `components.json` va con `"config": ""`; `tsconfig.json` sólo tiene `files`/`references` sin `compilerOptions`, que es exactamente el caso que hace fallar la resolución de alias del CLI de shadcn en plantillas de Vite; `package.json` declara `"type": "module"`, por eso el alias de Vite usa `fileURLToPath` y no `__dirname`; `@types/node` ya está instalado; `@testing-library/user-event` **no** lo está, por eso todos los tests usan `fireEvent`; el patrón `vi.spyOn(api, 'useX')` ya funciona en este repo (`SesionesAsesor.test.tsx`); `tsconfig.app.json` excluye los archivos de test de `tsc -b`, así que `pnpm build` no los typecheca y el error de tipos se ve en `pnpm test`; y `mapaDisponibilidades` tiene un único consumidor (`GrillaDisponibilidad`), que es lo que permite retirarla en la Task 11.

---

## Decisiones de diseño no fijadas por los specs

Las specs de los pasos 3, 6 y 7 fijaron el *qué*. Estas son las decisiones de *forma exacta* que toma este plan para ser ejecutable sin volver a diseño. Ninguna reabre algo ya decidido; cada una está donde el checkpoint puede aceptarla o rechazarla por separado.

| # | Decisión | Task |
|---|---|---|
| 1 | El componente compartido se llama `Dialogo` y vive en `components/ui/Dialogo.tsx`. | 3 |
| 2 | Se adopta el alias `@/`, pero sólo se usa en archivos nuevos; los imports relativos existentes no se reescriben. | 1 |
| 3 | Se descarta `lucide-react` y con él el botón "X" de cierre del `dialog.tsx` generado. | 2 |
| 4 | Se descarta `tw-animate-css`; la animación del diálogo son dos `@keyframes` propios en `index.css`. | 1, 2 |
| 5 | `Dialogo` renderiza sus propios botones en vez de componer `Boton`. | 3 |
| 6 | `SesionesAsesor` se migra a `tabs.tsx` en el mismo task que lo introduce. | 6 |
| 7 | El `tabs.tsx` curado conserva el estilo de subrayado de la app, no el "pill" de shadcn. | 6 |
| 8 | La ruta `/asesorias/disponibilidad` se retira sin redirect; las nuevas son `/asesorias/materias` y `/asesorias/horario`. | 8, 10, 11 |
| 9 | Un slot inactivo se reactiva con un toque, sin diálogo; sólo el activo abre `DialogoBloqueActivo`. | 10 |
| 10 | `primerMensajeDeError` sale a `api/errores.ts` y `DetalleAsesoria` pasa a importarlo. | 7 |
| 11 | Las pantallas nuevas se escriben contra los contratos del plan de backend aunque los endpoints no existan. | 8, 9, 10 |
| 12 | El estado "sin registro de asesor" se extrae a `SinRegistroAsesor` antes de escribir las pantallas. | 7 |

**1. `Dialogo`, no `ConfirmDialog`.** La spec del paso 6 dejó el nombre abierto y propuso `ConfirmDialog.tsx` como ejemplo. Se descarta por dos razones concretas: tres de los cuatro diálogos migrados llevan formulario (motivo, buscador de materias, formato+liga), no una confirmación, así que el nombre describiría mal a la mayoría de sus consumidores; y el documento del paso 7 ya lo nombra `Dialogo` al explicar la composición feature→ui ("un diálogo específico de asesorías que envuelve el `Dialogo` compartido"). Además encaja con la convención que el mismo documento fija: componentes propios en PascalCase y español, primitivos de shadcn en minúsculas y en inglés — con lo que `Dialogo.tsx` y `dialog.tsx` conviven en la carpeta plana sin ambigüedad sobre cuál es cuál.

**2. Alias `@/` sólo hacia adelante.** El CLI de shadcn requiere `paths` en el tsconfig y genera imports `@/lib/utils`; no es opcional. Lo que sí es una decisión es qué hacer con los imports relativos que ya existen (`'../../../components/ui/Boton'`). Se dejan como están: reescribirlos sería un diff enorme, sin test que lo cubra, mezclado con trabajo real — exactamente el tipo de refactor no relacionado que la decisión 5 de la spec del paso 6 evita para `Boton`. La regla queda: archivos nuevos y primitivos generados usan `@/`, el resto se migra sólo si ya se está tocando por otra razón.

**3. Sin `lucide-react`.** El `dialog.tsx` que genera el CLI trae un botón de cierre con un ícono de esa librería, y `add` la instala. ADR 0014 evaluó explícitamente una librería de íconos y la descartó ("para 9 íconos es una dependencia entera por un solo glyph"); ADR 0020 lista tres dependencias nuevas y ninguna es de íconos. Además el botón sería redundante: `Dialogo` siempre renderiza una acción de salir explícita, y tener una "X" en la esquina *más* un "Volver" abajo daría dos salidas con jerarquía distinta en un patrón cuyo punto entero es que el orden de salida sea uno solo. Se elimina el botón, no se reemplaza el ícono.

**4. Motion propio en vez de `tw-animate-css`.** El `init` de shadcn para Tailwind v4 instala ese paquete y los componentes generados usan sus utilidades (`animate-in`, `fade-in-0`, `zoom-in-95`). No pasan por el bloque `@media (prefers-reduced-motion: reduce)` de `index.css`, y el paso 7 exige que cualquier animación nueva lo respete "igual que las existentes". Dos `@keyframes` de cuatro líneas cada uno resuelven el caso y quedan registrados en ese bloque junto a `.skeleton`, `.spinner` y compañía — mismo patrón que el archivo ya usa, cero dependencias. Se pierde la animación de salida (Radix desmonta el contenido al cerrar); es una pérdida aceptada, no un olvido: recuperarla exigiría `forceMount` y manejo de `data-[state=closed]`, complejidad que ninguna spec pidió.

**5. `Dialogo` renderiza sus propios botones.** La opción obvia era componer `Boton`, y se descartó por tres restricciones simultáneas. (a) El fix de overflow del paso 3 pide `white-space: normal` para permitir dos líneas, y `Boton` tiene `h-11` fija: dos líneas se desbordarían del botón. (b) La convención de 3+ acciones exige una destructiva *en contorno*, y `Boton` sólo tiene tono `peligro` relleno; forzarlo con `className` es frágil, porque el orden de las clases en el atributo no decide qué gana en CSS. (c) `Boton` está explícitamente fuera de alcance por la decisión 5 de la spec del paso 6 y por las restricciones globales de este plan. Con eso, la única salida sin violar el alcance es que el diálogo tenga su propio botón interno — diez líneas, con el mismo lenguaje visual (`rounded-full`, `text-sm font-semibold`, spinner de `cargando`). El costo real y asumido: hay dos estilos de botón en la app. Cuando el paso 9 implemente el "Cancelar asesoría" en contorno del §5 del paso 3, ese es el momento natural para converger los tonos; queda anotado en el ledger, no se hace ahora.

**6. `SesionesAsesor` se migra a `tabs.tsx`.** La spec del paso 6 nombra a "Mi horario" como el consumidor de `tabs.tsx` y no menciona `SesionesAsesor`, así que esto es un agregado. La razón: `SesionesAsesor` es el único otro archivo de `features/` que importa Radix directo, y la regla de una línea de ADR 0020 dice "las features importan de esa carpeta, no reimplementan Radix directo". Dejarlo sin migrar conservaría, el mismo día que se instala el primitivo, exactamente la duplicación que la ADR condena. El cambio es de cinco líneas, no altera el resultado visual (las clases se mudan tal cual al primitivo) y su test existente pasa sin tocarlo, que es la evidencia de que no cambió el comportamiento. **Es la decisión más fácil de revertir de la lista:** si el checkpoint la rechaza, se borra el Step 5 de la Task 6 y nada más se mueve.

**7. El `tabs.tsx` curado usa el subrayado de la app.** shadcn genera un estilo "pill" (`bg-muted`, fondo activo). Adoptarlo obligaría a elegir entre cambiar el aspecto de Próximas/Historial —una pantalla ya aprobada en el paso 3, sin ajuste pedido— o tener dos patrones de pestañas en la misma app. Se mueven al primitivo las clases que `SesionesAsesor` ya tenía inline, más `.foco-visible` y una altura mínima táctil. Los consumidores afinan el layout con `className`, que es como "Mi horario" acomoda siete pestañas en un viewport angosto.

**8. Rutas nuevas, ruta vieja retirada sin redirect.** `/asesorias/materias` y `/asesorias/horario`, en plural y en español, siguiendo `/asesorias`. La vieja `/asesorias/disponibilidad` se borra en vez de redirigirse: sólo se alcanzaba desde el botón que la Task 11 reemplaza, la app no está liberada (no hay marcadores externos que romper), y un `Navigate` tendría que elegir arbitrariamente a cuál de las dos pantallas mandar — precisamente la pregunta que el rediseño separó por considerarla dos preguntas distintas. Ojo con el orden de las rutas: ambas se registran **antes** de `/asesorias/:id`, que si no las capturaría como un id.

**9. Un slot inactivo se reactiva con un toque.** La spec describe la leyenda con dos chips (Activo/Inactivo) pero el modelo tiene tres situaciones: sin `Disponibilidad`, con una `activa=false`, y con una activa. La UI colapsa las dos primeras en el chip "Inactivo" —es lo que la spec pide— y el comportamiento se resuelve así: slot vacío abre `DialogoNuevoBloque`; slot con registro inactivo hace `PATCH {activa: true}` directo, sin diálogo; slot activo abre `DialogoBloqueActivo`. Reactivar no destruye nada y la instrucción de la pantalla promete que "los cambios se autoguardan", así que pedir confirmación contradiría el copy. Por eso `slotsDelDia` devuelve la `disponibilidad` aunque `activo` sea `false`: sin ese dato la pantalla intentaría crear un bloque encima de un horario ya ocupado y el backend respondería con un conflicto de unicidad.

**10. `primerMensajeDeError` a `api/errores.ts`.** Hoy está copiado carácter por carácter en `DisponibilidadAsesor` y `DetalleAsesoria`. Este plan borra el primero y crea dos consumidores nuevos, así que la opción de "no tocar nada" en realidad significa volver a copiarlo dos veces más. Va a `src/api/` y no a `features/asesorias/logica.ts` porque su tema es la forma de error de la API (documentada en `docs/development/api-frontend.md`), no el dominio de asesorías. El cambio en `DetalleAsesoria` son dos líneas —borrar la copia local, agregar el import— y de paso la función gana los primeros tests de sus dos ramas.

**11. Las pantallas nuevas se escriben contra endpoints que aún no existen.** Quitar materia, consultar sesiones futuras y desactivar con cancelación están planeadas en las tasks 6, 7 y 8 del plan de backend del paso 4, escrito y sin ejecutar. Las alternativas eran omitir esas acciones —lo que dejaría "Mis materias" sin su botón de quitar y mataría el modal de 3 acciones, que es justamente el caso que motiva la mitad de la convención de botones— o inventar un fallback que ninguna spec pidió. Se implementa contra los contratos exactos que el plan de backend ya fijó (incluido el detalle de que quitar materia es `POST` y no `DELETE`, y que las dos opciones del modal van por un solo endpoint distinguido por `cancelar_sesiones`), con el error del backend mostrado en el diálogo mediante `primerMensajeDeError`. La consecuencia queda declarada en Global Constraints y en el ledger: la suite pasa, esas dos acciones fallan en runtime hasta que el backend se integre.

**12. `SinRegistroAsesor` extraído antes de las pantallas.** El estado "aún no tienes registro de asesor para este semestre" está hoy embebido en `DisponibilidadAsesor`, y las dos pantallas nuevas lo necesitan igual — sin registro no hay ni materias ni horario. Extraerlo en la Task 7, antes de escribir cualquiera de las dos, evita la alternativa realista: copiarlo en "Mis materias" (Task 8) y volver a copiarlo en "Mi horario" (Task 10), que reproduciría en pantallas la misma duplicación que este plan está eliminando en diálogos. Recibe el `titulo` como prop para que el encabezado corresponda a la pantalla desde la que se llegó.

### Critical Files for Implementation
- /home/hyfi/Development/atenea-fc/frontend/src/index.css
- /home/hyfi/Development/atenea-fc/frontend/src/components/ui/Dialogo.tsx
- /home/hyfi/Development/atenea-fc/frontend/src/features/asesorias/screens/MiHorario.tsx
- /home/hyfi/Development/atenea-fc/frontend/src/features/asesorias/logica.ts
- /home/hyfi/Development/atenea-fc/frontend/src/features/asesorias/api.ts
