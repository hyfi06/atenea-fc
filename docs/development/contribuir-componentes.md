# Contribuir componentes al frontend

Guía de referencia para agregar o modificar componentes en `frontend/src/components/` y `frontend/src/features/*/components/`. Pensada para retomarse en cualquier sesión (o subagente) sin releer el código completo — es la fuente de las convenciones, no una repetición de lo que ya está en [ADR 0014](../decisions/0014-tokens-logo-iconos-frontend.md) (tokens/logo/íconos) y [ADR 0020](../decisions/0020-sistema-componentes-shadcn.md) (patrón shadcn/ui, carpeta plana `components/ui/`) — léelas primero si algo aquí no tiene sentido sin ese contexto.

## Cuándo necesita revisión visual antes de código

Esto existe porque el flujo de asesorías se construyó sin visualización ni aprobación previa — ese fue el problema raíz que originó todo el plan de rediseño de login y componentes (`docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`). La regla:

**→ `superpowers:brainstorming` + mockup primero:**
- Pantalla o flujo nuevo (UX real, no solo un ajuste de estilo).
- Componente con lógica de interacción nueva (un patrón de diálogo, navegación o estado que no existe ya en el catálogo).

**→ directo a código:**
- Primitivo estructural agregado vía `pnpm dlx shadcn add <componente>` y usado tal cual (o con las variantes que shadcn ya define).
- Variante de un componente ya aprobado (mismo patrón de interacción, distinto contenido/color).
- Fix o ajuste puntual sobre algo existente.

Ante la duda, pesa hacia brainstorming primero — es más barato descartar un mockup que descartar código ya escrito.

## `components/ui/` vs específico de feature

- `frontend/src/components/ui/` — componentes sin conocimiento del dominio de negocio: no importan tipos de `api/types.ts` de un feature específico, no saben qué es una "asesoría" o una "materia". Primitivos de shadcn viven aquí. Ejemplo actual: `Boton.tsx`, `Skeleton.tsx`.
- `frontend/src/features/<feature>/components/` — componentes que sí conocen el dominio de ese feature (reciben/producen sus tipos, encapsulan su copy). Ejemplo actual: `TarjetaAsesoria.tsx`, `GrillaDisponibilidad.tsx`.
- Un componente puede vivir en `features/` y **componer** algo de `components/ui/` (p. ej. un diálogo específico de asesorías que envuelve el `Dialogo` compartido) — eso es lo esperado, no una excepción.
- `components/ui/` es plana (decisión de ADR 0020): no hay subcarpeta para separar shadcn de lo propio.

## Estructura de un componente nuevo

- **Nombre de archivo:** los primitivos generados por shadcn conservan el nombre que trae el CLI (minúsculas/kebab-case, p. ej. `dialog.tsx`, `dropdown-menu.tsx`) — no se traducen ni se renombran (ADR 0020). Los componentes propios del proyecto siguen la convención ya establecida: PascalCase (`Boton.tsx`, `InsigniaEstado.tsx`), nombre en español si es específico del dominio de Atenea.
- **Export:** nombrado (`export function Boton(...)`), no `export default` — única excepción existente es `App.tsx` (convención de punto de entrada de React Router, no aplica a componentes).
- **Props:** interfaz de TypeScript explícita; si envuelve un elemento nativo, extiende sus atributos en vez de reinventarlos (patrón ya usado: `interface BotonProps extends ButtonHTMLAttributes<HTMLButtonElement>`).
- **Tests:** co-localizados (`Componente.test.tsx` junto al componente) — patrón ya usado en `AuthContext.test.tsx`, `SesionesAsesor.test.tsx`. Gap conocido: ningún primitivo de `components/ui/` ni los 4 diálogos de asesorías tiene test hoy. No se corrige retroactivamente como parte de este documento, pero **todo componente nuevo con lógica propia (estado, validación, efectos) debe llevar al menos un test de comportamiento** — sigue `superpowers:test-driven-development` cuando la lógica lo amerite; un componente puramente presentacional (sin estado ni ramas) puede quedarse con un smoke test o ninguno si el costo no se justifica.

## Lineamientos de diseño

- **Color:** siempre a través de los tokens de ADR 0014 (`bg-primary`, `text-on-surface-variant`, etc.) — nunca un hex literal en un componente. Los primitivos de shadcn consumen esos mismos tokens vía el bloque de alias que define el paso 8 (`--primary: var(--color-primary)`, etc.); no se inventa una paleta paralela para shadcn.
- **Motion:** reusar lo que ya existe en `frontend/src/index.css` (`entrada-lista`/`salida-lista`, `pulso-exito`, `spinner`/`girar`, `skeleton`) antes de escribir un `@keyframes` nuevo. Si hace falta una animación nueva, debe respetar `prefers-reduced-motion` igual que las existentes (bloque `@media (prefers-reduced-motion: reduce)` al final de `index.css`).

## Checklist de accesibilidad

- **Foco visible:** gap real encontrado en el código actual — la única regla de foco en todo el proyecto (`Login.tsx`) usa `outline-none focus:border-primary`, sin un ring perceptible; no hay un patrón `:focus-visible` sistemático. A partir de este documento, **todo elemento interactivo nuevo necesita un estado de foco visible** (ring o cambio de color con suficiente contraste), no solo quitar el outline por defecto del navegador.
- **Live regions:** mensajes transitorios (confirmaciones, errores async) usan `role="status"` o `role="alert"` según si interrumpen o no — patrón ya usado en `Retroalimentacion.tsx`.
- **Decorativo:** elementos puramente visuales (skeletons, íconos sin significado propio) llevan `aria-hidden` — patrón ya usado en `Skeleton.tsx`.
- **Teclado:** si el componente compone Radix/shadcn, la navegación por teclado ya viene resuelta por la librería — no capturar/interceptar eventos de teclado que Radix ya maneja (foco atrapado en diálogos, `Esc` para cerrar, flechas en tabs).
- **Labels:** todo input/control lleva un label asociado (`htmlFor` o `aria-label`) — el placeholder nunca es el único label.
- **Contraste:** usar siempre el par `{rol}`/`on-{rol}` correcto de ADR 0014 juntos (p. ej. `bg-primary-container` con `text-on-primary-container`) — están pensados como pares de contraste AA; no mezclar el texto de un rol con el fondo de otro.

## Especificación ligera de componente

Para los casos que sí requieren revisión visual (ver arriba), no hace falta un archivo formal en `docs/superpowers/specs/` — alcanza con una tabla corta en la conversación de brainstorming, cubriendo:

- **Variantes** × propiedad visual relevante (igual que `Boton` ya distingue `primario`/`secundario`/`peligro`).
- **Estados**, en orden de prioridad cuando compiten entre sí: `disabled > loading > active > focus > hover > default`.
- **Anatomía**: qué elementos lleva y en qué orden (p. ej. la convención de orden de botones en diálogos de 3+ acciones, fijada en el paso 3 del plan: reversible arriba, destructivo en outline al medio, salir como texto plano al final).
- **Casos de error**, si el componente maneja datos asíncronos.

Esa tabla es el insumo que ya usa `superpowers:writing-plans` al convertir la spec aprobada en tareas — no hace falta reescribirla en otro formato.
