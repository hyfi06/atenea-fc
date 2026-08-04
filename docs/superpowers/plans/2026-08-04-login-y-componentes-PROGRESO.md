# Progreso — Rediseño documentado de login y sistema de componentes

Ledger vivo para retomar este trabajo en cualquier sesión. Fuente de verdad del avance — si una sesión se corta, leer este archivo primero antes de releer código.

Plan completo (fuera del repo, en el harness): `~/.claude/plans/parece-que-hubo-un-groovy-unicorn.md` — si no está disponible, este ledger junto con las specs/planes ya escritos en `docs/superpowers/` basta para reconstruir el contexto.

Contexto en una línea: el login (frontend+backend, dev/prod) ya funciona y está documentado (ADR 0003/0018); lo que se construyó sin visualización/aprobación previa fue el flujo de asesorías. Este trabajo es solo documentación/specs/planes — cero código de aplicación.

## Estado por paso

| # | Paso | Rama | Estado | Artefacto(s) |
|---|------|------|--------|--------------|
| 1 | Mapa de conocimiento (/graphify) | dev-frontend | En progreso | — |
| 2 | Spec de login frontend+backend | dev-frontend | Pendiente | `docs/superpowers/specs/2026-08-04-login-oauth-design.md` |
| 3 | Revisión retroactiva de vistas de asesorías | dev-ux-ui | Pendiente | `docs/superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md` |
| 4 | Cherry-pick docs + plan de login backend (Opus) | dev-backend | Pendiente | `docs/superpowers/plans/2026-08-04-login-oauth-backend.md` |
| 5 | Decisión de reset de dev-frontend | dev-frontend | Pendiente | rama `legacy-frontend-202608` (si aplica) |
| 6 | Spec de componentes reutilizables | dev-frontend | Pendiente | `docs/superpowers/specs/2026-08-04-sistema-componentes-design.md` |
| 7 | Marco de trabajo para nuevos componentes | dev-frontend | Pendiente | `docs/development/contribuir-componentes.md` |
| 8 | Plan de implementación de componentes (Opus) | dev-frontend | Pendiente | `docs/superpowers/plans/2026-08-04-sistema-componentes.md` |
| 9 | Plan de implementación de login frontend (Opus) | dev-frontend | Pendiente | `docs/superpowers/plans/2026-08-04-login-oauth-frontend.md` |

## Decisiones tomadas hasta ahora

- El "código descartable" es el del flujo de asesorías (implementado sin visualización/aprobación previa), **no** el de login.
- El spec de login (paso 2) debe reabrir la alternativa "Authorization Code + redirect" que ADR 0018 ya evaluó y descartó.
- Cadencia de ejecución: checkpoint explícito por cada paso numerado, sin avanzar sin confirmación del usuario.

## Próximo paso

Paso 1: ejecutar `/graphify` sobre el repo y resumir hallazgos relevantes para los pasos 2-3.
