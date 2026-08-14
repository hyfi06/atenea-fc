# Diseño de Spec — Animaciones de feedback y deleite del frontend

**Fecha:** 2026-08-14
**Status:** Approved

---

## Contexto

### Por qué este spec

El frontend tiene una base de motion funcional pero con cobertura parcial (ver [ADR 0026](../../decisions/0026-tokens-motion-frontend.md) para la decisión de tokens que la sostiene). Verificado por grep repo-wide: **cero usos de `:active` o `transition` en `frontend/src`**. Las entradas de toast, dropdown y modal están animadas pero sus salidas no — se desmontan de golpe. Diez-y-tantas listas/grids aparecen sin transición aunque el patrón (`entrada-lista` + `animationDelay` escalonado) ya existe y está en uso en dos sitios. Tres pantallas de baja frecuencia (404, Login, Landing) son completamente estáticas.

Este spec cataloga cada hueco, lo pasa por el gate de cuatro preguntas de `find-animation-opportunities` (frecuencia → propósito → velocidad → función) y fija el valor exacto (clase, easing, duración, `transform-origin`) a implementar. **No amerita ADR propia por ítem**: la única decisión de arquitectura reutilizable (los tokens de easing/duración) ya está en ADR 0026; este documento es catálogo + especificación, no arquitectura nueva.

### Estado actual (referencias verificadas)

**Stack:** Tailwind v4 puro (`@tailwindcss/vite`), sin librería de animación (no framer-motion/motion/react-spring en `package.json`). Radix (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`). Producto dark-only, paleta M3 institucional UNAM ([ADR 0014](../../decisions/0014-tokens-logo-iconos-frontend.md)) — personalidad **seria, no lúdica**; el motion debe leerse funcional, no bouncy, salvo en los dos momentos de deleite explícitamente listados abajo.

**Vocabulario de motion existente** (`frontend/src/index.css:71-160`, no se toca salvo donde se indica): `.skeleton` (shimmer 1.4s), `.entrada-lista`/`.salida-lista` (300ms/200ms, usadas hoy solo en `TarjetaAsesoria.tsx:82` y `AdminAsesores.tsx:58` con `animationDelay: Math.min(indice,10)*30ms`), `.pulso-exito` (400ms, único "celebration" existente, en `TarjetaAsesoria.tsx:79`), `.spinner` (600ms linear), `.entrada-dialogo`/`.entrada-velo` (180ms, `translate(-50%,-50%) scale`, pensadas para elementos **centrados**), `.foco-visible`. Todas cubiertas por `@media (prefers-reduced-motion: reduce)` en `:149-159`.

**Tokens nuevos disponibles** (ADR 0026, a declarar en el mismo commit que los use por primera vez): `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`, `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)`.

**Componentes/pantallas relevantes:**
- `frontend/src/components/ui/Boton.tsx:14-24` — botón base (variantes primario/secundario/peligro), 0 press feedback.
- `frontend/src/components/ui/Dialogo.tsx:39` — botones de acción de diálogos.
- `frontend/src/components/ui/Retroalimentacion.tsx` — `useRetroalimentacion()` (hook: `mostrar(texto, tipo)`, `setTimeout` de 3000ms limpia `mensaje`) + `<Retroalimentacion mensaje={mensaje} />` (`if (!mensaje) return null`). Toast entra con `.entrada-lista`, sale sin animación.
- `frontend/src/components/MenuUsuario.tsx` — dropdown con state `abierto` (`:contenedorRef`, `:disparadorRef`), **ya tiene un state `cerrando` sin usar** (verificar líneas exactas al implementar); panel `{abierto && <div className="entrada-dialogo absolute right-0 top-12 ...">}`.
- `frontend/src/components/ui/dialog.tsx` — wrapper de `@radix-ui/react-dialog`; `Content` usa `.entrada-dialogo`, `Overlay` usa `.entrada-velo`; Radix desmonta ambos sin animación de salida (comentario propio en el archivo reconoce la limitación).
- Botones de regreso / tarjetas / filas clicables sin feedback: `features/asesorias/components/TarjetaAsesoria.tsx:88`, `screens/Home.tsx:25`, `features/asesorias/screens/AgendarAsesoria.tsx:141,166,236`, `OfertaAsesorias.tsx:104`, `AdminAsesorias.tsx:114,168`, `AdminOfertaMateria.tsx:130`, `MiHorario.tsx:238`, `MisMaterias.tsx:74`.
- Hover sin transición: `MisMaterias.tsx:88`, `MiHorario.tsx:238`, `features/asesorias/components/DialogoAgregarMateria.tsx:74`.
- Mensajes de error/éxito instantáneos: `screens/Login.tsx:102`, `screens/Landing.tsx:178`, `AgendarAsesoria.tsx:106`, `DetalleAsesoria.tsx:159,215`.
- Swap skeleton→contenido instantáneo: `Asesorias.tsx:148`, `OfertaAsesorias.tsx:87`, `AdminAsesores.tsx:45`, `MiHorario.tsx:219`, `AdminAsesorDetalle.tsx:47,87`.
- Listas/grids sin `.entrada-lista`: `screens/Home.tsx:34` (grid de servicios), `OfertaAsesorias.tsx:67,99`, `AgendarAsesoria.tsx:117,136`, `MisMaterias.tsx:68`, `MiHorario.tsx:201,208,227`, `AdminAsesorias.tsx:114,168`, `DetalleAsesoria.tsx:90`, `DialogoAgregarMateria.tsx:71`.
- Pantallas estáticas de baja frecuencia: `screens/NoEncontrado.tsx:208-223`, `screens/Login.tsx:85-127`, `screens/Landing.tsx:162-197`.

---

## Decisiones de arquitectura

| Decisión | Elegida | Alternativa descartada | Por qué |
|---|---|---|---|
| Salida animada de toast/dropdown/modal | **Reusar el patrón `cerrando`** (ya presente sin usar en `MenuUsuario.tsx`): al pedir el cierre, se activa un state `cerrando=true` que dispara la clase de salida; un `setTimeout` igual a la duración de esa clase ejecuta el desmontaje/`onOpenChange(false)` real | Adoptar `@radix-ui/react-toast` o una librería de animación para manejar exit-then-unmount | Mismo argumento de [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md): una dependencia nueva no se paga por 3 componentes. El patrón ya existe a medias en el código (state muerto en `MenuUsuario`); esta spec lo completa y lo replica, no inventa uno nuevo. |
| Clases de press feedback | **Dos clases compartidas** en `index.css`: `.presionable` (botones/tiles independientes, `scale(0.97)`) y `.fila-interactiva` (filas/tarjetas de ancho completo, `scale(0.99)` + `background-color` en hover) | `active:` inline por componente vía Tailwind | Mismo criterio que `.foco-visible` (`index.css:144-147`, comentario explícito "declarada una vez aquí... en vez de repetir"): 15+ sitios comparten el mismo comportamiento, una clase declarada una vez es la convención ya establecida en este archivo. |
| Alcance del deleite | **Solo `NoEncontrado` y `Landing`** reciben la clase nueva `.entrada-deleite` (scale 0.95→1 + translateY(12px), 400ms `--ease-out`, stagger 70ms). **`Login` usa `.entrada-lista` existente**, sin clase nueva | Dar a las tres pantallas el mismo tratamiento "delight" | `Login` se revisita cada vez que expira una sesión o hay logout explícito — más frecuente que un 404 real o la primera visita a la landing. El gate de frecuencia (`find-animation-opportunities`) baja su tier de "rare/first-time" a "occasional"; se mantiene conservador y coherente con la personalidad "dashboard serio". |
| Stagger del grid de `Home` | **Reusar `.entrada-lista` con el mismo tope de 10 ítems** ya convencionado (`TarjetaAsesoria.tsx:82`) | Crear una animación de entrada distinta para el grid de servicios | `Home` se ve varias veces por sesión (tier tens/day de la tabla de frecuencia) — motion apenas perceptible es lo único admisible ahí; usar la misma clase ya calibrada evita inventar un movimiento más notorio para una superficie de alta frecuencia. |
| `transform-origin` del dropdown de usuario | Nuevas keyframes `entrada-menu`/`salida-menu` con `transform-origin: top right`, sin `translate(-50%,-50%)` | Seguir reusando `.entrada-dialogo` | `.entrada-dialogo` fue diseñada para un elemento centrado en viewport (`position: fixed; translate(-50%,-50%)`); el panel del menú está anclado `absolute right-0 top-12` al disparador — aplicarle esa transformación es un bug latente de posicionamiento, no solo una animación subóptima. |
| Velocidad de entrada vs. salida | **Salida más rápida que la entrada** en todo par entrada/salida nuevo (dropdown: 180ms entra / 140ms sale; toast: 300ms entra / 200ms sale) | Misma duración en ambos sentidos | Regla explícita de `emil-design-eng`: el sistema debe sentirse responsivo al cerrar/descartar, aunque haya sido deliberado al abrir. |

---

## Catálogo de animaciones

Cada fila: Ubicación → Hoy → Propósito → Frecuencia → Motion exacto (clase/valores a implementar). Todas pasan el gate de 4 preguntas.

### A. Press feedback (`Feedback`)

| # | Ubicación | Hoy | Frecuencia | Motion exacto |
|---|---|---|---|---|
| A1 | `components/ui/Boton.tsx:19` (className del `<button>`) | Sin `:active`, sin `transition` | Tens/día | Añadir clase `.presionable` a la nueva clase compartida en `index.css`: `.presionable { transition: transform 160ms var(--ease-out); } .presionable:active:not(:disabled) { transform: scale(0.97); }`. Aplicar a `Boton.tsx` y a los botones de acción de `Dialogo.tsx:39`. |
| A2 | Tiles/tarjetas independientes: `screens/Home.tsx:25` (tile SAE) | Sin feedback | Ocasional (pocas veces por sesión) | `.presionable` (mismo scale 0.97) |
| A3 | Filas/tarjetas de ancho completo: `TarjetaAsesoria.tsx:88`, `AgendarAsesoria.tsx:141,166,236`, `OfertaAsesorias.tsx:104`, `AdminAsesorias.tsx:114,168`, `AdminOfertaMateria.tsx:130`, `MiHorario.tsx:238`, `MisMaterias.tsx:74` | Sin feedback | Tens/día en las más usadas (listas de asesorías) | Clase compartida `.fila-interactiva`: `transition: transform 160ms var(--ease-out), background-color 150ms ease; } .fila-interactiva:active:not(:disabled) { transform: scale(0.99); }` — scale más sutil que `.presionable` porque son elementos anchos (evita que el borde "salte" visualmente). |
| A4 | Hover sin transición: `MisMaterias.tsx:88`, `MiHorario.tsx:238`, `DialogoAgregarMateria.tsx:74` | `hover:bg-surface-container-high` sin transición | Tens/día | Incluido en `.fila-interactiva` de A3 (mismo elemento en los 3 casos): `@media (hover: hover) and (pointer: fine) { .fila-interactiva:hover { background-color: var(--color-surface-container-high); } }` |

### B. Salidas simétricas (`Spatial consistency` / `Preventing jarring change`)

| # | Ubicación | Hoy | Frecuencia | Motion exacto |
|---|---|---|---|---|
| B1 | `components/ui/Retroalimentacion.tsx` | Entra con `.entrada-lista` (300ms), sale al instante (`setTimeout` limpia `mensaje` sin transición) | Ocasional | Nueva keyframe `@keyframes salida-toast { from { opacity:1; transform: translateY(0); } to { opacity:0; transform: translateY(8px); } }` + clase `.salida-toast { animation: salida-toast 200ms var(--ease-out) forwards; }`. En el hook: `mostrar()` programa `saliendo=true` a los 2700ms y limpia `mensaje` a los 2900ms (200ms después, igual a la duración de `.salida-toast`). El componente aplica `.salida-toast` cuando `saliendo` es true. |
| B2 | `components/MenuUsuario.tsx` (panel del dropdown) | Usa `.entrada-dialogo` (`translate(-50%,-50%)`, pensada para modal centrado); state `cerrando` existe pero no anima nada | Ocasional | Nuevas keyframes: `@keyframes entrada-menu { from { opacity:0; transform: scale(0.95); } to { opacity:1; transform: scale(1); } }` / `@keyframes salida-menu { from { opacity:1; transform: scale(1); } to { opacity:0; transform: scale(0.95); } }`. Clases: `.entrada-menu { transform-origin: top right; animation: entrada-menu 180ms var(--ease-drawer); }` / `.salida-menu { transform-origin: top right; animation: salida-menu 140ms var(--ease-out) forwards; }`. El state `cerrando` ya existente pasa a controlar cuál clase se aplica y el `setTimeout` (140ms) antes de `setAbierto(false)`. |
| B3 | `components/ui/dialog.tsx` (`Content`/`Overlay` de Radix) | `.entrada-dialogo`/`.entrada-velo` en apertura; Radix desmonta sin exit | Ocasional | Mismo patrón `cerrando` que B2, adaptado al wrapper de Radix: interceptar `onOpenChange(false)`, poner `cerrando=true`, aplicar `.salida-dialogo`/`.salida-velo` nuevas (reverse de las de entrada, 150ms `var(--ease-out)`), y tras 150ms invocar el `onOpenChange(false)` real recibido por props. |

### C. Estado sin transición (`Preventing jarring change` / `State indication`)

| # | Ubicación | Hoy | Frecuencia | Motion exacto |
|---|---|---|---|---|
| C1 | Mensajes de error/éxito: `Login.tsx:102`, `Landing.tsx:178`, `AgendarAsesoria.tsx:106`, `DetalleAsesoria.tsx:159,215` | `{error && <p role="alert">...}` aparece de golpe | Ocasional (solo en fallo) | Añadir clase existente `.entrada-lista` (sin `animationDelay`, 300ms `ease-out`) al `<p>`. No requiere clase nueva. |
| C2 | Swap skeleton→contenido: `Asesorias.tsx:148`, `OfertaAsesorias.tsx:87`, `AdminAsesores.tsx:45`, `MiHorario.tsx:219`, `AdminAsesorDetalle.tsx:47,87` | El contenido real reemplaza al skeleton en el mismo tick, sin transición | Ocasional (cada carga) | Envolver el contenido real (no el skeleton) con `.entrada-lista` — el fade+translateY(8px) de 300ms en la entrada del contenido real es suficiente para suavizar el swap; no se anima la salida del skeleton (se desmonta junto con el condicional, es instantáneo por diseño — el contenido que entra ya cubre el "jarring change"). |
| C3 | Listas/grids sin stagger: `Home.tsx:34`, `OfertaAsesorias.tsx:67,99`, `AgendarAsesoria.tsx:117,136`, `MisMaterias.tsx:68`, `MiHorario.tsx:201,208,227`, `AdminAsesorias.tsx:114,168`, `DetalleAsesoria.tsx:90`, `DialogoAgregarMateria.tsx:71` | Aparecen todos a la vez | Ocasional (algunas, ej. `Home`, tens/día) | Aplicar el patrón exacto ya en uso en `TarjetaAsesoria.tsx:82`: `className="entrada-lista" style={{ animationDelay: \`${Math.min(indice, 10) * 30}ms\` }}` a cada `<li>`/`<div>` del `.map()`. Ningún token ni clase nueva — es replicar el patrón existente a los sitios que faltan. |

### D. Deleite (`Delight`, solo tier rare/first-time)

| # | Ubicación | Hoy | Frecuencia | Motion exacto |
|---|---|---|---|---|
| D1 | `screens/NoEncontrado.tsx:208-223` (Logo, "404", título, texto, botón) | Estático | Rara | Nueva clase `.entrada-deleite`: `@keyframes entrada-deleite { from { opacity:0; transform: translateY(12px) scale(0.95); } to { opacity:1; transform: translateY(0) scale(1); } } .entrada-deleite { animation: entrada-deleite 400ms var(--ease-out) backwards; }`. Aplicar a los 5 elementos con `animationDelay` escalonado 70ms entre cada uno (`0, 70, 140, 210, 280ms`). |
| D2 | `screens/Landing.tsx:162-197` (Logo + branding + CTA) | Estático | Rara/primera vez (visitante anónimo) | Misma clase `.entrada-deleite`, mismo stagger 70ms, aplicado a Logo → título → subtítulo → botones. |

**Fuera de esta tabla, sin cambio:** `TarjetaAsesoria.tsx:79` (`.pulso-exito`) ya es el celebration existente — se mantiene como está, sirve de referencia de tono para D1/D2.

---

## Rechazado

- **Transiciones de ruta SPA** (`App.tsx`, `react-router-dom`) — **Rechazado: frecuencia.** La navegación entre pantallas ocurre decenas de veces por sesión, con una porción relevante disparada por el botón "atrás" del navegador (fuera del control de la app). Animar transiciones de ruta en una app de alta frecuencia de navegación las hace sentir más lentas, no mejores — mismo argumento que "nunca animar acciones de teclado" aplicado a navegación de sistema.
- **Indicador deslizante en `components/ui/tabs.tsx:38`** — **Rechazado: sin evidencia de frecuencia suficiente hoy.** Las tabs de Radix se usan en un número acotado de pantallas de asesorías; no hay evidencia de uso repetido que justifique el costo de mantenimiento de un indicador animado. Se puede reabrir si aparece una superficie de tabs de alto uso.
- **Parallax / mouse-tracking decorativo en `Landing.tsx`** — **Rechazado: función.** Aunque es la pantalla de marketing/primera impresión, el producto es un dashboard institucional serio, no un producto de consumo lúdico; decoración no funcional desentonaría con el resto de la app y con el copy formal ya presente (`Landing.tsx:169-174`).
- **Animación de datos leídos** (ninguna hoy, regla preventiva) — si en el futuro se agregan gráficas o tablas de datos en vivo (ej. dashboard de ocupación de asesorías), esos elementos no se animan por estilo — es información que el usuario está tratando de leer, no una superficie de feedback.

---

## Verdict

El frontend ya tenía la disciplina correcta (motion sobrio, `prefers-reduced-motion` cubierto, un patrón de stagger reutilizable) — lo que faltaba era **cobertura**, no dirección. El ítem de mayor palanca es **A1** (`Boton.tsx`): es el componente más reusado de la app y hoy no da ninguna señal de "te escuché" al presionar. El segundo grupo de mayor impacto es **B1-B3**: las tres superficies que ya animan su entrada (toast, menú, modal) se sienten rotas al cerrarse porque no hay salida — es la clase de bug de percepción que más se nota aunque nadie sepa nombrarlo. El plan de implementación (`docs/superpowers/plans/2026-08-14-animaciones-feedback-deleite-frontend-plan.md`) ordena las tasks por esa misma prioridad.
