# Progreso — Rediseño documentado de login y sistema de componentes

Ledger vivo para retomar este trabajo en cualquier sesión. Fuente de verdad del avance — si una sesión se corta, leer este archivo primero antes de releer código.

Plan completo (fuera del repo, en el harness): `~/.claude/plans/parece-que-hubo-un-groovy-unicorn.md` — si no está disponible, este ledger junto con las specs/planes ya escritos en `docs/superpowers/` basta para reconstruir el contexto.

Contexto en una línea: el login (frontend+backend, dev/prod) ya funciona y está documentado (ADR 0003/0018); lo que se construyó sin visualización/aprobación previa fue el flujo de asesorías. Este trabajo es solo documentación/specs/planes — cero código de aplicación.

## Estado por paso

| # | Paso | Rama | Estado | Artefacto(s) |
|---|------|------|--------|--------------|
| 1 | Mapa de conocimiento (/graphify) | dev-frontend | Completo | `graphify-out/` (local, gitignored) — 923 nodos, 1866 aristas, 101 comunidades |
| 2 | Spec de login frontend+backend | dev-frontend | Completo | `docs/superpowers/specs/2026-08-04-login-oauth-design.md`, [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md), changelog en ADR 0018 |
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

## Hallazgos del Paso 1 (graphify)

- Grafo local en `graphify-out/` (no versionado, ver `.gitignore`) — reconsultar con `graphify query "<pregunta>"` en vez de releer archivos en los pasos 2-9.
- God nodes: `User`, `Asesoria`, `Disponibilidad`, `PerfilAcademico`, `RegistroAsesor` — confirman que el dominio de negocio (asesorías + identidad) concentra la complejidad real, no el login.
- Comunidad "ADR 0018: contrato de auth prod (cookies JWT)" y "ADR 0003/0010/0013: OAuth, User, auto-registro" quedaron claramente delimitadas y cohesivas — confirma que el contrato de login está bien encapsulado y documentado, consistente con el hallazgo de la Fase 1 (login sí funciona).
- Conexión sorprendente relevante al Paso 2: deuda técnica 0010 (API no expone perfil/rol) conecta directamente el auth wiring del frontend con el modelo de Asesorías — es la pieza que más comunidades cruza, refuerza que decidir sobre 0010 en el spec de login (paso 2) no es opcional, condiciona a asesorías también.
- Aviso de salud del grafo: 234 edges con endpoint colgante (referencias semánticas a nodos fuera de su chunk) — no bloqueante, esperado en una primera pasada sin `--mode deep`; no se corrigió en este paso.

## Hallazgos del Paso 2 (spec de login)

- Se reabrió la decisión 1 de ADR 0018 (transporte de Google OAuth) por pedido explícito del usuario: alinear con el estándar actual y priorizar seguridad, no por un incidente puntual.
- El brainstorming encontró una **tercera opción no contemplada en el ledger original**: Sign In With Google / ID token (OIDC), distinta tanto del statu quo (GIS Token Client / access_token) como de "Authorization Code + redirect" que el ledger nombraba. Se eligió esta tercera opción.
- Razón técnica concreta (no solo "mejor práctica" genérica): el flujo actual de `access_token` no verifica `audience` al validar identidad (`GoogleOAuth2Adapter._fetch_user_info` vía userinfo, sin chequeo de para qué client_id se emitió el token) — clase de vulnerabilidad "OAuth token confusion". El flujo de `id_token` sí verifica `audience=app.client_id`, ya soportado sin cambios por `django-allauth` instalado.
- Cero variables de entorno nuevas en cualquiera de las tres opciones evaluadas — se confirmó en código (`backend/.env.example`, `frontend/.env.example`, `config/settings/{base,prod}.py`).
- Deuda técnica 0010 (perfil/rol no expuesto en `/api/auth/user/`) se dejó **explícitamente fuera de esta spec** — decisión de scope, no omisión silenciosa; registrada como pendiente a resolver antes del paso 9 (plan de implementación de login frontend).
- Artefactos: spec (`docs/superpowers/specs/2026-08-04-login-oauth-design.md`), ADR nueva (`docs/decisions/0019-transporte-login-google-id-token.md`), changelog agregado a ADR 0018 (decisión 1 marcada como superada, decisiones 2 y 3 confirmadas sin cambios).
- Se usó `/graphify query` para confirmar el número de ADR más alto y las conexiones auth↔asesorías antes de escribir, en vez de releer archivos — consistente con la práctica establecida en el paso 1.

## Próximo paso

Paso 3: revisión retroactiva de vistas de asesorías, en la rama `dev-ux-ui` (`docs/superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md`). Checkpoint pendiente de confirmación del usuario antes de cambiar de rama y empezar.
