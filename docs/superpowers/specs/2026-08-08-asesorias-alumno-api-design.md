## Asesorías Académicas — API del lado alumno (oferta, agendado por asesor, ocultar notas)

**Status:** Approved
**Date:** 2026-08-08

### Context

La capa DRF de Asesorías ([ADR 0017](../../decisions/0017-asesorias-academicas-api.md), spec `2026-07-30-asesorias-academicas-api-design.md`) expone el flujo del asesor completo y un flujo de alumno **mínimo**: búsqueda de disponibilidad anónima (`GET /api/asesorias/disponibilidad/buscar/`) y agendado (`POST /api/asesorias/asesorias/`). El frontend del alumno (spec gemela `2026-08-08-asesorias-alumno-frontend-design.md`, [ADR 0022](../../decisions/0022-asesorias-vista-unificada-frontend.md)) necesita un flujo **centrado en asesor**: elegir materia → elegir asesor → ver sus días en la ventana de dos semanas → elegir bloque → elegir carrera → agendar. La API actual no lo soporta y además filtra un dato que el alumno no debe ver.

Esta spec cubre sólo los huecos de la API del lado alumno. No reabre decisiones de ADR 0017 ni toca el flujo del asesor.

**Estado actual del código** (referencias verificadas):
- `BuscarDisponibilidadView` (`asesorias/views.py:96`) devuelve slots **anónimos** (`ResultadoBusquedaSerializer`, `serializers.py:61`): `disponibilidad_id, fecha, hora_inicio, hora_fin, formato, ubicacion, liga_virtual`. No filtra por asesor ni expone su identidad.
- `AsesoriaSerializer` (`serializers.py:88`) incluye `notas` en `fields` (`:100`) y en `read_only_fields` (`:105`); `AsesoriaViewSet.get_queryset` (`views.py:156`) sólo exige `IsAuthenticated` en `list`/`retrieve` y une ambos lados por rol con `Q` (`:173-180`). **Hoy el alumno recibe `notas` del asesor** en cada consulta de sus sesiones — leak.
- `AsesoriaSerializer.validate` (`serializers.py:130`) fija `carrera = alumno.carrera` ignorando cualquier valor del payload; `carrera` está en `read_only_fields` (`:104`).
- `GET /api/materias/materias/?habilitada_asesorias=true` filtra materias por flag, **no** por disponibilidad real de asesores.
- Ya existen y se reutilizan sin cambios: `EsAlumno`/`EsAsesorAcademico`/`EsDuenoDeLaAsesoria` (`asesorias/permissions.py`), `ventana_agendable()` (`asesorias/servicios.py:6`), `GET /api/asesorias/asesorias/?semestre=` y `GET /api/asesorias/asesorias/semestres/` (`views.py:187,236`).

**Prerrequisito:** ninguno de modelo — esta spec no crea migraciones. Todo se resuelve en views/serializers salvo la escritura de `carrera` (ver Decision 4), que tampoco cambia el esquema.

### Decisions captured

1. **Endpoint de oferta**: `GET /api/asesorias/oferta/?carrera=&buscar=` como `APIView` dedicada (no viewset), consistente con `BuscarDisponibilidadView`. Devuelve las **materias que tienen ≥1 asesor con `Disponibilidad.activa`** en el semestre vigente (derivadas de `Disponibilidad.objects.filter(activa=True) → registro__materias`), no las materias por flag. `carrera` (filtra `materia.carrera_id`) y `buscar` (`nombre__icontains`) son opcionales. Permiso `EsAlumno`.
2. **Endpoint de asesores por materia**: `GET /api/asesorias/oferta/{materia_id}/asesores/`, `APIView`, `EsAlumno`. Devuelve los asesores con disponibilidad activa para esa materia: `[{registro_id, asesor_nombre, area_nombre, formatos: ["presencial","virtual"]}]`. Cierra el hueco de que la búsqueda es anónima: el nombre del asesor sólo aparecía tras agendar (`AsesoriaSerializer.asesor_nombre`).
3. **Disponibilidad de un asesor**: extender `BuscarDisponibilidadView` con `?asesor=<registro_id>` (filtra `registro_id`) y añadir `registro_id` + `asesor_nombre` a `ResultadoBusquedaSerializer`. El frontend agrupa los resultados por `fecha` para dibujar días → bloques. La proyección sobre la ventana `ventana_agendable()` y la exclusión de slots ocupados no cambian.
4. **Carrera elegible al agendar**: `carrera` pasa a ser **escribible** en `AsesoriaSerializer` (sale de `read_only_fields`). `validate` la valida contra las carreras del alumno — hoy el conjunto es exactamente `{alumno.carrera}` (una sola, [deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md)); si el payload la omite o envía la única carrera del alumno, se usa `alumno.carrera`; cualquier otra → `400`. Se conserva el snapshot (`carrera` no se reescribe si `PerfilAlumno.carrera` cambia después). Sin cambios de modelo.
5. **Ocultar `notas` al alumno**: `AsesoriaSerializer` deja de emitir `notas` cuando el solicitante **no es el asesor dueño** de la sesión. Se implementa quitando el campo en `to_representation`/`get_fields` según `context["request"].user` (asesor de la sesión = `obj.disponibilidad.registro.asesor.user`). Corrige el leak sin serializers duplicados y deja el dato disponible para el asesor y (futuro) admin. Es una **corrección de seguridad**, no deuda diferida.
6. **Sin nuevos permisos ni modelos**: se reutiliza `EsAlumno` y el `AsesoriaViewSet` compartido. Los dos endpoints nuevos son de sólo lectura y scoped por la ventana agendable, no por dueño (la oferta es pública para cualquier alumno autenticado).

### Resources & endpoints

```
# Nuevos (alumno)
GET  /api/asesorias/oferta/                      # ?carrera=&buscar=  -> materias con asesores disponibles
GET  /api/asesorias/oferta/{materia_id}/asesores/ # asesores con disponibilidad activa para la materia

# Modificados
GET  /api/asesorias/disponibilidad/buscar/       # + ?asesor=<registro_id>; result + registro_id, asesor_nombre
POST /api/asesorias/asesorias/                    # body acepta carrera (validada contra carreras del alumno)
GET  /api/asesorias/asesorias/                    # notas omitido salvo para el asesor dueño

# Reutilizados sin cambios
GET  /api/asesorias/asesorias/?semestre=          # historial filtrado
GET  /api/asesorias/asesorias/semestres/          # claves de semestre (subtabs)
POST /api/asesorias/asesorias/{id}/cancelar/      # alumno dueño
```

Formas de respuesta nuevas/extendidas:

```
# GET /oferta/
[{ "materia_id": 12, "nombre": "Cálculo III", "carrera_id": 3, "num_asesores": 2 }]

# GET /oferta/{materia_id}/asesores/
[{ "registro_id": 7, "asesor_nombre": "Ana López", "area_nombre": "Matemáticas",
   "formatos": ["presencial", "virtual"] }]

# GET /disponibilidad/buscar/?materia=&asesor=  (campos añadidos en negrita)
[{ "registro_id": 7, "asesor_nombre": "Ana López",
   "disponibilidad_id": 41, "fecha": "2026-08-11", "hora_inicio": "10:00", "hora_fin": "10:30",
   "formato": "presencial", "ubicacion": "Salón 4", "liga_virtual": "" }]
```

### Data flow

- **Oferta**: alumno abre "Nueva asesoría" → `GET /oferta/?carrera=&buscar=` → lista de materias con asesores. Filtro por carrera y búsqueda por nombre son parámetros de la misma llamada (o filtrado en cliente sobre el resultado; ver spec frontend).
- **Detalle de materia**: `GET /oferta/{materia}/asesores/` → lista de asesores. El alumno elige uno.
- **Disponibilidad del asesor**: `GET /disponibilidad/buscar/?materia=&asesor=<registro_id>` → slots dentro de la ventana; el frontend los agrupa por `fecha` (días, dos semanas) y por bloque.
- **Agendar**: `POST /asesorias/` con `{disponibilidad, fecha, materia, carrera}` → `AsesoriaSerializer.validate` dispara `Asesoria.clean()` (día-de-semana + ventana) y valida `carrera` contra las carreras del alumno → transacción → `409` si otro alumno ganó la carrera (sin cambios respecto a ADR 0017 dec. 8).
- **Mis sesiones / historial**: `GET /asesorias/` (unión por rol) y `?semestre=`; el alumno **no** recibe `notas`. `semestres/` alimenta los subtabs.

### Error handling

| Situación | Código | Origen |
|---|---|---|
| Sin autenticación | `401` | `IsAuthenticated` (default DRF) |
| No-alumno llamando `/oferta/`, `/oferta/{m}/asesores/`, `/disponibilidad/buscar/`, `POST /asesorias/` | `403` | `EsAlumno` |
| `materia_id` inexistente en `/oferta/{materia_id}/asesores/` | `404` | lookup del `APIView` |
| `carrera` ajena al alumno en `POST /asesorias/` | `400` | `AsesoriaSerializer.validate` |
| `ValidationError` de `Asesoria.clean()` (fuera de ventana, día equivocado) | `400` | capturado en la vista, mensaje del modelo |
| Doble-booking (condición de carrera en `INSERT`) | `409` | `IntegrityError` del `UniqueConstraint`, ya existente |

### Testing

`APITestCase` + `force_authenticate`, por flujo:
- **Oferta**: sólo devuelve materias con ≥1 disponibilidad activa; una materia habilitada pero sin asesores con disponibilidad **no** aparece; `?carrera=` y `?buscar=` filtran; no-alumno → `403`.
- **Asesores por materia**: lista los registros con disponibilidad activa (nombre, área, formatos); materia sin asesores → `[]`; `materia_id` inexistente → `404`.
- **Disponibilidad por asesor**: `?asesor=` restringe a ese registro; el resultado incluye `registro_id`/`asesor_nombre`; respeta ventana y excluye ocupados (regresión de ADR 0017).
- **Carrera al agendar**: agendar con la carrera del alumno → `201`; omitir `carrera` → usa `alumno.carrera`; enviar una carrera ajena → `400`; el snapshot conserva la carrera aunque `PerfilAlumno.carrera` cambie después.
- **Ocultar notas (seguridad)**: como alumno dueño, `GET /asesorias/` y `retrieve` **no** contienen `notas`; como asesor dueño, sí; regresión: un usuario doble-rol ve `notas` sólo en las sesiones donde es el asesor.

### Out of scope

- Modelo `HistoriaAcademica` / múltiples carreras por alumno — [deuda 0008](../../technical-debt/0008-perfil-alumno-una-sola-carrera.md), ya registrada. La escritura de `carrera` queda lista para cuando el conjunto sea >1.
- Paginación de `/oferta/` y de los listados — [deuda 0006](../../technical-debt/0006-sin-paginacion-listados.md).
- Modelo de calendario académico (la ventana sigue fija en código) — [deuda 0001](../../technical-debt/0001-sin-modelo-calendario-academico.md).
- Vista de admin (mostrar ambos nombres, ver `notas`) — el serializer deja el dato accesible, pero el endpoint/rol admin es trabajo posterior.
- Documentación OpenAPI de los endpoints nuevos.

### Self-review

- Sin placeholders/TBD: cada endpoint nuevo tiene ruta, permiso, forma de respuesta y casos de prueba concretos.
- Alcance cohesivo: sólo los huecos de la API del lado alumno; no toca el flujo del asesor ni reabre ADR 0017.
- Sin contradicciones con ADR 0017: reutiliza `AsesoriaViewSet` compartido, `ventana_agendable()`, el patrón `APIView` de búsqueda y el `409` por doble-booking; la ocultación de `notas` corrige un comportamiento que ADR 0017 no había especificado.
- Consistente con patrones previos: `APIView` dedicada para transformaciones que no son CRUD, permisos por `hasattr`, filtrado manual por query param (igual que `materias/views.py` y el filtro `?semestre=`).
- Deuda referenciada, no duplicada: carrera múltiple → 0008 existente; paginación → 0006; calendario → 0001. No se crea deuda nueva. El leak de `notas` se corrige aquí (no es deuda).
