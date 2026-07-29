# 0014 — Tokens de diseño, logo e íconos en el frontend

**Status:** Accepted
**Date:** 2026-07-29

## Context

La exploración de identidad visual (paleta Material 3 dark, logo de Atenea, set de íconos de servicios) ya se validó como Artifact y el usuario eligió una dirección concreta: logo Opción B ("casco con cresta"), paleta M3 dark con semilla `#0EA5E9`, y 9 íconos de servicios de línea. Esta ADR documenta cómo esas decisiones de diseño ya tomadas se llevan al código del frontend (ADR 0006: Vite+TS+Tailwind).

## Decision

- **Tokens**: los roles de color de Material 3 dark se declaran como variables CSS bajo `@theme` en `frontend/src/index.css` (convención CSS-first de Tailwind v4 — sin `tailwind.config.js`). Nombradas `--color-{role}` (ej. `--color-primary-container`), Tailwind genera automáticamente las utilidades (`bg-primary-container`, `text-on-primary-container`, etc.) para cualquier clase que se use en el código; las que no se usan se eliminan del CSS final (comportamiento JIT esperado, no un bug).
- **Logo**: componente `Logo.tsx` en `frontend/src/components/`, SVG con `stroke="currentColor"` para heredar color vía `className` — la Opción B elegida. El `favicon.svg` usa la Opción A (sin cresta, más legible a 16px) con un color fijo, porque un favicon no hereda el CSS de la página.
- **Íconos de servicios**: `frontend/src/components/icons/ServiceIcons.tsx`, un componente por servicio, todos de trazo (mismo `viewBox`/grosor vía un `IconBase` interno) **excepto** `IconServicioSocial`, que usa el ícono "handshake" de [Google Material Symbols](https://fonts.google.com/icons) (Apache License 2.0) relleno — después de más de una decena de intentos a mano ninguno se leía como un apretón de manos real (documentado en el propio Artifact de exploración). Es la única excepción de estilo en el set, y queda anotada con un comentario y la fuente en el código.

## Consequences

- Agregar un rol de color nuevo es una línea en el bloque `@theme`; no hay archivo de tokens en TypeScript/JS separado que mantener sincronizado.
- El logo y los íconos son componentes React normales (no un sprite SVG ni una librería de íconos) — cero dependencias nuevas, coherente con el alcance mínimo del frontend hasta ahora.
- `IconServicioSocial` es la única pieza del sistema con una licencia de terceros de por medio (Apache 2.0) — debe conservarse la atribución si se audita el proyecto o se redistribuye.
- Si más adelante se necesitan más íconos de Material Symbols, vale la pena reconsiderar esta ADR (¿vale la pena una dependencia real del paquete en vez de copiar paths sueltos?) — por ahora, con una sola excepción, copiar el path es más simple.

## Alternatives considered

- **Tokens en un archivo `tokens.ts`/JSON consumido por Tailwind**: más portable entre herramientas, pero agrega una capa de indirección que Tailwind v4 ya no necesita — su config es CSS nativo.
- **Librería de íconos completa (ej. `lucide-react`, `@material-symbols/svg-400`)** en vez de componentes a mano: evita el problema de dibujar el handshake, pero para 9 íconos (8 propios + 1 excepción) es una dependencia entera por un solo glyph; se prefirió copiar el path puntual.
- **Generar el handshake también a mano, iterando más**: se intentó extensamente (ver Artifact de exploración) sin llegar a un resultado legible — usar un ícono real y con licencia libre fue más rápido y más confiable que seguir iterando a ciegas.
