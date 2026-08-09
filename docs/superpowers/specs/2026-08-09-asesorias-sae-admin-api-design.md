## Asesorías Académicas — API de administración SAE (identidad `PerfilSAE`, superficie admin de solo lectura)

**Status:** Approved
**Date:** 2026-08-09

### Context

La capa DRF de Asesorías ([ADR 0017](../../decisions/0017-asesorias-academicas-api.md), [ADR 0021](../../decisions/0021-asesorias-alumno-api.md)) sirve a dos personas: **alumno** y **asesor**. Ambos flujos están acotados al usuario autenticado: `AsesoriaViewSet.get_queryset` (`asesorias/views.py`) une por rol las sesiones donde el usuario es alumno **o** asesor, y los endpoints de oferta/búsqueda son `EsAlumno`. **No hay ningún rol ni endpoint para un miembro de la SAE** que supervise el servicio de forma transversal.

Esta spec introduce la **identidad SAE** y una superficie de API **de solo lectura** para que un miembro de la SAE consulte todas las asesorías, la oferta y el directorio de asesores. El miembro SAE funge casi como administrador de este servicio: ve datos de asesor **y** alumno, incluidas las `notas`. No agenda, no edita, no cancela.

La spec gemela [`2026-08-09-asesorias-sae-admin-frontend-design.md`](2026-08-09-asesorias-sae-admin-frontend-design.md) ([ADR 0024](../../decisions/0024-asesorias-sae-admin-frontend.md)) consume estos contratos.

**Estado actual del código (referencias verificadas):**
- Roles se derivan por existencia de perfil (`hasattr(user, "perfil_alumno" / "perfil_academico" / "perfil_asesor_academico")`). `UserDetailsSerializer.get_roles` (`accounts/serializers.py:109-120`) arma el array `roles` con `"alumno"`/`"academico"`/`"asesor_academico"`.
- Perfiles siguen el patrón `PerfilX` OneToOne a `User` ([ADR 0012](../../decisions/0012-perfiles-identidad-roles.md)): `PerfilAlumno`/`PerfilAcademico` (`accounts/models.py`), `PerfilAsesorAcademico` (`asesorias/models.py`).
- Permisos en `asesorias/permissions.py`: `EsAlumno`, `EsAsesorAcademico`, `EsAlumnoOAsesorAcademico`, `EsDuenoDelRegistro`, `EsDuenoDeLaAsesoria` — todos por `hasattr`.
- `AsesoriaSerializer` (`asesorias/serializers.py`) ya expone `alumno_nombre` y `asesor_nombre`, y **oculta `notas`** a quien no sea el asesor dueño vía `to_representation` (fix de privacidad de ADR 0021).
- Endpoints de consulta hoy `EsAlumno`: `OfertaView` (`GET /api/asesorias/oferta/?carrera=&buscar=`), `AsesoresDeMateriaView` (`GET /api/asesorias/oferta/{materia_id}/asesores/`), `BuscarDisponibilidadView` (`GET /api/asesorias/disponibilidad/buscar/?materia=&carrera=&formato=&asesor=`).
- `RegistroAsesor` (per-semestre, M2M a materias), `Disponibilidad` (bloques de 30 min) y `PerfilAsesorAcademico` (`area`, `activo`) ya modelan lo que el directorio necesita mostrar.
- `ventana_agendable()` (`asesorias/servicios.py`) fija la ventana de dos semanas usada por la búsqueda de disponibilidad.

**Prerrequisito de modelo:** una migración para `PerfilSAE` (única del feature). El resto son views/serializers/permisos, sin cambios de esquema en asesorías existentes.

### Decisions captured

1. **Identidad SAE — `PerfilSAE`.** Nuevo perfil OneToOne a `User` siguiendo el patrón `PerfilX` ([ADR 0012](../../decisions/0012-perfiles-identidad-roles.md)). Ubicación: app `accounts` (junto a `PerfilAlumno`/`PerfilAcademico`, ya que no es específico de asesorías y otros servicios SAE lo reutilizarán). Campos mínimos: `user` (OneToOne), `activo` (bool). Se registra en el Django admin para alta manual. **Alta sólo por admin** → [deuda 0014](../../technical-debt/0014-alta-perfil-sae-solo-admin.md) (hermana de [0002](../../technical-debt/0002-alta-perfil-asesor-solo-admin.md)).
2. **Rol `'sae'` en login.** `UserDetailsSerializer.get_roles` añade `"sae"` cuando `hasattr(user, "perfil_sae")`. El SPA lo consume para guardas y navegación.
3. **Permiso `EsMiembroSAE`.** Nuevo en `asesorias/permissions.py`: `hasattr(request.user, "perfil_sae")`. Más `EsAlumnoOMiembroSAE` para los endpoints de consulta compartidos.
4. **Reuso de endpoints de consulta (oferta / asesores-por-materia / búsqueda).** `OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` amplían su permiso de `EsAlumno` a **`EsAlumnoOMiembroSAE`**. El SAE consulta el mismo flujo materias → asesores → disponibilidad que el alumno, pero **no puede** `POST /asesorias/` (agendar sigue `EsAlumno`). Cero duplicación de estos endpoints. La búsqueda para el SAE usa la misma `ventana_agendable()` (consulta lo agendable ahora; el histórico de disponibilidad no se modela — ver Out of scope).
5. **Superficie admin de solo lectura bajo `/api/asesorias/admin/`.** Endpoints nuevos con permiso `EsMiembroSAE`, en views dedicadas (no se toca el `AsesoriaViewSet` acotado al usuario):
   - `GET /admin/asesorias/?asesor=&alumno=&semestre=&estado=` — todas las sesiones, con `alumno_nombre` **y** `asesor_nombre`. Sin `?semestre` → próximas agendadas (por defecto `estado=agendada`, `fecha >= hoy`, orden ascendente). Filtros por `asesor` (perfil id — ver dec. 8), `alumno` (perfil id), `semestre`, `estado`.
   - `GET /admin/semestres/` — **todos** los semestres del sistema con asesorías (`Asesoria` → `disponibilidad__registro__semestre`, distinct, ordenado desc), para los subtabs de histórico. Distinto del `asesorias/semestres/` existente, que es por-usuario.
   - `GET /admin/asesores/` — directorio: `[{perfil_id, nombre, area_nombre, activo, num_materias_semestre_vigente}]`, ordenado por nombre.
   - `GET /admin/asesores/{perfil_id}/?semestre=` — detalle read-only de un asesor: sus materias del registro del semestre (default: vigente) y su disponibilidad. Alimenta la reutilización read-only de `MisMaterias`/`MiHorario` en el frontend. Forma: `{perfil_id, nombre, area_nombre, activo, semestre, materias: [...], disponibilidades: [...]}`.
   - `GET /admin/alumnos/?buscar=` — autocompletar alumno por nombre o `numero_cuenta` (`icontains`, límite fijo de resultados). Alimenta el filtro por alumno del frontend (conjunto grande → búsqueda, no select).
6. **`notas` visibles para el SAE.** El gate de `to_representation` que hoy oculta `notas` a quien no es el asesor dueño se amplía: se muestran `notas` si el solicitante **es el asesor dueño** **o** **es miembro SAE**. El endpoint `/admin/asesorias/` usa el mismo `AsesoriaSerializer` (o una subclase `AsesoriaAdminSerializer` si conviene aislar el comportamiento), garantizando que el SAE ve la sesión completa. El alumno sigue sin ver `notas` (no se reabre ADR 0021).
7. **Solo lectura, sin paginación (por ahora).** Todos los endpoints admin son `GET`. No hay `POST`/`PATCH`/`DELETE` para el SAE en esta fase. Sin paginación, coherente con [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md); el histórico admin-wide es el caso que más presiona esa deuda a futuro (se referencia, no se resuelve aquí).
8. **Filtro por asesor = por `PerfilAsesorAcademico.id`.** El directorio (`/admin/asesores/`) devuelve `perfil_id`; ese id filtra `/admin/asesorias/?asesor=` (`disponibilidad__registro__asesor_id`). Se valida `digit`/lenient igual que los filtros existentes de `BuscarDisponibilidadView` (un valor no numérico se ignora, no rompe).

### Resources & endpoints

```
# Nuevos (admin SAE, permiso EsMiembroSAE, solo lectura)
GET  /api/asesorias/admin/asesorias/            # ?asesor=&alumno=&semestre=&estado=
GET  /api/asesorias/admin/semestres/            # todos los semestres del sistema
GET  /api/asesorias/admin/asesores/             # directorio de asesores
GET  /api/asesorias/admin/asesores/{perfil_id}/ # ?semestre=  detalle materias + disponibilidad
GET  /api/asesorias/admin/alumnos/              # ?buscar=  autocompletar alumno

# Modificados (permiso EsAlumno -> EsAlumnoOMiembroSAE)
GET  /api/asesorias/oferta/                     # ?carrera=&buscar=
GET  /api/asesorias/oferta/{materia_id}/asesores/
GET  /api/asesorias/disponibilidad/buscar/      # ?materia=&carrera=&formato=&asesor=

# Modificado (comportamiento de serializer)
GET  /api/asesorias/admin/asesorias/            # notas visible para miembro SAE
```

Formas de respuesta nuevas:

```
# GET /admin/asesorias/
[{ "id": 88, "estado": "agendada", "fecha": "2026-08-12", "hora_inicio": "10:00",
   "materia": 12, "carrera": 3, "formato": "presencial", "ubicacion": "Salón 4",
   "liga_virtual": "", "alumno_nombre": "Juan Pérez", "asesor_nombre": "Ana López",
   "asistio": null, "notas": "" }]

# GET /admin/semestres/
["2026-2", "2026-1", "2025-2"]

# GET /admin/asesores/
[{ "perfil_id": 7, "nombre": "Ana López", "area_nombre": "Matemáticas",
   "activo": true, "num_materias_semestre_vigente": 3 }]

# GET /admin/asesores/7/?semestre=2026-2
{ "perfil_id": 7, "nombre": "Ana López", "area_nombre": "Matemáticas", "activo": true,
  "semestre": "2026-2",
  "materias": [{ "id": 12, "clave": "1234", "nombre": "Cálculo III" }],
  "disponibilidades": [{ "id": 41, "dia_semana": 1, "hora_inicio": "10:00", "hora_fin": "10:30",
                         "formato": "presencial", "ubicacion": "Salón 4", "liga_virtual": "",
                         "activa": true }] }

# GET /admin/alumnos/?buscar=jua
[{ "perfil_id": 15, "nombre": "Juan Pérez", "numero_cuenta": "312345678" }]
```

### Data flow

- **Identidad:** admin da de alta `PerfilSAE(user, activo=True)` en Django admin → `GET /api/auth/user/` devuelve `roles` con `"sae"` → el SPA habilita el área SAE.
- **Agendadas / histórico:** `GET /admin/asesorias/` (default próximas agendadas) y con `?semestre=` (histórico); `?asesor=`/`?alumno=` acotan. `GET /admin/semestres/` alimenta los subtabs. Cada tarjeta muestra ambos nombres y (para el SAE) `notas`.
- **Oferta (consulta):** reutiliza `GET /oferta/?carrera=&buscar=` → `GET /oferta/{materia}/asesores/` → `GET /disponibilidad/buscar/?materia=&asesor=` — idéntico al alumno, sin el `POST` de agendado.
- **Directorio de asesores:** `GET /admin/asesores/` → `GET /admin/asesores/{perfil_id}/?semestre=` → el frontend pinta materias + horario en modo solo-lectura.
- **Filtro por alumno:** `GET /admin/alumnos/?buscar=` (autocompletar) → `perfil_id` → `GET /admin/asesorias/?alumno=`.

### Error handling

| Situación | Código | Origen |
|---|---|---|
| Sin autenticación | `401` | `IsAuthenticated` (default DRF) |
| No-SAE llamando cualquier `/admin/...` | `403` | `EsMiembroSAE` |
| No-alumno y no-SAE llamando `/oferta/`, `/oferta/{m}/asesores/`, `/disponibilidad/buscar/` | `403` | `EsAlumnoOMiembroSAE` |
| SAE intentando `POST /asesorias/` | `403` | `EsAlumno` (no se amplía) |
| `perfil_id` inexistente en `/admin/asesores/{id}/` | `404` | lookup del view |
| Filtro no numérico (`asesor`, `alumno`) | ignorado (200) | validación lenient, como `BuscarDisponibilidadView` |
| `?semestre=` inexistente en `/admin/asesorias/` | `[]` (200) | filtro sin match |

### Testing

`APITestCase` + `force_authenticate`, por flujo:
- **Permiso SAE:** con `PerfilSAE`, `/admin/*` → `200`; sin él → `403`; `POST /asesorias/` como SAE → `403`. `roles` incluye `"sae"` sólo con el perfil.
- **Endpoints compartidos ampliados:** un SAE (sin `PerfilAlumno`) obtiene `200` en `/oferta/`, `/oferta/{m}/asesores/`, `/disponibilidad/buscar/`; un usuario sin alumno ni SAE → `403` (regresión del gate `EsAlumno` previo).
- **Listado admin:** `/admin/asesorias/` devuelve sesiones de **distintos** asesores/alumnos (no acotado al caller); `?asesor=` filtra por perfil de asesor; `?alumno=` por perfil de alumno; `?semestre=` por semestre; `?estado=` por estado; sin `?semestre` → próximas agendadas.
- **Notas visibles al SAE:** la respuesta de `/admin/asesorias/` incluye `notas`; regresión: el alumno dueño sigue **sin** ver `notas` en `/asesorias/`.
- **Semestres admin:** lista todos los semestres del sistema (de varios asesores), no sólo los del caller.
- **Directorio + detalle:** `/admin/asesores/` lista todos con conteo de materias del semestre vigente; `/admin/asesores/{id}/` devuelve materias y disponibilidad del semestre pedido; `perfil_id` inexistente → `404`.
- **Autocompletar alumno:** `?buscar=` filtra por nombre y por `numero_cuenta`; límite de resultados respetado.

### Out of scope

- Cualquier acción de escritura del SAE (cancelar, reasignar, editar disponibilidad, alta de asesores desde la app). Esta fase es solo lectura.
- Alta de `PerfilSAE` fuera del Django admin → [deuda 0014](../../technical-debt/0014-alta-perfil-sae-solo-admin.md).
- Histórico de **disponibilidad** por semestre pasado (la disponibilidad no versiona su estado activa/inactiva en el tiempo) — [deuda 0005](../../technical-debt/0005-editar-disponibilidad-no-propaga.md) toca terreno cercano; el detalle del asesor muestra la disponibilidad **actual** del registro del semestre pedido.
- Paginación de los listados admin → [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).
- Scope de semestre vigente en oferta/búsqueda → [deuda 0012](../../technical-debt/0012-oferta-asesorias-sin-scope-de-semestre.md) (heredada; el SAE consulta la misma oferta que el alumno).
- Documentación OpenAPI de los endpoints nuevos.

### Self-review

- Sin placeholders/TBD: cada endpoint tiene ruta, permiso, forma de respuesta y casos de prueba.
- Alcance cohesivo: identidad SAE + superficie admin de solo lectura; no reabre ADR 0017/0021 ni toca los flujos de alumno/asesor salvo ampliar un permiso y un gate de `notas`.
- Consistente con patrones previos: perfil `PerfilX` (ADR 0012), permisos por `hasattr`, `APIView` para lecturas no-CRUD, filtrado lenient por query param, reuso de `AsesoriaSerializer`.
- Deuda referenciada, no duplicada: alta manual → **0014 (nueva)**; paginación → 0006; scope de semestre → 0012; disponibilidad histórica → 0005. La visibilidad de `notas` para el SAE es una decisión de producto explícita, no deuda.
