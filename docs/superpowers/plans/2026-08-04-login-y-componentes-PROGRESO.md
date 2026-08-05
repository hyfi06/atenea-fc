# Progreso — Rediseño documentado de login y sistema de componentes

Ledger vivo para retomar este trabajo en cualquier sesión. Fuente de verdad del avance — si una sesión se corta, leer este archivo primero antes de releer código.

Plan completo (fuera del repo, en el harness): `~/.claude/plans/parece-que-hubo-un-groovy-unicorn.md` — si no está disponible, este ledger junto con las specs/planes ya escritos en `docs/superpowers/` basta para reconstruir el contexto.

Contexto en una línea: el login (frontend+backend, dev/prod) ya funciona y está documentado (ADR 0003/0018); lo que se construyó sin visualización/aprobación previa fue el flujo de asesorías. Este trabajo es solo documentación/specs/planes — cero código de aplicación.

Nota de rama: este archivo vive en `dev-frontend` (pasos 1-2, 5-9) y en paralelo en `dev-ux-ui` (paso 3) y `dev-backend` (paso 4) — cada rama actualiza su copia al cerrar el paso que le toca; no se reconcilian entre sí salvo que un paso lo requiera explícitamente (como hizo el paso 4).

## Estado por paso

| # | Paso | Rama | Estado | Artefacto(s) |
|---|------|------|--------|--------------|
| 1 | Mapa de conocimiento (/graphify) | dev-frontend | Completo | `graphify-out/` (local, gitignored) — 923 nodos, 1866 aristas, 101 comunidades |
| 2 | Spec de login frontend+backend | dev-frontend | Completo | `docs/superpowers/specs/2026-08-04-login-oauth-design.md`, [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md), changelog en ADR 0018 |
| 3 | Revisión retroactiva de vistas de asesorías | dev-ux-ui | Completo | `docs/superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md` |
| 4 | Cherry-pick docs + plan de login backend (Opus) | dev-backend | Completo | `docs/superpowers/plans/2026-08-04-login-oauth-backend.md` (plan escrito, ejecución diferida) |
| 5 | Decisión de reset de dev-frontend | dev-frontend | Completo | Sin reset — ver hallazgos abajo |
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
- Corrección post-cierre: al leer el plan completo (`~/.claude/plans/parece-que-hubo-un-groovy-unicorn.md`) antes de empezar el paso 3, se detectó que la primera versión del spec no cubría dos requisitos explícitos del paso 2 (fix del placeholder de `Landing.tsx`, decisión razonada sí/no sobre CSRF/deuda 0009). Se corrigió el spec antes de avanzar.

## Hallazgos del Paso 3 (revisión retroactiva de vistas de asesorías, en dev-ux-ui)

- Método: app real corriendo (`dev-ux-ui`, backend+frontend locales contra Postgres/Redis ya activos) + datos de demo sembrados (asesor con sesiones en los 3 estados) + Playwright para capturas reales — no mockups aislados. Datos y servidores locales, nada de esto se comitea.
- Primera pasada (solo lectura, sin cambios de diseño): 5 hallazgos reales — impacto visible de la deuda técnica 0010 (`Alumno #N` en vez de nombre), un bug de React confirmado (`key` prop faltante en `GrillaDisponibilidad.tsx`, fragmento sin key en `HORAS.map()`), y el hallazgo más importante: la grilla semanal de `DisponibilidadAsesor` (7×28 celdas, 640px de ancho) solo mostraba ~3 de 7 columnas en un viewport de 390px sin ninguna pista visual de scroll horizontal.
- Segunda pasada (rediseño, con `superpowers:brainstorming` + `ui-ux-pro-max`): la grilla se reemplaza por dos pantallas nuevas — "Mis materias" y "Mi horario" (tabs por día) — en vez de un ajuste puntual a la grilla original. Se estableció una convención de botones para diálogos (2 acciones = fila horizontal; 3+ acciones = columna con orden fijo: reversible arriba, destructivo en outline al medio, salir al final como texto plano) que corrige una inconsistencia real encontrada entre diálogos existentes y nuevos, más un bug de overflow (`flex:1` sin `min-width:0`).
- Ícono nuevo (`IconAsesoriasAcademicas`) diseñado para Home, mismo lenguaje visual del set existente.
- Home gana su primera tarjeta condicional a rol (asesor o alumno) — esto disparó una decisión explícita sobre deuda técnica 0010: **se decide resolverla en el paso 4** (exponer perfil/rol en una sola llamada) en vez de agregar un segundo sondeo "parche gemelo" a `useEsAsesor()`.
- Nueva superficie de backend identificada, pendiente para el paso 4 (ninguna existe hoy): confirmar sesiones futuras antes de desactivar un horario, quitar una materia del registro del asesor, y filtrar el historial de asesorías por semestre (este último conecta con la deuda técnica 0006, sin paginación — la cubre parcialmente, no la reemplaza).
- Artefacto: `docs/superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md` — autocontenido (no depende de los artefactos HTML de la sesión de diseño para ser implementable en otra sesión).

## Hallazgos del Paso 4 (`dev-backend`, resumen — detalle completo en la copia del ledger de esa rama)

- Cherry-pick limpio de 8 commits de documentación (2 fixes backend-only + 6 docs) desde `dev-frontend`/`dev-ux-ui`; único conflicto fue `.gitignore` (dos líneas nuevas en paralelo), resuelto conservando ambas.
- Plan de backend generado por agente `model: opus` (`superpowers:writing-plans`): `docs/superpowers/plans/2026-08-04-login-oauth-backend.md` — 10 tasks TDD cubriendo transporte `id_token` (ADR 0019), deuda técnica 0010 completa, y los 4 endpoints nuevos de asesorías del paso 3.
- Checkpoint cerrado por el usuario con el plan escrito pero **sin ejecutar** — la ejecución queda pendiente para una sesión futura, sin fecha fijada.

## Hallazgos del Paso 5 (decisión de reset de `dev-frontend`)

- Se releyó la tabla de veredictos del paso 3 (`docs/superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md`, sección "Decisión por pantalla") como criterio de compuerta explícito del plan: **0 pantallas quedaron en "Rehacer"**. Todas son "Aprobada" o "Aprobada con ajustes" — incluido el caso más profundo (Disponibilidad del asesor, que cambia de grilla única a dos pantallas con tabs), que sigue siendo rediseño de lo existente, no descarte.
- Decisión confirmada por el usuario: **no se resetea `dev-frontend`**. No se crea `legacy-frontend-202608`. Las correcciones documentadas como "ajustes" en el paso 3 quedan como input para los planes de implementación de los pasos 8 (componentes) y 9 (login frontend), no vía reset de rama.
- Como no hubo reset, no aplica el paso de sincronizar `/frontend` en `dev-backend` (esa acción solo estaba condicionada a que hubiera reset).
- Este es el checkpoint marcado en el plan original como "la acción más difícil de revertir de todo el trabajo" — se cierra sin acción de rama, decisión y razón quedan documentadas aquí para no reabrirse sin nueva evidencia.

## Próximo paso

Paso 6 (`dev-frontend`): spec de componentes reutilizables (`docs/superpowers/specs/2026-08-04-sistema-componentes-design.md`). Reabre la decisión de facto de no usar librería de componentes (Radix headless + Tailwind a mano vs shadcn/ui vs librería completa) — trabajo de arquitectura, no mecánico: usar `superpowers:brainstorming` antes de escribir, apoyado en `ui-ux-pro-max` para evaluar las opciones contra las necesidades reales de UI del proyecto. Deja la decisión abierta con recomendación motivada si no se cierra en el checkpoint, tal como pide el plan. Checkpoint pendiente de confirmación del usuario antes de empezar.
