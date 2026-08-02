# API del backend — guía para el equipo de frontend

Referencia de integración: qué expone el backend hoy (rutas, contratos de request/response, permisos, reglas de negocio que se traducen en errores HTTP) y qué debe saber el SPA para consumirlo. Verificado contra el código (`backend/`) el 2026-08-01, no contra los ADRs por sí solos — donde el código y un ADR no coinciden se marca explícitamente.

No existe schema OpenAPI/Swagger (no hay `drf-spectacular`/`drf-yasg` en el proyecto): este documento es la fuente más cercana a un contrato formal.

## Convenciones generales

- **Base URL:** `VITE_API_BASE_URL` (`http://localhost:8000` en dev). Todas las rutas de abajo son relativas a esa base.
- **Formato:** JSON en request y response, `Content-Type: application/json`.
- **Autenticación:** todo endpoint requiere `IsAuthenticated` por default (`Authorization: Bearer <access>` en dev — ver [Autenticación](#autenticación)) salvo que se indique `AllowAny` explícitamente.
- **Paginación:** no existe en ningún endpoint. Todo `list` devuelve un array JSON plano, no `{results, count, next, previous}`. Ver [deuda técnica 0006](../technical-debt/0006-sin-paginacion-listados.md).
- **Forma de los errores — no es uniforme:**
  - Endpoints de `dj-rest-auth` (login, password reset, etc.) y validación de campo de DRF: `{"field": ["mensaje"]}` o `{"detail": "mensaje"}`.
  - Endpoints de `asesorias` cuando la regla de negocio vive en el modelo (`.clean()`): siempre `{"detail": ["mensaje"]}` — **una lista**, incluso con un solo mensaje.
- **CORS:** solo se permite el origen exacto en `FRONTEND_URL` (`http://localhost:5173` en dev). No hay wildcard.

## Autenticación

Contrato completo y su razonamiento en [ADR 0003](../decisions/0003-google-oauth-allauth-jwt.md) y [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md). Resumen operativo para implementar `api/client.ts`:

### Login con Google (único flujo social soportado)

1. El SPA usa Google Identity Services (`google.accounts.oauth2.initTokenClient`) para abrir un popup y obtener un `access_token` de OAuth directamente en el navegador. **No existe flujo de redirect/Authorization Code** — se eliminó del backend el 2026-08-01 (commit `cdefb7e`); no hay ruta de callback que implementar.
2. `POST /api/auth/google/` con `{"access_token": "<token>"}`.
3. Regla de negocio (no auto-registro, [ADR 0013](../decisions/0013-bloqueo-autoregistro-social.md)): el correo de Google debe corresponder a un `User` ya existente, dado de alta por la SAE. Si no existe cuenta: `400 {"detail": ["No existe una cuenta para este correo. Contacta a la SAE."]}` y no se crea nada.
4. Éxito: `200` con el mismo payload que `/api/auth/login/` (ver abajo).
5. El frontend necesita su propia `VITE_GOOGLE_OAUTH_CLIENT_ID` — **hoy no está en `frontend/.env.example`**, hay que agregarla.

### Login con email/password

`POST /api/auth/login/` — `{"email": "...", "password": "..."}` → `200` con:

```json
{
  "access": "<jwt>",
  "refresh": "<jwt o \"\" si JWT_AUTH_HTTPONLY>",
  "user": { "pk": 1, "email": "...", "first_name": "..." }
}
```

`400` si las credenciales son inválidas (`{"non_field_errors": [...]}`).

**Ojo:** este payload de `user` **no incluye `apellido1`/`apellido2`**, aunque existen en el modelo `User` — `UserDetailsSerializer` (el default de dj-rest-auth, sin override) solo expone campos que calcen con nombres estándar de Django (`first_name`, no `last_name`, no apellidos). Si el frontend necesita nombre completo, hoy no está disponible vía API.

### Transporte del JWT — difiere entre dev y prod

- **Dev:** `JWT_AUTH_HTTPONLY = False` → los tokens viajan en el body JSON (arriba). El SPA los guarda en `localStorage` y manda `Authorization: Bearer <access>` en cada request.
- **Prod (según ADR 0018):** `JWT_AUTH_HTTPONLY = True` → `dj-rest-auth` entrega `access`/`refresh` como cookies `httpOnly`+`Secure`, y el SPA usa `credentials: 'include'` en vez de un header armado a mano.

> **Estado (2026-08-01):** el flujo de cookies de prod ya es funcional — `config/settings/prod.py` define `JWT_AUTH_COOKIE`/`JWT_AUTH_REFRESH_COOKIE`/`JWT_AUTH_SECURE`, y `DEFAULT_AUTHENTICATION_CLASSES` usa `JWTCookieAuthentication` (lee el header si está presente, si no cae a la cookie) — verificado con tests en `accounts/tests/test_auth.py::CookieBasedLoginTests`. Un detalle a tener presente: `access` sigue apareciendo en el body JSON de `/api/auth/login/` y `/api/auth/google/` incluso con `JWT_AUTH_HTTPONLY=True` (comportamiento default de `dj-rest-auth`, no algo que este proyecto controle sin sobreescribir la vista) — el SPA en prod debe simplemente ignorar ese campo del body y depender solo de la cookie (`credentials: 'include'`), nunca leerlo ni guardarlo.

### Refresh y expiración

- Access token: vive 15 minutos (`ACCESS_TOKEN_LIFETIME`). El frontend necesita refrescar en `401` o antes de que expire.
- Refresh token: vive 7 días, **no rota** (`ROTATE_REFRESH_TOKENS = False`) — tras `POST /api/auth/token/refresh/` solo cambia `access`, el refresh guardado sigue siendo válido.
- `POST /api/auth/token/refresh/` → `{"access": "<jwt>", "access_expiration": "<iso datetime>"}`. `access_expiration` lo agrega incondicionalmente `finalize_response` de la vista de refresh (`dj_rest_auth.jwt_auth.RefreshViewWithCookieSupport`), en ambos entornos.
  - **Dev:** body `{"refresh": "<token>"}` — el refresh token viaja explícito en el body (el flujo ya documentado arriba).
  - **Prod:** el refresh token es `httpOnly` — el SPA no puede leerlo ni mandarlo en el body. El call correcto es body vacío `{}` con `credentials: 'include'`; el navegador adjunta la cookie de refresh automáticamente y la vista la usa (`CookieTokenRefreshSerializer.extract_refresh_token` prioriza `request.data['refresh']` y solo cae a la cookie si el body no lo trae — con body vacío, siempre es la cookie). Este es exactamente el flujo que prueba `CookieBasedLoginTests.test_cookie_alone_refreshes_access_token` en `accounts/tests/test_auth.py`.
- `POST /api/auth/token/verify/` — `{"token": "<jwt>"}` → `200`/`401`.

### Logout

`POST /api/auth/logout/` limpia el estado del lado del cliente (cookie si aplica). **No invalida el refresh token en el servidor** — no está instalado `token_blacklist`, así que el refresh sigue siendo válido hasta su expiración natural (7 días) aunque el usuario "cierre sesión". Deuda técnica aceptada, ver [0007](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md).

### Otros endpoints de `accounts`

| Método | Ruta | Auth | Notas |
|---|---|---|---|
| `GET/PUT/PATCH` | `/api/auth/user/` | requerida | ver payload arriba; solo `first_name` es editable |
| `POST` | `/api/auth/password/reset/` | `AllowAny` | `{email}` → siempre `200`, incluso si el correo no existe. El link generado apunta a `{FRONTEND_URL}/reset-password/:uid/:token` — **esa ruta debe existir en el SPA** |
| `POST` | `/api/auth/password/reset/confirm/` | `AllowAny` | `{uid, token, new_password1, new_password2}` |
| `POST` | `/api/auth/password/change/` | requerida | `{old_password, new_password1, new_password2}` |

No existe endpoint de auto-registro (`dj_rest_auth.registration` no está incluido) — coherente con ADR 0013.

## `carreras`

Solo lectura (`ReadOnlyModelViewSet`), sin filtros ni paginación.

| Método | Ruta | Response |
|---|---|---|
| `GET` | `/api/carreras/areas/` | `[{id, nombre}]` |
| `GET` | `/api/carreras/areas/{id}/` | `{id, nombre}` |
| `GET` | `/api/carreras/carreras/` | `[{id, clave, nombre, area: {id, nombre}, acepta_nuevo_ingreso}]` |
| `GET` | `/api/carreras/carreras/{id}/` | idem, un objeto |

`area` viene anidado como objeto, no como id. Campos del modelo que **no** se exponen: `alias`, `siass_id`, `siassypp_id`, `dgeci_id`.

## `materias`

Solo lectura, sin paginación. Filtros por query param (comparación manual en `get_queryset`, no `django-filter`):

- `?carrera=<id>`
- `?habilitada_asesorias=<bool>` — solo `"1"`/`"true"` (case-insensitive) cuentan como verdadero; cualquier otro valor, incluido `"yes"`, se trata como falso.

| Método | Ruta | Response |
|---|---|---|
| `GET` | `/api/materias/materias/` | `[{id, clave, nombre, carrera, nivel, plan, habilitada_asesorias}]` |
| `GET` | `/api/materias/materias/{id}/` | idem, un objeto |

`carrera` aquí es un id plano (a diferencia de `carreras.area`, que va anidado). No hay endpoint para `OfertaMateria` — se carga por management command, nunca vía API.

## `asesorias`

El dominio central. Contexto de negocio completo en [ADR 0016](../decisions/0016-asesorias-academicas.md) y [ADR 0017](../decisions/0017-asesorias-academicas-api.md).

### Permisos por perfil

No hay roles genéricos — se derivan de qué perfil tiene el usuario autenticado:

| Clase | Regla |
|---|---|
| `EsAlumno` | `request.user` tiene `perfil_alumno` |
| `EsAsesorAcademico` | `request.user` tiene `perfil_asesor_academico` |
| `EsAlumnoOAsesorAcademico` | `request.user` tiene `perfil_alumno` **o** `perfil_asesor_academico` (usada en `cancelar`, ver más abajo) |
| `EsDuenoDelRegistro` | (a nivel objeto) el registro/disponibilidad pertenece al asesor autenticado |
| `EsDuenoDeLaAsesoria` | (a nivel objeto) la sesión pertenece al alumno o asesor autenticado |

Denegado → `403` con un mensaje descriptivo (p. ej. `"Se requiere un perfil de alumno."`, `"No puedes operar sobre una sesión ajena."`).

### Rutas — vista de asesor (`registros`, `disponibilidades`)

| Método | Ruta | Notas |
|---|---|---|
| `GET`/`POST` | `/api/asesorias/registros/` | solo los propios; `asesor` se asigna server-side |
| `GET` | `/api/asesorias/registros/{id}/` | |
| `POST` | `/api/asesorias/registros/{id}/materias/` | agrega una materia al registro — `{materia_id}` |
| `GET`/`POST` | `/api/asesorias/disponibilidades/` | solo las propias |
| `GET`/`PATCH`/`DELETE` | `/api/asesorias/disponibilidades/{id}/` | sin `PUT` |

`RegistroAsesor` no acepta `PUT`/`DELETE` en ningún caso; `materias` es de solo lectura en el serializer excepto vía la acción `materias/`, que puede fallar con `400 {"detail": ["La materia no está habilitada para asesorías."]}` o `{"detail": ["La materia no se imparte en este semestre."]}`.

`Disponibilidad` es un slot fijo de 30 minutos, no un rango — `dia_semana` (0=Lunes…6=Domingo), `hora_inicio` debe caer en la rejilla `:00`/`:30`, `formato` (`presencial`/`virtual`) determina si `ubicacion` o `liga_virtual` es obligatorio. Validaciones fallidas → `400 {"detail": ["..."]}`.

### Rutas — vista de alumno (búsqueda y booking)

**`GET /api/asesorias/disponibilidad/buscar/`** — `EsAlumno`. Query params opcionales, combinados con AND: `?materia=<id>`, `?carrera=<id>`, `?formato=presencial|virtual`. Devuelve slots libres ya expandidos por fecha dentro de la ventana agendable:

```json
[{
  "disponibilidad_id": 12,
  "fecha": "2026-08-03",
  "hora_inicio": "10:00:00",
  "hora_fin": "10:30:00",
  "formato": "virtual",
  "ubicacion": "",
  "liga_virtual": "https://..."
}]
```

**Ventana agendable:** hoy hasta el domingo que cierra la semana siguiente (semana en curso + la próxima). Regla fija en código (`asesorias/servicios.py`), no hay modelo de calendario académico — ver [deuda técnica 0001](../technical-debt/0001-sin-modelo-calendario-academico.md).

**`POST /api/asesorias/asesorias/`** — `EsAlumno`. Body: `{disponibilidad, materia, fecha}` — son los **únicos** campos que el cliente escribe; todo lo demás (`alumno`, `carrera`, `hora_inicio`, `formato`, `ubicacion`, `liga_virtual`) se copia server-side desde la disponibilidad y el perfil del alumno al momento de crear, y queda congelado aunque la disponibilidad cambie después.

> **`409` — el único endpoint de toda la API que puede devolverlo:** `{"detail": "Este horario ya fue tomado por otro alumno."}` cuando dos alumnos intentan tomar el mismo slot en la misma fecha (constraint a nivel de base de datos, no un chequeo optimista previo). **El frontend debe manejarlo explícitamente**: no reintentar el mismo POST, sino volver a buscar disponibilidad.

Otros `400` posibles en creación: `"La fecha no coincide con el día de la disponibilidad."`, `"La fecha está fuera de la ventana agendable (semana en curso y la siguiente)."`.

| Método | Ruta | Auth | Notas |
|---|---|---|---|
| `GET` | `/api/asesorias/asesorias/` | requerida | |
| `POST` | `/api/asesorias/asesorias/` | `EsAlumno` | ver arriba, puede dar `409` |
| `GET` | `/api/asesorias/asesorias/{id}/` | requerida | |
| `POST` | `/api/asesorias/asesorias/{id}/cancelar/` | `EsAlumnoOAsesorAcademico` + dueño | `{motivo?}` — el alumno o el asesor dueño de la sesión pueden cancelarla |
| `POST` | `/api/asesorias/asesorias/{id}/marcar_asistencia/` | `EsAsesorAcademico` + dueño | `{asistio: bool}` — falla si es antes de que ocurra la sesión |
| `POST` | `/api/asesorias/asesorias/{id}/notas/` | `EsAsesorAcademico` + dueño | `{texto}` — falla si `asistio` no es `true` |

`Asesoria.estado`: `agendada` (default) → `cancelada` | `realizada`. Nunca se borra un registro. `asistio` es tri-estado: `null` (aún no ocurre/no marcada), `true`, `false`.

Cancelar y crear una asesoría disparan notificaciones por correo vía Celery (asíncronas, no bloquean la response).

`cancelar/` está listado en esta sección de alumno porque nació ahí, pero desde 2026-08-02 no es exclusivo de alumno: el asesor dueño de la sesión también puede cancelarla (ver ADR 0017, changelog).

## Resumen — qué endpoints son `AllowAny`

Todo lo demás requiere `Authorization: Bearer <access>` (o cookie en prod, con la salvedad de la sección de autenticación).

- `GET /api/health/`
- `POST /api/auth/login/`, `/api/auth/google/`, `/api/auth/logout/`
- `POST /api/auth/password/reset/`, `/password/reset/confirm/`
- `POST /api/auth/token/refresh/`, `/token/verify/`

## Ver también

- [ADR 0003 — Google OAuth + allauth + JWT](../decisions/0003-google-oauth-allauth-jwt.md)
- [ADR 0013 — Bloqueo de autoregistro social](../decisions/0013-bloqueo-autoregistro-social.md)
- [ADR 0015 — Catálogo académico](../decisions/0015-catalogo-academico.md) (`carreras`, `materias`)
- [ADR 0016 — Asesorías académicas](../decisions/0016-asesorias-academicas.md) / [ADR 0017 — API](../decisions/0017-asesorias-academicas-api.md)
- [ADR 0018 — Contrato de autenticación frontend-backend](../decisions/0018-contrato-autenticacion-frontend-backend.md)
- [Deuda técnica](../technical-debt/README.md) — en particular 0001 (sin calendario académico), 0006 (sin paginación), 0007 (logout sin invalidación)
