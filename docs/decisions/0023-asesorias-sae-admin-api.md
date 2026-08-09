# 0023 — Asesorías Académicas: identidad SAE y API de administración

**Status:** Accepted
**Date:** 2026-08-09

## Context

La capa DRF de Asesorías ([ADR 0017](0017-asesorias-academicas-api.md), [ADR 0021](0021-asesorias-alumno-api.md)) sirve a dos personas — alumno y asesor — y **acota todo queryset de `Asesoria` al usuario autenticado**: `AsesoriaViewSet.get_queryset` (`asesorias/views.py`) une por rol las sesiones donde el usuario es alumno o asesor, y los endpoints de oferta/búsqueda son `EsAlumno`. No existe rol ni endpoint para un **miembro de la SAE** que supervise el servicio de forma transversal; `is_staff`/`is_superuser` sólo alimentan el Django admin. Los roles se derivan por existencia de perfil (`hasattr`, patrón `PerfilX` de [ADR 0012](0012-perfiles-identidad-roles.md)) y se exponen en el array `roles` de `UserDetailsSerializer`. Diseño completo en [`docs/superpowers/specs/2026-08-09-asesorias-sae-admin-api-design.md`](../superpowers/specs/2026-08-09-asesorias-sae-admin-api-design.md).

El miembro SAE funge casi como administrador de este servicio: consulta datos de asesor y alumno (incluidas las `notas`), pero no agenda, edita ni cancela.

## Decision

- **Identidad `PerfilSAE`**: nuevo perfil OneToOne a `User` (patrón `PerfilX`, [ADR 0012](0012-perfiles-identidad-roles.md)) en la app `accounts` (no es específico de asesorías; otros servicios SAE lo reutilizarán). Campos mínimos `user` + `activo`, registrado en Django admin. Alta sólo por admin → [deuda 0014](../technical-debt/0014-alta-perfil-sae-solo-admin.md) (hermana de [0002](../technical-debt/0002-alta-perfil-asesor-solo-admin.md)).
- **Rol `'sae'`**: `UserDetailsSerializer.get_roles` lo añade cuando `hasattr(user, "perfil_sae")`. Permiso `EsMiembroSAE` (`hasattr(request.user, "perfil_sae")`) y `EsAlumnoOMiembroSAE` en `asesorias/permissions.py`.
- **Reuso de endpoints de consulta**: `OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` amplían su permiso de `EsAlumno` a `EsAlumnoOMiembroSAE`. El SAE consulta el mismo flujo materias → asesores → disponibilidad que el alumno, sin poder `POST /asesorias/` (agendar sigue `EsAlumno`). Cero duplicación.
- **Superficie admin de solo lectura** bajo `/api/asesorias/admin/`, con permiso `EsMiembroSAE`, en views dedicadas (sin tocar el `AsesoriaViewSet` acotado al usuario): `GET /admin/asesorias/?asesor=&alumno=&semestre=&estado=` (ambos nombres; sin `?semestre` → próximas agendadas), `GET /admin/semestres/` (todos los del sistema), `GET /admin/asesores/` (directorio), `GET /admin/asesores/{perfil_id}/?semestre=` (materias + disponibilidad), `GET /admin/alumnos/?buscar=` (autocompletar por nombre/`numero_cuenta`).
- **`notas` visibles al SAE**: el gate de `to_representation` que oculta `notas` a quien no es el asesor dueño se amplía para mostrarlas también al miembro SAE. El alumno sigue sin verlas (no se reabre ADR 0021).
- **Sin escritura ni paginación** en esta fase: todos los endpoints admin son `GET`; sin paginación, coherente con [deuda 0006](../technical-debt/0006-sin-paginacion-listados.md).
- **Filtro por asesor = `PerfilAsesorAcademico.id`** (`disponibilidad__registro__asesor_id`), validado lenient como los filtros de `BuscarDisponibilidadView`.

## Consequences

- Aparece una tercera persona (SAE) con su propio rol y permiso, consistente con el patrón `PerfilX`/`hasattr`; el resto del sistema no cambia de mecanismo de rol.
- La supervisión transversal vive en views admin separadas, dejando intacto el `AsesoriaViewSet` acotado al usuario; el riesgo de exponer datos de más queda contenido en una superficie con permiso `EsMiembroSAE`.
- Ampliar tres endpoints a `EsAlumnoOMiembroSAE` evita duplicar el flujo de oferta; el precio es que esos endpoints ahora sirven a dos roles y sus tests deben cubrir ambos.
- La visibilidad de `notas` para el SAE es una decisión de producto (rol casi-administrador), no un leak: el gate se amplía explícitamente y el alumno sigue excluido.
- `PerfilSAE` introduce una migración; el alta manual queda como [deuda 0014](../technical-debt/0014-alta-perfil-sae-solo-admin.md). Paginación → [0006](../technical-debt/0006-sin-paginacion-listados.md); scope de semestre en oferta → [0012](../technical-debt/0012-oferta-asesorias-sin-scope-de-semestre.md); disponibilidad histórica → [0005](../technical-debt/0005-editar-disponibilidad-no-propaga.md).

## Alternatives considered

- **Reusar `is_staff`** como marca de miembro SAE: menos código, pero mezcla el acceso al Django admin con el acceso a la app SAE y rompe el patrón `roles`-array/`hasattr` del resto del sistema. Descartada.
- **Grupo de Django `SAE`**: flexible para permisos granulares, pero introduce un mecanismo de rol distinto al patrón `PerfilX` ya establecido. Descartada por consistencia.
- **Extender el `AsesoriaViewSet` con una rama de rol admin** en `get_queryset`: acoplaría la lógica acotada-al-usuario con la transversal en una sola clase; se prefieren views admin dedicadas.
- **Serializer de admin totalmente separado**: se prefiere ampliar el gate de `notas` en el serializer compartido (o una subclase mínima) para no duplicar el shape del recurso.

## Changelog

- (sin enmiendas)
