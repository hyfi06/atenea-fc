# 0024 — Asesorías Académicas: vista de administración SAE (frontend)

**Status:** Accepted
**Date:** 2026-08-09

## Context

El frontend de asesorías sirve a alumno y asesor bajo `/asesorias*` ([ADR 0022](0022-asesorias-vista-unificada-frontend.md)), con guardas `RutaDeAsesorias` y `RutaDeAsesor`. No existe ningún área de administración para la SAE. La API que la habilita se define en [ADR 0023](0023-asesorias-sae-admin-api.md) (rol `'sae'`, endpoints `/admin/*`, oferta/búsqueda ampliadas a `EsAlumnoOMiembroSAE`). Diseño completo en [`docs/superpowers/specs/2026-08-09-asesorias-sae-admin-frontend-design.md`](../superpowers/specs/2026-08-09-asesorias-sae-admin-frontend-design.md).

El área SAE es de **solo lectura**: supervisar asesorías agendadas e históricas, consultar la oferta materias → asesores → disponibilidad sin agendar, y navegar un directorio de asesores con el detalle de sus materias y horarios.

## Decision

- **Rol y guarda**: `useEsMiembroSAE()` (`roles.includes('sae')`) en `auth/rol.ts` y `RutaDeSAE` en `RutaProtegida.tsx` (espejo de `RutaDeAsesor`; externo → `/home`). Se añade `'sae'` al tipo `RolUsuario`.
- **Área propia bajo `/sae/*`**: `/sae/asesorias` (agendadas + histórico + consulta de oferta) y `/sae/asesores` (directorio + detalle), no subrutas de `/asesorias`. Tarjeta de servicio condicional en `screens/Home.tsx`.
- **Pantalla `AdminAsesorias`** (`/sae/asesorias`): `Tabs` Próximas/Historial con pills por semestre (`useAdminAsesorias`, `useAdminSemestres`), filtros por asesor (select, `useAdminAsesores`) y alumno (búsqueda, `useBuscarAlumnos`). `TarjetaAsesoria` en modo admin: ambos nombres + `notas`, no interactiva.
- **Consulta de oferta** (`/sae/asesorias/oferta` → `.../:materiaId`): reusa `OfertaAsesorias` en modo consulta y `useOferta`/`useAsesoresDeMateria`/`useDisponibilidadDeAsesor`/`agruparPorDia`, terminando en visualización read-only — sin selector de carrera, sin `Dialogo` de confirmación, sin `useAgendarAsesoria`.
- **Directorio + detalle de asesor** (`/sae/asesores` → `.../:asesorId`): `AdminAsesores` lista desde `/admin/asesores/`; el detalle reutiliza `MisMaterias`/`MiHorario` con prop `soloLectura` y datos de `/admin/asesores/{id}/`, con selector de semestre.
- **Sin dependencias nuevas**: TanStack Query con query keys planas, CSS puro, componentes `ui/` existentes, tokens MD3 ([ADR 0014](0014-tokens-logo-iconos-frontend.md)), sistema de componentes ([ADR 0020](0020-sistema-componentes-shadcn.md)).
- **Proceso**: las pantallas/componentes nuevos se validan con **artefactos (mockups)** antes de implementar; el plan lo hace explícito por pantalla.

## Consequences

- La SAE gana una tercera área con su propia guarda, sin tocar los flujos de alumno/asesor salvo extender `TarjetaAsesoria` (modo admin) y parametrizar `MisMaterias`/`MiHorario` con `soloLectura`.
- Reutilizar las pantallas del asesor en modo lectura da paridad visual sin duplicar layout, a costa de introducir un flag de modo en dos pantallas hoy puramente interactivas — hay que cuidar que ese flag no filtre acciones de escritura.
- Separar el árbol `/sae/*` evita ramas de rol adicionales en pantallas ya densas; el precio es algo de duplicación de andamiaje (tabs, listado) que se mitiga reusando `ui/` y `logica.ts`.
- La fuente de datos admin-wide (`/admin/asesorias/`) es distinta de `useMisAsesorias`; una pantalla dedicada (`AdminAsesorias`) mantiene ambas limpias.
- Deuda referenciada, no duplicada: paginación → [0006](../technical-debt/0006-sin-paginacion-listados.md); alta de `PerfilSAE` → [0014](../technical-debt/0014-alta-perfil-sae-solo-admin.md).

## Alternatives considered

- **Reusar `Asesorias.tsx`** (la vista unificada alumno/asesor) añadiendo una rama de rol SAE: la fuente de datos es admin-wide, no `useMisAsesorias`; sumar un tercer rol densificaría una pantalla ya ramificada. Descartada.
- **Subrutas bajo `/asesorias`** en vez de `/sae/*`: mezclaría la navegación de tres personas en un árbol; se prefiere un área propia. Descartada por decisión explícita del usuario.
- **Componentes read-only nuevos** para el detalle del asesor: mantiene las pantallas del asesor sin flags, a costa de duplicar el layout de materias/horario. Descartada por decisión explícita del usuario a favor de reusar en modo lectura.
- **Tarjeta admin separada**: `TarjetaAsesoria` ya ramifica por rol; se extiende para el caso SAE en vez de duplicar.

## Changelog

- (sin enmiendas)
