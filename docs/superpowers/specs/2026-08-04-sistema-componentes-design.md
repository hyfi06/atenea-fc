## Sistema de componentes reutilizables — adopción del patrón shadcn/ui

**Status:** Approved
**Date:** 2026-08-04 (creada 2026-08-05)

### Context

El frontend nunca tomó formalmente una decisión sobre librería de componentes — es una omisión, no una ADR existente. En la práctica ya se instaló Radix headless (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`) y se estilizó a mano con Tailwind, pero sin ninguna capa de abstracción compartida.

Confirmado en código (no solo en el ledger del paso 3): el catálogo actual es pequeño — 4 primitivos en `components/ui/` (`Boton.tsx`, `InsigniaEstado.tsx`, `Retroalimentacion.tsx`, `Skeleton.tsx`) — y **los 4 diálogos de asesorías** (`DialogoCancelar.tsx`, `DialogoNuevoBloque.tsx`, `DialogoAgregarMateria.tsx`, `DialogoBloqueActivo.tsx`) **importan `@radix-ui/react-dialog` directo, cada uno reconstruyendo `Dialog.Root`/`Portal`/`Overlay`/`Content` desde cero** — sin ningún wrapper compartido. La convención de orden de botones fijada en el paso 3 de este mismo plan (2 acciones = fila; 3+ = columna, reversible arriba/destructivo en outline al medio/salir como texto plano al final) no tiene dónde vivir una sola vez — hoy se copiaría a mano en cada diálogo nuevo.

Hay además una inversión real ya hecha en tokens propios ([ADR 0014](../../decisions/0014-tokens-logo-iconos-frontend.md)): paleta Material 3 dark declarada como `--color-{role}` bajo `@theme` en `frontend/src/index.css` (Tailwind v4, CSS-first, sin `tailwind.config.js`), más un sistema de motion propio (`@keyframes shimmer/entrada-lista/pulso-exito/girar`) en el mismo archivo.

Dos variables del contexto del proyecto pesaron en la decisión:

- **Crecimiento esperado:** "moderado y constante" — asesorías fue el primer servicio de la SAE integrado (ver `CLAUDE.md`: "los servicios se integran de forma incremental"), van a seguir apareciendo pantallas y diálogos nuevos por cada servicio que se sume.
- **Quién mantiene el frontend:** el usuario, en varias sesiones, apoyándose en subagentes — no un equipo humano que crece. La prioridad real de "documentar el patrón" es que una sesión nueva (o un subagente) lo pueda aplicar barato, sin releer mucho código ni inferir de documentación externa — economía de contexto, no onboarding humano tradicional.

Se evaluaron tres opciones (detalle de trade-offs abajo y en [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)):

1. Formalizar el statu quo — Radix headless + Tailwind a mano, extrayendo la duplicación actual a un wrapper compartido, sin dependencias nuevas.
2. Adoptar el patrón shadcn/ui — generador que copia código fuente (Radix + `class-variance-authority`) directo al repo, no una dependencia de UI en runtime.
3. Librería completa (MUI/Chakra/Ant).

### Decisions captured

1. **Se adopta el patrón shadcn/ui** sobre Radix + Tailwind ya existente, en vez de formalizar el statu quo sin más o traer una librería completa. Ver [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md) para el detalle y las alternativas descartadas con su razón.
2. **Mapeo de tokens:** shadcn asume su propio vocabulario de variables CSS (`--background`, `--primary`, `--destructive`, `--border`, `--ring`, etc.). En vez de que los componentes generados usen esos nombres tal cual — lo que introduciría una segunda paleta paralela a la de ADR 0014 — se agrega un bloque de alias en `frontend/src/index.css`, después del `@theme` existente, donde cada nombre-shadcn apunta a un token M3 ya definido (p. ej. `--background: var(--color-surface)`, `--primary: var(--color-primary)`, `--destructive: var(--color-error)`, `--border: var(--color-outline)`). ADR 0014 sigue siendo la fuente canónica de color; shadcn nunca la reemplaza ni la duplica.
3. **Estructura de carpetas: una sola capa, sin separación por idioma.** `components/ui/` sigue siendo la carpeta única. El output del CLI de shadcn (`dialog.tsx`, `tabs.tsx`, ...) se agrega ahí directo, con los nombres que el CLI genera (inglés, convención del ecosistema shadcn) — sin subcarpeta separada ni traducción forzada a español. Los componentes propios existentes (`Boton.tsx`, `InsigniaEstado.tsx`, ...) conviven en la misma carpeta, sin renombrarse. Decisión explícita del checkpoint: "inglés está bien para el proyecto" — se descartó una capa `components/ui/shadcn/` con wrappers en español por agregar indirección sin beneficio real.

   Regla de una línea para retomar esto en una sesión nueva: *`components/ui/` es plana — primitivos de shadcn y componentes propios conviven ahí; las features importan de esa carpeta, no reimplementan Radix directo.*
4. **Qué migra ahora:** los 4 diálogos de asesorías se consolidan en un componente compartido (nombre exacto a definir en el plan de implementación, p. ej. `ConfirmDialog.tsx`) que envuelve el `dialog.tsx` generado por shadcn y codifica **una sola vez** la convención de orden de botones del paso 3, en vez de copiarse en cada diálogo. La pantalla "Mi horario" (tabs por día, rediseño de `DisponibilidadAsesor` del paso 3, aún no implementada) usa el `tabs.tsx` de shadcn desde el inicio, no una implementación a mano.
5. **Qué NO migra:** `Boton.tsx`, `InsigniaEstado.tsx`, `Retroalimentacion.tsx`, `Skeleton.tsx` quedan exactamente como están. No están duplicados en ningún lado — migrarlos ahora sería refactor no relacionado al problema real que esta decisión resuelve (YAGNI). Se reevalúa cada uno individualmente el día que necesite algo que shadcn ya resuelve mejor (p. ej. `asChild`/composición), no como parte de este trabajo.
6. **Instalación on-demand, no de golpe.** `pnpm dlx shadcn@latest init` una sola vez (detecta Tailwind v4 + el bloque `@theme` existente, genera `components.json`). A partir de ahí, `pnpm dlx shadcn add <componente>` solo cuando una pantalla real lo necesita — no se instala el catálogo completo de shadcn por adelantado.

### Dependencias nuevas

| Paquete | Rol |
|---|---|
| `class-variance-authority` | Variantes de componentes (patrón `cva` que usa shadcn) |
| `clsx` | Combinar clases condicionalmente |
| `tailwind-merge` | Resolver conflictos de clases Tailwind al componer variantes |

Ninguna es un kit de UI en sí — son utilidades que shadcn usa internamente; el código de los componentes sigue viviendo en el repo, no en un paquete de terceros. Gestor de paquetes ya confirmado: `pnpm` (`frontend/pnpm-lock.yaml`).

### Fuera de alcance de este spec

- **Ejecución real** (paso 8 del plan): correr el CLI, escribir el bloque de alias de tokens, migrar los 4 diálogos al componente compartido, decidir su nombre exacto y su forma final de props.
- **Migración de `Boton`/`InsigniaEstado`/`Retroalimentacion`/`Skeleton`** — explícitamente fuera, ver decisión 5.
- **Set de íconos de servicios** (`ServiceIcons.tsx`) — ya decidido en ADR 0014, sin relación con esta decisión.

### Alternatives considered

1. **Formalizar el statu quo (Radix headless + Tailwind a mano, sin shadcn).** Resuelve la duplicación de hoy (un wrapper de `Dialog` compartido, cero dependencias nuevas) con el mínimo esfuerzo posible. Se descarta como opción principal porque no da vocabulario para el crecimiento esperado — cada primitivo nuevo (select, popover, tooltip, dropdown-menu, previsibles según lleguen más servicios de la SAE) se sigue escribiendo desde cero, cuando shadcn ya lo resuelve y lo deja como código propio igual de legible. Queda documentada como la alternativa más liviana si el ritmo de necesidad de componentes nuevos bajara del "moderado y constante" asumido aquí.
2. **Librería completa (MUI, Chakra, Ant Design).** Descartada: cada una trae su propio sistema de theming, en conflicto directo con la inversión ya hecha en ADR 0014 (paleta M3 como `@theme` CSS vars, logo e íconos a mano con `currentColor`). Además, sus componentes viven en `node_modules` como caja negra — una sesión nueva (o un subagente) no puede leer la fuente real del componente, tiene que inferir su API de la documentación de la librería. Es exactamente el tipo de gasto de contexto que este plan busca evitar, dado que quien mantiene el frontend son sesiones y subagentes, no un equipo humano que crece (ver Context).
3. **Separar componentes shadcn (inglés) de componentes propios (español) en carpetas distintas.** Se propuso durante el checkpoint y se descartó a pedido del usuario: agrega una capa de indirección (dos carpetas, una regla de cuándo traducir un nombre) sin beneficio real — "inglés está bien para el proyecto". Una sola carpeta plana (`components/ui/`) es más simple y sigue siendo igual de legible para una sesión nueva.
