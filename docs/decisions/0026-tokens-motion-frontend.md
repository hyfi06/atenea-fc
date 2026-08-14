# 0026 — Tokens de motion (easing/duración) para el frontend

**Status:** Accepted
**Date:** 2026-08-14

## Context

El frontend acumuló una base de animación funcional de forma orgánica en `frontend/src/index.css:71-160`: seis `@keyframes` (`shimmer`, `entrada-lista`, `pulso-exito`, `girar`, `entrada-dialogo`, `entrada-velo`) y sus clases (`.skeleton`, `.entrada-lista`, `.salida-lista`, `.pulso-exito`, `.spinner`, `.entrada-dialogo`, `.entrada-velo`), con `prefers-reduced-motion` ya cubierto para todas ellas (`:149-159`). Nunca hubo una decisión que fijara ese vocabulario — se fue escribiendo caso por caso, igual que el patrón shadcn antes de [ADR 0020](0020-sistema-componentes-shadcn.md).

Verificado en código: **cero usos de `:active` o `transition` en todo `frontend/src`** (grep repo-wide). Las duraciones existentes están hardcodeadas por clase (180ms/200ms/300ms/400ms/600ms/1400ms) sin una curva de easing declarada como variable — cada `animation:` referencia `ease-out`/`ease-in`/`linear` del navegador directo, no una curva propia. Esto se reabre ahora porque el [spec de animaciones de feedback y deleite](../superpowers/specs/2026-08-14-animaciones-feedback-deleite-frontend-design.md) necesita cerrar huecos de cobertura (press feedback, salidas simétricas de toast/dropdown/modal, entradas de listas) y cada hueco nuevo repetiría el mismo problema de valores sueltos si no hay un vocabulario compartido primero.

Dos factores pesan en la decisión, en la misma línea que ADR 0020:

- El catálogo de motion va a seguir creciendo con cada servicio SAE nuevo (`CLAUDE.md`: "los servicios se integran de forma incremental"), igual que el catálogo de componentes.
- Sin variables, cada nueva animación vuelve a elegir su propio `cubic-bezier` a ojo — no hay forma barata de mantener cohesión de "feel" entre press feedback, popovers y modales.

El producto es un dashboard institucional serio (UNAM SAE), no un producto lúdico — el motion debe leerse **funcional y sobrio**: eso también es una decisión que vale la pena fijar una vez, no repetir en cada componente.

## Decision

Se declaran tres variables de easing en el bloque `@theme`/`:root` de `frontend/src/index.css`, junto a los tokens de color de [ADR 0014](0014-tokens-logo-iconos-frontend.md):

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* entradas, press feedback */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* movimiento en pantalla */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* paneles anclados (dropdown) */
```

Reglas de uso, vinculantes para todo motion nuevo (ya documentadas en detalle en el spec de la SKILL `emil-design-eng`, aquí se fijan como convención del repo):

- **Nunca `ease-in` en UI.** Solo `--ease-out` (entra/sale), `--ease-in-out` (se mueve/transforma en pantalla), `--ease-drawer` (paneles anclados tipo dropdown/drawer), o `linear` (spinners, progreso constante — ya usado en `.spinner`).
- **Presupuesto de duración**, sin excepción salvo el punto de deleite: press feedback 100-160ms, tooltips/popovers pequeños 125-200ms, dropdowns/selects 150-250ms, modales/drawers 200-500ms, stagger de listas 30-80ms entre ítems. Deleite (404, Login, Landing) puede exceder 300ms — es la única superficie donde aplica.
- **`transition`, no `@keyframes`, para lo interrumpible/repetible**: press feedback, hover, toasts que se apilan rápido. `@keyframes` se conserva donde ya está y no se re-dispara en ráfaga (entrada de diálogo, entrada de lista).
- **Nunca `scale(0)`** en una entrada — mínimo `scale(0.95)` + `opacity: 0`.
- **`transform-origin` consciente del trigger** en popovers/dropdowns (excepción explícita: los modales quedan centrados, no anclados).
- **Todo `hover:` nuevo** se declara bajo `@media (hover: hover) and (pointer: fine)` — los tres usos actuales (`MisMaterias.tsx:88`, `MiHorario.tsx:238`, `DialogoAgregarMateria.tsx:74`) migran al tocarse.
- **Toda clase de animación nueva se añade a la lista de `@media (prefers-reduced-motion: reduce)`** en `index.css:149-159` en el mismo commit que la introduce — es la extensión de un checklist ya existente, no una decisión nueva por caso.

No se introduce ninguna librería de animación (framer-motion/motion/react-spring): el catálogo sigue siendo CSS puro, consistente con que hoy no existe ninguna dependencia de motion en `package.json`. Si en el futuro aparece una necesidad real de física de resorte interrumpible (drag-to-dismiss, gestos), esa es una decisión aparte que se documenta cuando el caso de uso exista — no se anticipa aquí.

## Consequences

- Todo motion nuevo declarado en el [spec de animaciones de feedback y deleite](../superpowers/specs/2026-08-14-animaciones-feedback-deleite-frontend-design.md) referencia estas tres variables en vez de inventar `cubic-bezier` sueltos — un único lugar (`index.css`) fija el "feel" de toda la app.
- Las seis animaciones existentes (`shimmer`, `entrada-lista`, `pulso-exito`, `girar`, `entrada-dialogo`, `entrada-velo`) **no se reescriben** por esta ADR — ya están dentro de presupuesto y su `ease-out`/`ease-in`/`linear` nativo es aceptable; migrarlas a las variables nuevas es opcional y de bajo riesgo, no un requisito de esta decisión.
- Cada componente nuevo que anime paga un costo casi nulo de "¿qué curva uso?" — la tabla de reglas de arriba responde la pregunta sin criterio caso por caso.
- El checklist de `prefers-reduced-motion` deja de ser "algo que alguien podría olvidar": queda escrito como obligación en el mismo commit.

## Alternatives considered

- **No tokenizar; seguir hardcodeando curvas por clase.** Es lo que hay hoy y funciona para seis animaciones. Se descarta porque el spec que motiva esta ADR agrega del orden de 10-15 sitios nuevos de motion; sin variables compartidas, cada uno vuelve a elegir a ojo y la cohesión de "feel" se pierde con el tiempo — el mismo argumento de crecimiento incremental que ya justificó ADR 0020 para componentes.
- **Adoptar una librería de animación (Motion/framer-motion) ahora.** Da springs interrumpibles y control de gestos de fábrica. Se descarta: ninguno de los huecos identificados en el spec (press feedback, salida de toast/dropdown/modal, entrada de listas) necesita física de resorte — todos son transiciones CSS de propiedades `transform`/`opacity`, que corren fuera del hilo principal y no requieren JS. Añadir la dependencia ahora sería anticipar una necesidad (drag/gestos) que todavía no existe en ninguna pantalla.
- **Definir los tokens dentro del spec de diseño en vez de una ADR.** El spec es donde vive el catálogo de *qué* anima y *por qué*; las variables de easing/duración son una decisión de arquitectura reutilizable por cualquier feature futura (igual que los tokens de color de ADR 0014), no una decisión puntual de esta iniciativa — por eso se separa en su propia ADR, y el spec la referencia en vez de repetirla.
