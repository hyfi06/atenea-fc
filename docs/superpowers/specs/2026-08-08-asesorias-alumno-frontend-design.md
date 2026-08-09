# Diseño de Spec — Vista unificada de Asesorías (lado alumno + asesor + admin futuro)

**Fecha:** 2026-08-08
**Status:** Approved

---

## Contexto

### Por qué este plan

El frontend de asesorías cubre hoy sólo el **lado asesor**: `SesionesAsesor.tsx` (tabs Próximas/Historial + botones Mis materias / Mi horario), `MisMaterias`, `MiHorario`, `DetalleAsesoria`, todo bajo `/asesorias*` protegido por `RutaDeAsesor` (asesor-only, redirige no-asesores a `/home`). El lado alumno estaba diferido a Fase 2 ([spec de asesor](2026-08-01-asesorias-frontend-asesor-design.md), decisiones de alcance). Esta spec es esa fase, pero con un cambio de diseño validado en brainstorming: en vez de una pantalla de alumno separada, se **unifica** la pantalla de asesorías para que una sola vista y ruta sirva a alumno, asesor y (futuro) admin, diferenciando **acciones** y **contenido de tarjeta** por rol.

La API del lado alumno se diseña en la spec gemela [`2026-08-08-asesorias-alumno-api-design.md`](2026-08-08-asesorias-alumno-api-design.md) ([ADR 0021](../../decisions/0021-asesorias-alumno-api.md)): endpoints de oferta, asesores-por-materia, disponibilidad-por-asesor, carrera escribible al agendar y ocultamiento de `notas`. Este plan asume esos contratos.

### Estado actual (referencias verificadas)
- `SesionesAsesor.tsx:9` consume `useMisAsesorias()` → `GET /api/asesorias/asesorias/`, que ya **une ambos lados por rol** (`views.py:173-180`). La misma query sirve a alumno y asesor sin cambios.
- `RutaDeAsesor` (`auth/RutaProtegida.tsx:14`) exige `useEsAsesor()`. `useEsAlumno()` ya existe (`auth/rol.ts:18`) leyendo `useAuth().roles`.
- `App.tsx:20-51`: `/asesorias`, `/asesorias/materias`, `/asesorias/horario`, `/asesorias/:id`, todas con `RutaDeAsesor`.
- `TarjetaAsesoria.tsx:30` hardcodea `Alumno #{asesoria.alumno}`. El serializer ya expone `alumno_nombre`/`asesor_nombre` (`serializers.py:90-93`).
- Patrón de búsqueda+filtrado en cliente: `DialogoAgregarMateria.tsx:25` (`useMemo` + input controlado + lista con `aria-pressed`). `useMapaMaterias`/`useMapaCarreras` en `features/catalogo/api.ts:22-30`.
- Lógica pura reutilizable: `proximas`/`historial`/`semestreActual` (`features/asesorias/logica.ts`).

---

## Decisiones de alcance

1. **Este plan (a detalle):** vista unificada de asesorías. Alumno: botón *Nueva asesoría* → oferta → wizard de agendado; ambos roles: tabs Próximas/Historial. Ocultar notas al alumno en la tarjeta/detalle.
2. **Reuso para asesor:** la pantalla unificada conserva los botones *Mis materias* / *Mi horario* para el asesor; sus pantallas (`MisMaterias`, `MiHorario`, `DetalleAsesoria`) no se rediseñan.
3. **Fuera de este plan:** vista de admin (mostrar ambos nombres, ver notas) — la `TarjetaAsesoria` se diseña para soportarla, pero el rol/ruta admin es trabajo posterior.

---

## Decisiones de arquitectura

| Decisión | Elegida | Alternativa descartada | Por qué |
|---|---|---|---|
| Estructura de la vista | **Una pantalla unificada** en `/asesorias` que ramifica por rol | Pantalla de alumno separada (`/asesorias-alumno`) | La lista (`useMisAsesorias`) ya es compartida por rol en el backend; una sola vista evita duplicar tabs/lista y prepara la vista de admin. Deriva de la aclaración explícita del usuario. |
| Guard de ruta | **`RutaDeAsesorias`**: autenticado y (alumno **o** asesor); externo → `/home` | Mantener `RutaDeAsesor` y añadir guard paralelo de alumno | Un solo guard para una sola vista; `RutaDeAsesor` se conserva sólo para las subrutas exclusivas de asesor (`/materias`, `/horario`). |
| Acciones por rol | Encabezado condicional: asesor → *Mis materias*/*Mi horario*; alumno → *Nueva asesoría* (`useEsAsesor()`/`useEsAlumno()`) | Dos componentes de encabezado distintos | Un condicional simple sobre roles ya disponibles en `AuthContext`; sin nueva fuente de verdad de rol. |
| Tarjeta de asesoría | `TarjetaAsesoria` muestra el **contraparte** (alumno ve asesor, asesor ve alumno) vía `asesor_nombre`/`alumno_nombre`; admin mostrará ambos | Tarjetas separadas por rol | Un mismo shape reutilizable en las tres vistas; elimina el hardcode `Alumno #{id}`. |
| Notas del asesor | El alumno **nunca** ve `notas` (ausente del payload por ADR 0021; la UI tampoco lo renderiza) | Ocultar sólo en frontend | Defensa en profundidad: el backend deja de enviarlo y el frontend no lo referencia. |
| Modelo del wizard de agendado | **Stepper, misma ruta**: estado interno de paso, Atrás/Siguiente; sin rutas por paso | Ruta por paso (deep-link por paso) | Menos código de ruteo, conserva contexto; el flujo es lineal y corto (asesor → día → bloque → carrera). Decisión explícita del usuario. |
| Selector de carrera | Selector en el último paso, **autoseleccionado** con la única carrera del alumno hoy | Omitir el selector (auto invisible) | Deja la UI lista para múltiples carreras ([deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md)) sin rehacer el paso; con un dato se preselecciona y no estorba. |
| Oferta: filtro y búsqueda | Filtro por carrera (select) + búsqueda por nombre (input), patrón `useMemo` de `DialogoAgregarMateria` | Filtrado sólo en servidor | Reutiliza un patrón ya probado; `GET /oferta/` también acepta `carrera`/`buscar`, así que el filtrado puede ser servidor o cliente según volumen (ver Pantallas). |
| Estado de servidor / motion / diálogos | TanStack Query, CSS puro, `Dialogo` compartido | (igual que spec de asesor) | Coherencia con ADR 0014 y [ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md); no se introducen dependencias nuevas. |

---

## Pantallas y flujos

### 1. Vista unificada de asesorías — `Asesorias.tsx` (renombra `SesionesAsesor.tsx`)
**Ruta:** `/asesorias` (guard `RutaDeAsesorias`).
**Encabezado por rol:**
- Asesor: botones *Mis materias* (`/asesorias/materias`) y *Mi horario* (`/asesorias/horario`) — sin cambios.
- Alumno: botón primario *Nueva asesoría* → `/asesorias/nueva`.
**Cuerpo (ambos roles):** tabs `Próximas` / `Historial` sobre `useMisAsesorias()`; `proximas()`/`historial()` de `logica.ts`. Historial: subtabs por semestre alimentados por `GET /asesorias/semestres/`, lista filtrada con `?semestre=`.
**Tarjeta:** `TarjetaAsesoria` con nombre del contraparte según rol.

### 2. Oferta de asesorías — `OfertaAsesorias.tsx` (sólo alumno)
**Ruta:** `/asesorias/nueva`.
**Flujo:** `GET /oferta/?carrera=&buscar=` → lista de materias con `num_asesores`. Filtro por carrera (select con `useMapaCarreras`) + búsqueda por nombre (input, `useMemo` sobre el resultado). Seleccionar materia → navega al wizard con `materia_id`. Nombres de materia truncados según convención (1 línea + ellipsis + `title`).

### 3. Wizard de agendado — `AgendarAsesoria.tsx` (sólo alumno)
**Ruta:** `/asesorias/nueva/:materiaId` (stepper interno, sin ruta por paso).
**Pasos:**
1. **Asesor** — `GET /oferta/{materia}/asesores/` → lista seleccionable (`aria-pressed`), muestra nombre, área, formatos.
2. **Día** — `GET /disponibilidad/buscar/?materia=&asesor=<registro>` → resultados agrupados por `fecha` (dos semanas). Selección de día. La agrupación por fecha es lógica pura testeable en `logica.ts` (p.ej. `agruparPorDia(resultados)`).
3. **Bloque** — bloques del día elegido (hora_inicio/fin, formato, ubicación/liga).
4. **Carrera + confirmar** — selector de carrera (autoseleccionado) + resumen; confirmación con `Dialogo` de **2 acciones** (izquierda *Volver*, derecha *Agendar* primario). `POST /asesorias/` con `{disponibilidad, fecha, materia, carrera}`.
**Navegación:** botón *Atrás* entre pasos; *Siguiente* deshabilitado hasta que el paso tenga selección.
**Manejo de errores:** `409` → mensaje "ese horario ya fue tomado", volver al paso de día e invalidar la disponibilidad; `400` (validación) → mensaje del backend con `Retroalimentacion`.

### 4. Post-agendado
`invalidateQueries({ queryKey: ['asesorias'] })` → navegar a `/asesorias` (tab Próximas) con **foco en la tarjeta nueva** (por `id`, vía `ref` + `scrollIntoView` + `focus()`) y animación `pulso-exito`. Toast de éxito con `useRetroalimentacion`.

---

## API frontend (nuevos hooks en `features/asesorias/api.ts`)

Mismo patrón `apiGet/apiPost` + query keys planas + `invalidateQueries`:
- `useOferta(filtros)` → `['oferta', filtros]`.
- `useAsesoresDeMateria(materiaId)` → `['oferta', materiaId, 'asesores']`.
- `useDisponibilidadDeAsesor(materiaId, registroId)` → `['disponibilidad', materiaId, registroId]`.
- `useAgendarAsesoria()` → mutation `POST /asesorias/`, `onSuccess` invalida `['asesorias']`.

Tipos nuevos en `src/api/types.ts`: `MateriaOferta`, `AsesorDisponible`, `SlotDisponibilidad` (extiende el resultado de búsqueda con `registro_id`/`asesor_nombre`).

---

## Componentes y reuso

**Reusar (no reimplementar):** `Tabs` (`components/ui/tabs`), `Boton`, `Dialogo`, `Retroalimentacion`/`useRetroalimentacion`, `Skeleton`, `InsigniaEstado`, `useMapaMaterias`/`useMapaCarreras`, tokens MD3 (`index.css`), `.foco-visible`, y `proximas`/`historial`/`semestreActual` de `logica.ts`.

**Modificar:**
- `TarjetaAsesoria.tsx` — contraparte por rol; nunca renderiza `notas`.
- `App.tsx` — `/asesorias` pasa a `RutaDeAsesorias`; nuevas rutas `/asesorias/nueva` y `/asesorias/nueva/:materiaId`.
- `auth/RutaProtegida.tsx` — añadir `RutaDeAsesorias` (autenticado + alumno-o-asesor); `RutaDeAsesor` se conserva para `/materias` y `/horario`.

**Crear:** `OfertaAsesorias.tsx`, `AgendarAsesoria.tsx` (+ componentes de paso si conviene), hooks nuevos, lógica pura de agrupación por día en `logica.ts`.

**Convenciones a respetar:** convención de diálogos 2-vs-3+ acciones ([ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)); truncamiento de materias (1 línea+ellipsis en chips/filas, `line-clamp:2` en encabezados); toque mínimo 44×44; íconos de formato pin/monitor de `ServiceIcons.tsx`; motion CSS puro con `@media (prefers-reduced-motion)`.

---

## Testing

Vitest + Testing Library, tests colocados junto al archivo, hooks mockeados con `vi.spyOn`, `usuarioDePrueba` de `src/test/factories.ts`:
- **Vista unificada:** con rol alumno se ve *Nueva asesoría* y no *Mis materias*/*Mi horario*; con rol asesor, al revés; tabs Próximas/Historial visibles para ambos; historial con subtabs por semestre.
- **Guard:** externo (sin alumno ni asesor) → redirige a `/home`; no autenticado → `/login`.
- **Tarjeta:** como alumno muestra `asesor_nombre` y no `notas`; como asesor muestra `alumno_nombre`.
- **Oferta:** filtra por carrera y por búsqueda de nombre; materia sin asesores no navega a agendar.
- **Wizard:** avanzar requiere selección en cada paso; *Atrás* preserva selección previa; confirmar dispara `POST` con `{disponibilidad, fecha, materia, carrera}`; `409` regresa al paso de día.
- **Lógica pura:** `agruparPorDia` en `logica.test.ts` (dos semanas, orden por fecha, bloques por día).
- **Post-agendado:** invalida `['asesorias']` y navega a Próximas.

---

## Out of scope

- Vista de admin (ambos nombres + notas) — la tarjeta la soporta; rol/ruta admin, posterior.
- Múltiples carreras por alumno — [deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md); el selector queda listo, hoy autoselecciona.
- Paginación de oferta/listados — [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).
- Rediseño de `MisMaterias`/`MiHorario`/`DetalleAsesoria` — sin cambios en este plan.

---

## Self-review

- Sin placeholders/TBD: cada pantalla tiene ruta, flujo, endpoints y casos de prueba concretos; los contratos que consume están definidos en la spec de API gemela.
- Alcance cohesivo: una vista unificada + oferta + wizard del alumno; no rediseña las pantallas del asesor ni el admin.
- Sin contradicciones con specs previas: reutiliza `useMisAsesorias` (unión por rol de ADR 0017/deuda 0011 ya cerrada), el sistema de componentes de ADR 0020 y los tokens de ADR 0014; el ocultamiento de `notas` es coherente con ADR 0021.
- Consistente con patrones: TanStack Query + query keys planas, filtrado en cliente estilo `DialogoAgregarMateria`, guards espejo de `RutaProtegida`, lógica pura en `logica.ts` testeada aparte.
- Deuda referenciada, no duplicada: carrera → 0008; paginación → 0006. No se crea deuda nueva.
