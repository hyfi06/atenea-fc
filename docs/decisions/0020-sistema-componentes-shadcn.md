# 0020 — Sistema de componentes: patrón shadcn/ui sobre Radix + Tailwind

**Status:** Accepted
**Date:** 2026-08-05

## Context

El frontend usa Radix headless (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`) estilizado a mano con Tailwind desde su scaffolding inicial, pero nunca hubo una ADR que lo decidiera formalmente — fue una omisión, no una decisión documentada. Al retomar el paso 6 del plan de rediseño (`docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`), se reabrió esa omisión explícitamente para decidirla.

Verificado en código: el catálogo actual es pequeño (4 primitivos en `frontend/src/components/ui/`), pero los 4 diálogos de asesorías (`DialogoCancelar.tsx`, `DialogoNuevoBloque.tsx`, `DialogoAgregarMateria.tsx`, `DialogoBloqueActivo.tsx`) importan `@radix-ui/react-dialog` directo cada uno, reconstruyendo `Dialog.Root`/`Portal`/`Overlay`/`Content` desde cero sin ningún wrapper compartido — la convención de orden de botones fijada en el paso 3 del mismo plan no tiene dónde codificarse una sola vez.

Dos factores de contexto pesaron en la decisión:

- El crecimiento del catálogo se espera "moderado y constante": asesorías fue el primer servicio de la SAE integrado (`CLAUDE.md`: "los servicios se integran de forma incremental"), van a seguir apareciendo pantallas y diálogos con cada servicio nuevo.
- Quien mantiene el frontend es el usuario en varias sesiones apoyándose en subagentes, no un equipo humano creciente — la prioridad es que el patrón sea barato de aplicar sin releer mucho código, no onboarding humano.

Hay además una inversión ya hecha en tokens propios ([ADR 0014](0014-tokens-logo-iconos-frontend.md)): paleta Material 3 dark como `--color-{role}` bajo `@theme` en `frontend/src/index.css` (Tailwind v4 CSS-first).

## Decision

Se adopta el **patrón shadcn/ui**: un generador (`shadcn` CLI) que copia código fuente de componentes (Radix + `class-variance-authority` para variantes) directo al repo — no una dependencia de UI en runtime, sino una forma de escribir componentes propios más rápido, reusando primitivos de accesibilidad ya resueltos.

- `pnpm dlx shadcn@latest init` una vez; componentes se agregan on-demand (`pnpm dlx shadcn add <componente>`) solo cuando una pantalla real los necesita — no una instalación masiva del catálogo.
- Los componentes generados se mapean a los tokens M3 de ADR 0014 vía un bloque de alias en `index.css` (`--primary: var(--color-primary)`, etc.) — ADR 0014 sigue siendo la fuente canónica de color, shadcn no introduce una paleta paralela.
- `components/ui/` es una sola carpeta plana: output de shadcn (nombres en inglés, tal cual el CLI los genera) y componentes propios existentes (`Boton.tsx`, `InsigniaEstado.tsx`, en español) conviven ahí sin separación por idioma ni subcarpetas.
- Los 4 diálogos duplicados de asesorías se consolidan en un componente compartido que envuelve el `dialog.tsx` de shadcn y codifica la convención de botones del paso 3 una sola vez. `Boton`/`InsigniaEstado`/`Retroalimentacion`/`Skeleton` no se tocan — no están duplicados, migrarlos sería refactor no relacionado.

Detalle completo de la decisión, el mapeo de tokens y qué migra/no migra: [spec del paso 6](../superpowers/specs/2026-08-04-sistema-componentes-design.md).

## Consequences

- Deja de crecer la duplicación de wiring de Radix por cada diálogo/tab nuevo — se escribe una vez por primitivo, no una vez por pantalla.
- Tres dependencias nuevas, todas utilidades (no un kit de UI): `class-variance-authority`, `clsx`, `tailwind-merge`.
- El código de cada componente sigue viviendo en el repo (`components/ui/`), legible directo por una sesión nueva o un subagente sin inferir de documentación externa — a diferencia de una librería completa en `node_modules`.
- Requiere retemar una vez el vocabulario de variables CSS de shadcn a los tokens M3 ya definidos; ese trabajo es puntual (un bloque de alias), no un sistema de theming paralelo a mantener.
- La ejecución (CLI, mapeo de tokens, migración de los 4 diálogos) queda para el plan de implementación del paso 8 — esta ADR fija la decisión y su forma, no la ejecuta.

## Alternatives considered

- **Formalizar el statu quo (Radix headless + Tailwind a mano, sin shadcn):** resuelve la duplicación actual con cero dependencias nuevas y el mínimo esfuerzo. Se descarta como decisión principal porque no da vocabulario para el crecimiento esperado — cada primitivo nuevo (select, popover, tooltip, dropdown-menu) se seguiría escribiendo desde cero. Queda como alternativa más liviana si el ritmo de necesidad de componentes bajara del "moderado y constante" asumido aquí.
- **Librería completa (MUI, Chakra, Ant Design):** descartada por chocar con la paleta M3 ya construida en ADR 0014 (theming propio, en conflicto directo con el de cualquiera de estas librerías) y por vivir como caja negra en `node_modules` — mal ajuste dado que quien mantiene el frontend son sesiones/subagentes que necesitan leer la fuente real de un componente, no inferir su API de documentación externa.
- **Separar componentes de shadcn (inglés) de componentes propios (español) en carpetas distintas:** se evaluó durante el checkpoint del paso 6 y se descartó a pedido del usuario — agrega una capa de indirección (dos carpetas, regla de cuándo traducir un nombre) sin beneficio real; una sola carpeta plana es igual de legible y más simple.

## Changelog

- **2026-08-05** — Decisión ejecutada (paso 8, `dev-frontend`). `components.json` + alias `@/`, bloque de alias shadcn→M3 en `index.css` (16 nombres, cero valores de color duplicados), primitivos `dialog.tsx` y `tabs.tsx` generados y curados —sin `lucide-react` ni `tw-animate-css`, que el CLI instala por default y que chocan con ADR 0014 y con el sistema de motion propio—, `components/ui/Dialogo.tsx` como el único lugar donde vive la convención de botones, y los 4 diálogos duplicados migrados: ninguna feature importa ya `@radix-ui/react-dialog` ni `@radix-ui/react-tabs`. Plan: `docs/superpowers/plans/2026-08-04-sistema-componentes.md`.
- **2026-08-05** — ADR creada al retomar el paso 6 del plan de rediseño de login y componentes, formalizando una decisión que hasta ahora era de facto (Radix + Tailwind sin documentar) y decidiendo explícitamente adoptar el patrón shadcn/ui sobre ella.
