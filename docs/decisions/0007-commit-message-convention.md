# 0007 — Convención de mensajes de commit

**Status:** Accepted
**Date:** 2026-07-27

## Context

El proyecto necesita un historial de commits legible y consistente a medida que varios servicios de la SAE se integran de forma incremental (ver [architecture-overview.md](../architecture-overview.md)), con contribuciones tanto en `/backend` como en `/frontend`.

## Decision

Adoptar el formato `[type][scope] resumen` con lista de cambios y `Signed-off-by`, basado en los tipos de [Conventional Commits](https://www.conventionalcommits.org/) (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`) pero usando corchetes en vez de dos puntos, y agregando un `scope` opcional para ubicar el cambio dentro del monorepo (ver [0001](0001-monorepo-structure.md)).

Los commits deben ser lo más atómicos posible: un commit, un tipo de cambio.

Detalle completo del formato, tabla de tipos y ejemplos en [`docs/development/commit-conventions.md`](../development/commit-conventions.md).

## Consequences

- Historial de commits filtrable/legible por tipo y por área del monorepo.
- `Signed-off-by` (vía `git commit -s`) queda como requisito de facto para certificar autoría de cada cambio.
- Commits atómicos facilitan revertir o hacer bisect de cambios problemáticos sin arrastrar cambios no relacionados.

## Alternatives considered

- **Conventional Commits estándar (`feat: resumen`, sin corchetes):** es el formato más extendido en el ecosistema (compatible con herramientas como `commitlint`/`semantic-release`), pero se descartó a favor del formato con corchetes explícitamente solicitado.
