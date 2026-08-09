# 0022 — Asesorías: vista unificada de frontend (alumno + asesor + admin futuro)

**Status:** Accepted
**Date:** 2026-08-08

## Context

El frontend de asesorías cubría sólo el lado asesor ([spec de asesor](../superpowers/specs/2026-08-01-asesorias-frontend-asesor-design.md)), con el lado alumno diferido a Fase 2. Al diseñar esa fase, el usuario decidió **unificar** la pantalla en vez de crear una vista de alumno separada: la lista de sesiones (`useMisAsesorias()` → `GET /api/asesorias/asesorias/`) ya está unida por rol en el backend ([ADR 0017](0017-asesorias-academicas-api.md), deuda 0011 cerrada), así que una sola vista puede servir a alumno, asesor y (futuro) admin, diferenciando acciones y contenido de tarjeta por rol. Diseño completo en [`docs/superpowers/specs/2026-08-08-asesorias-alumno-frontend-design.md`](../superpowers/specs/2026-08-08-asesorias-alumno-frontend-design.md). La API que consume está en [ADR 0021](0021-asesorias-alumno-api.md).

## Decision

- **Una pantalla unificada en `/asesorias`** (`Asesorias.tsx`, renombra `SesionesAsesor.tsx`) que ramifica por rol: tabs Próximas/Historial para ambos; encabezado con *Mis materias*/*Mi horario* para el asesor y *Nueva asesoría* para el alumno (`useEsAsesor()`/`useEsAlumno()` de `auth/rol.ts`).
- **Guard `RutaDeAsesorias`**: autenticado y (alumno **o** asesor); externo → `/home`. `RutaDeAsesor` se conserva sólo para las subrutas exclusivas de asesor (`/asesorias/materias`, `/asesorias/horario`).
- **`TarjetaAsesoria` muestra el contraparte** según rol (alumno ve `asesor_nombre`, asesor ve `alumno_nombre`), reemplazando el hardcode `Alumno #{id}`; diseñada para que admin muestre ambos. Nunca renderiza `notas` al alumno.
- **Flujo de agendado como stepper de una sola ruta** (`/asesorias/nueva` → oferta; `/asesorias/nueva/:materiaId` → wizard asesor → día → bloque → carrera), con estado de paso interno y navegación Atrás/Siguiente, no una ruta por paso.
- **Selector de carrera autoseleccionado** con la única carrera del alumno de hoy, listo para múltiples carreras ([deuda 0008](../technical-debt/0008-perfil-alumno-una-sola-carrera.md)).
- **Sin dependencias nuevas**: TanStack Query, CSS puro, `Dialogo`/`Tabs`/`Boton` del sistema de componentes ([ADR 0020](0020-sistema-componentes-shadcn.md)), tokens MD3 ([ADR 0014](0014-tokens-logo-iconos-frontend.md)).

## Consequences

- La lista, los tabs y la tarjeta dejan de estar acoplados a un rol; agregar la vista de admin más adelante es sobre todo ruteo y una condición de tarjeta, no una pantalla nueva.
- `RutaDeAsesor` deja de proteger `/asesorias`; hay que verificar que las subrutas de asesor sigan bajo el guard estricto para no exponerlas al alumno.
- Eliminar el hardcode `Alumno #{id}` depende de `alumno_nombre`/`asesor_nombre` (ya expuestos por ADR 0017) y del ocultamiento de `notas` (ADR 0021) — este plan asume ambos contratos.
- El wizard de una sola ruta no permite deep-link por paso; es un trade-off aceptado por la simplicidad de un flujo lineal corto.
- El selector de carrera introduce un paso que hoy tiene una sola opción; se preselecciona para no estorbar, y queda listo cuando exista `HistoriaAcademica`.

## Alternatives considered

- **Pantalla de alumno separada** (`/asesorias-alumno`): más aislada, pero duplicaría tabs/lista/tarjeta que el backend ya sirve unificados por rol, y no prepara la vista de admin. Descartada por decisión explícita del usuario.
- **Guard de alumno paralelo** manteniendo `RutaDeAsesor` en `/asesorias`: dos guards para una vista compartida; se prefiere un único `RutaDeAsesorias`.
- **Wizard con ruta por paso**: habilita deep-link y back del navegador por paso, a costa de más ruteo y estado en URL; innecesario para un flujo lineal corto.
- **Ocultar `notas` sólo en el frontend**: dejaría el dato viajando al cliente; se prefiere defensa en profundidad (backend omite + frontend no referencia), alineado con ADR 0021.

## Changelog

- (sin enmiendas)
