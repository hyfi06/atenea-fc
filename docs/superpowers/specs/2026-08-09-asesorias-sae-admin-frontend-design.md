# Diseño de Spec — Vista de administración SAE de Asesorías (frontend, solo lectura)

**Fecha:** 2026-08-09
**Status:** Approved

---

## Contexto

### Por qué este plan

El frontend de asesorías sirve hoy a alumno y asesor bajo `/asesorias*`, con guardas `RutaDeAsesorias` (alumno **o** asesor) y `RutaDeAsesor` (asesor). **No existe ningún área de administración** para la SAE (búsqueda repo-wide de `admin|SAE|staff` → 0 resultados). Esta spec añade el **área SAE de solo lectura**: supervisar asesorías agendadas e históricas, consultar la oferta materias → asesores → disponibilidad sin agendar, y navegar un directorio de asesores con el detalle de sus materias y horarios reutilizando las pantallas del asesor en modo solo-lectura.

La API la define la spec gemela [`2026-08-09-asesorias-sae-admin-api-design.md`](2026-08-09-asesorias-sae-admin-api-design.md) ([ADR 0023](../../decisions/0023-asesorias-sae-admin-api.md)): rol `'sae'`, endpoints `/admin/asesorias|semestres|asesores|alumnos`, y ampliación de oferta/búsqueda a `EsAlumnoOMiembroSAE`. Este plan asume esos contratos.

> **Nota de proceso:** las pantallas y componentes nuevos de esta área requieren **flujo de aprobación y discusión mediante artefactos** (mockups) antes de implementar; el plan de implementación lo hará explícito por pantalla.

### Estado actual (referencias verificadas)

- Guardas y roles: `auth/RutaProtegida.tsx` (`RutaDeAsesorias`, `RutaDeAsesor`), `auth/rol.ts` (`useEsAsesor`/`useEsAlumno` sobre `useAuth().roles`). El tipo `RolUsuario` (`api/types.ts`) admite `'academico'` sin uso; se añadirá `'sae'`.
- `features/asesorias/screens/Asesorias.tsx` — hub por rol (tabs Próximas/Historial + pills por semestre) con `useMisAsesorias`, `useSemestres`, `useAsesoriasDeSemestre`.
- `OfertaAsesorias.tsx` (filtro carrera + búsqueda materia, `useOferta`) y `AgendarAsesoria.tsx` (wizard asesor → día → bloque → carrera, `useAsesoresDeMateria`, `useDisponibilidadDeAsesor`, `agruparPorDia`).
- `MisMaterias.tsx` (`useRegistroDelSemestre`, diálogos agregar/quitar) y `MiHorario.tsx` (`Tabs` de 7 días, slots de 30 min, autosave) — pantallas del asesor a reutilizar en solo-lectura.
- `TarjetaAsesoria.tsx` — tarjeta con rama **interactiva** (asesor → detalle) y **read-only div** (no-asesor); muestra el contraparte por rol.
- Reuso directo: `components/ui/` (`tabs`, `InsigniaEstado`, `Skeleton`, `Boton`), helpers puros de `features/asesorias/logica.ts` (`proximas`, `historial`, `agruparPorDia`, `slotsDelDia`, `semestreActual`), mapas de catálogo `useMapaMaterias`/`useMapaCarreras`.

---

## Decisiones de alcance

1. **Este plan (a detalle):** área SAE de solo lectura en `/sae/asesorias` (agendadas + histórico + consulta de oferta) y `/sae/asesores` (directorio + detalle). Sin acciones de escritura.
2. **Reuso para el detalle del asesor:** `MisMaterias`/`MiHorario` se parametrizan con un modo **solo-lectura** + fuente de datos admin (asesor seleccionado); no se rediseñan.
3. **Fuera de este plan:** cualquier acción de administración con escritura (cancelar, reasignar, editar). Notas **sí** se muestran al SAE.

---

## Decisiones de arquitectura

| Decisión | Elegida | Alternativa descartada | Por qué |
|---|---|---|---|
| Rol y guarda | `useEsMiembroSAE()` + **`RutaDeSAE`** (autenticado + `sae`; externo → `/home`) | Reusar `RutaDeAsesor` con más roles | Guarda propia, espejo de las existentes; el SAE es una persona distinta con su propia área. |
| Ubicación de rutas | Área propia bajo **`/sae/*`** (`/sae/asesorias`, `/sae/asesores`) | Subrutas bajo `/asesorias` | El SAE no comparte la vista de alumno/asesor; separar el árbol evita ramas de rol en pantallas ya densas. Decisión explícita del usuario. |
| Agendadas + histórico | Pantalla `AdminAsesorias` con `Tabs` Próximas/Historial (pills por semestre) + filtros por asesor (select) y alumno (búsqueda) | Reusar `Asesorias.tsx` con más ramas de rol | La fuente de datos es admin-wide (`/admin/asesorias/`), no `useMisAsesorias`; una pantalla dedicada mantiene ambas limpias. Reusa `Tabs`, `TarjetaAsesoria`, `InsigniaEstado`, `logica.ts`. |
| Tarjeta admin | `TarjetaAsesoria` en modo admin: muestra **ambos** nombres y **`notas`** | Tarjeta nueva | La tarjeta ya distingue contraparte por rol; se extiende para el caso SAE (ambos + notas) sin duplicar. |
| Filtro asesor / alumno | Asesor = **select** (`/admin/asesores/`); alumno = **búsqueda/autocompletar** (`/admin/alumnos/?buscar=`) | Ambos select | El conjunto de alumnos es grande; búsqueda evita un select inmanejable. Decisión de la spec de API. |
| Consulta de oferta | Reusar `OfertaAsesorias` en **modo consulta** → vista read-only de asesores + disponibilidad (sin paso de confirmar/agendar) | Reusar el wizard completo | El SAE no agenda; el flujo termina en visualización. Reusa el listado de oferta y `agruparPorDia`, elimina el `POST` y el `Dialogo` de confirmación. |
| Detalle de asesor | Reusar `MisMaterias`/`MiHorario` con prop `soloLectura` + datos de `/admin/asesores/{id}/` | Componentes read-only nuevos | Máxima paridad visual, sin duplicar layout; en modo lectura se ocultan diálogos y los chips no son interactivos. Decisión explícita del usuario. |
| Estado de servidor / motion / diálogos | TanStack Query, CSS puro, componentes `ui/` existentes | dependencias nuevas | Coherencia con [ADR 0014](../../decisions/0014-tokens-logo-iconos-frontend.md)/[ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md). |

---

## Pantallas y flujos

### 0. Entrada
- `useEsMiembroSAE()` en `auth/rol.ts` (`roles.includes('sae')`); `'sae'` añadido a `RolUsuario`.
- `RutaDeSAE` en `RutaProtegida.tsx` (espejo de `RutaDeAsesor`).
- Tarjeta de servicio condicional en `screens/Home.tsx` para el SAE → `/sae/asesorias`.
- Rutas nuevas en `App.tsx` bajo `RutaDeSAE`: `/sae/asesorias`, `/sae/asesorias/oferta`, `/sae/asesorias/oferta/:materiaId`, `/sae/asesores`, `/sae/asesores/:asesorId`.

### 1. Asesorías agendadas + histórico — `AdminAsesorias.tsx`
**Ruta:** `/sae/asesorias`.
**Cuerpo:** `Tabs` Próximas / Historial. Próximas = `useAdminAsesorias()` (default próximas agendadas). Historial = subtabs por semestre de `useAdminSemestres()` + `useAdminAsesorias({semestre})`.
**Filtros:** select de asesor (`useAdminAsesores`) + búsqueda de alumno (`useBuscarAlumnos`, autocompletar); ambos se traducen a `?asesor=`/`?alumno=`.
**Tarjeta:** `TarjetaAsesoria` en modo admin (ambos nombres + `notas`, no interactiva — no hay `/sae/asesorias/:id` en esta fase). Enlace a "Nueva asesoría (consulta)" → `/sae/asesorias/oferta`.

### 2. Consulta de oferta — `AdminOferta.tsx` (reusa `OfertaAsesorias` en modo consulta)
**Ruta:** `/sae/asesorias/oferta`.
**Flujo:** `useOferta()` (filtro carrera + búsqueda materia, idéntico al alumno) → seleccionar materia → `/sae/asesorias/oferta/:materiaId`.
**Detalle materia — `AdminOfertaMateria.tsx`:** `useAsesoresDeMateria` → seleccionar asesor → `useDisponibilidadDeAsesor` → días (`agruparPorDia`) → bloques, **todo read-only**; sin selector de carrera, sin `Dialogo` de confirmación, sin `useAgendarAsesoria`. Termina en visualización.

### 3. Directorio de asesores — `AdminAsesores.tsx`
**Ruta:** `/sae/asesores`.
**Cuerpo:** `useAdminAsesores()` → lista con nombre, área, `activo`, nº de materias del semestre vigente; buscador por nombre (cliente). Seleccionar → `/sae/asesores/:asesorId`.

### 4. Detalle de asesor — `AdminAsesorDetalle.tsx`
**Ruta:** `/sae/asesores/:asesorId`.
**Cuerpo:** `useAdminAsesor(asesorId, semestre)` → reutiliza `MisMaterias` y `MiHorario` con `soloLectura` y datos del asesor seleccionado. Sin diálogos de agregar/quitar/editar; chips de horario no interactivos; selector de semestre para navegar registros pasados. `InsigniaEstado` para `activo`.

---

## API frontend (nuevos hooks en `features/asesorias/api.ts`)

Mismo patrón `apiGet` + query keys planas:
- `useAdminAsesorias(filtros)` → `['admin', 'asesorias', filtros]` → `GET /admin/asesorias/`.
- `useAdminSemestres()` → `['admin', 'semestres']` → `GET /admin/semestres/`.
- `useAdminAsesores()` → `['admin', 'asesores']` → `GET /admin/asesores/`.
- `useAdminAsesor(perfilId, semestre)` → `['admin', 'asesor', perfilId, semestre]` → `GET /admin/asesores/{perfilId}/?semestre=`.
- `useBuscarAlumnos(buscar)` → `['admin', 'alumnos', buscar]` → `GET /admin/alumnos/?buscar=` (habilitado con `enabled: buscar.length >= 2`).
- Reuso sin cambios: `useOferta`, `useAsesoresDeMateria`, `useDisponibilidadDeAsesor` (endpoints ya ampliados a `EsAlumnoOMiembroSAE`).

Tipos nuevos en `src/api/types.ts`: `AsesoriaAdmin` (con `alumno_nombre`+`asesor_nombre`+`notas`), `AsesorDirectorio`, `AsesorDetalle`, `AlumnoBusqueda`.

---

## Componentes y reuso

**Reusar (no reimplementar):** `Tabs`, `InsigniaEstado`, `Skeleton`, `Boton`, `useMapaMaterias`/`useMapaCarreras`, helpers de `logica.ts`, tokens/`.foco-visible`, y — en su modo consulta/lectura — `OfertaAsesorias`, `useAsesoresDeMateria`, `useDisponibilidadDeAsesor`, `agruparPorDia`.

**Modificar:**
- `TarjetaAsesoria.tsx` — modo admin: ambos nombres + `notas`, no interactiva.
- `MisMaterias.tsx` / `MiHorario.tsx` — prop `soloLectura` + fuente de datos parametrizable.
- `OfertaAsesorias.tsx` — modo consulta (destino de navegación configurable, sin agendar) o wrapper `AdminOferta` que lo reusa.
- `auth/rol.ts` (`useEsMiembroSAE`), `auth/RutaProtegida.tsx` (`RutaDeSAE`), `api/types.ts` (`'sae'` en `RolUsuario`), `App.tsx` (rutas `/sae/*`), `screens/Home.tsx` (tarjeta de servicio SAE).

**Crear:** `AdminAsesorias.tsx`, `AdminOfertaMateria.tsx`, `AdminAsesores.tsx`, `AdminAsesorDetalle.tsx` (+ `AdminOferta.tsx` si se prefiere wrapper), hooks admin nuevos.

**Convenciones:** convención de diálogos ([ADR 0020](../../decisions/0020-sistema-componentes-shadcn.md)) — aquí casi no aplica por ser lectura; truncamiento de materias; toque mínimo 44×44; íconos de formato de `ServiceIcons.tsx`; motion CSS con `prefers-reduced-motion`.

---

## Testing

Vitest + Testing Library, tests colocados, hooks mockeados con `vi.spyOn`, factories de `src/test/factories.ts` (añadir `usuarioSAE`):
- **Guarda:** con rol `sae` entra a `/sae/*`; sin él → `/home`; no autenticado → `/login`.
- **Agendadas/histórico:** tabs Próximas/Historial; subtabs por semestre; filtro por asesor (select) y por alumno (búsqueda) disparan la query con `?asesor=`/`?alumno=`.
- **Tarjeta admin:** muestra ambos nombres y `notas`; no navega a detalle (no interactiva).
- **Consulta de oferta:** filtra por carrera y por búsqueda; el detalle de materia muestra asesores y disponibilidad **sin** botón de agendar ni selector de carrera.
- **Directorio + detalle:** lista asesores; detalle reusa materias/horario en `soloLectura` (sin diálogos, chips no interactivos); cambio de semestre recarga el detalle.
- **Home:** la tarjeta de servicio SAE aparece sólo con rol `sae`.

---

## Out of scope

- Acciones de escritura del SAE (cancelar, reasignar, editar) — fase posterior.
- Vista de detalle de sesión admin (`/sae/asesorias/:id`) — en esta fase la tarjeta no navega.
- Paginación de listados → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).
- Alta de `PerfilSAE` desde la app → [deuda 0014](../../technical-debt/0014-alta-perfil-sae-solo-admin.md).

---

## Self-review

- Sin placeholders/TBD: cada pantalla tiene ruta, flujo, hooks y casos de prueba; los contratos que consume están en la spec de API gemela.
- Alcance cohesivo: área SAE de solo lectura; reusa las pantallas del asesor sin rediseñarlas y no toca los flujos de alumno/asesor salvo extender `TarjetaAsesoria`.
- Consistente con patrones: guardas espejo de `RutaProtegida`, hooks de rol sobre `useAuth().roles`, TanStack Query con query keys planas, reuso de `ui/` y `logica.ts`.
- Deuda referenciada, no duplicada: alta manual → 0014; paginación → 0006.
