# 0010 — API no expone perfil ni rol del usuario autenticado

**Estado:** Resuelta — 2026-08-04 ([plan de backend](../superpowers/plans/2026-08-04-login-oauth-backend.md), ver Changelog de [ADR 0017](../decisions/0017-asesorias-academicas-api.md))
**Origen:** [ADR 0017](../decisions/0017-asesorias-academicas-api.md), [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md)

## Qué se simplificó

`GET /api/auth/user/` devuelve únicamente `{pk, email, first_name}` — no indica
qué perfil de negocio (`PerfilAlumno`, `PerfilAsesorAcademico`, `PerfilAcademico`)
tiene el usuario autenticado. Tampoco existe ningún endpoint donde un usuario
pueda resolver el nombre de **otro** usuario a partir del id de su perfil:
`AsesoriaSerializer` expone `alumno` como un id plano (`PerfilAlumno.id`), y no
hay ruta para que un asesor consulte el nombre asociado a ese id.

El frontend de la Fase 1 (asesorías — vista de asesor) resuelve esto con dos
workarounds:

1. **Detección de rol tras login:** sondea `GET /api/asesorias/registros/`
   (exclusivo de `EsAsesorAcademico`) y usa el código de estado (200 vs 403)
   para decidir si el usuario es asesor. No escala a más de un rol sin agregar
   una llamada de sondeo por cada rol a verificar.
2. **Nombre de alumno en la UI:** se muestra `"Alumno #<id>"` en vez de un
   nombre, en la lista y detalle de asesorías del asesor.

Un tercer campo relacionado, encontrado en `backend/asesorias/serializers.py`:
`AsesoriaSerializer.Meta.fields` no incluye `motivo_cancelacion` ni
`cancelado_por`, aunque el modelo `Asesoria` sí los tiene y `cancelar()` los
llena. El panel de "asesoría cancelada" en el detalle del asesor no puede
mostrar el motivo por esta razón — muestra solo el estado, sin motivo, hasta
que se agreguen esos dos campos al serializer.

## Por qué era razonable

Agregar campos de perfil/rol al serializer de `User` o de `Asesoria` es un
cambio de backend pequeño pero con superficie propia (qué campos exponer, a
quién, si expandir `alumno` a un objeto rompe compatibilidad con lo que ya
consume el body de creación) — se decidió tratarlo como su propio cambio de
backend en vez de mezclarlo dentro del plan de frontend que lo necesita.

## Señal de revisión

- Antes de construir la **Fase 2** (vista de alumno): si el alumno también
  necesita ver el nombre de su asesor, el mismo gap se repite en el otro
  sentido — dos parches iguales es la señal de que ya no es aceptable
  posponerlo.
- Antes de construir la **Fase 3** (vista de administración): el patrón de
  "sondear un endpoint por rol" no funciona para un panel que necesita listar
  *todos* los roles de *todos* los usuarios — en ese punto el sondeo deja de
  ser viable y este ítem se vuelve bloqueante, no solo incómodo.
- Si un asesor pide ver el motivo de una cancelación hecha por el alumno: la
  señal de que `motivo_cancelacion`/`cancelado_por` ya no pueden seguir fuera
  del serializer.

## Cómo se resolvió

Los tres puntos se cerraron en la misma pasada de backend:

1. **Detección de rol:** `GET /api/auth/user/` (y la clave `user` del body de login, mismo serializer) expone `roles` — lista de claves estables (`"alumno"`, `"academico"`, `"asesor_academico"`) — más un objeto por perfil o `null`, derivados de los `OneToOneField` inversos ya existentes. El sondeo de `GET /api/asesorias/registros/` (200 vs 403) deja de ser necesario. `roles` sigue el mismo criterio que la permission class `EsAsesorAcademico` (el perfil existe), no `activo`, para que la UI no oculte una pantalla a la que el backend sí da acceso.
2. **Nombre de la contraparte:** `AsesoriaSerializer` gana `alumno_nombre` y `asesor_nombre` (de solo lectura, vía `User.nombre_completo`), como campos **hermanos** de `alumno` — que sigue siendo un id plano, así que no se rompe ningún consumidor del payload, que era la preocupación registrada arriba en "Por qué era razonable". Se agregaron las dos direcciones a la vez y no solo la del asesor, precisamente porque la señal de revisión de este ítem nombraba el caso simétrico (Fase 2, el alumno viendo a su asesor) como el disparador de un segundo parche idéntico.
3. **Campos de cancelación:** `motivo_cancelacion` y `cancelado_por` entraron a `AsesoriaSerializer.Meta.fields`, más un `cancelado_por_rol` derivado (`"alumno"`/`"asesor"`/`"otro"`/`null`) — el id crudo de `User` no basta para renderizar el panel de cancelación, porque ninguna de las dos partes conoce el id de `User` de la otra.

Lo que **no** cubre: sigue sin existir un endpoint donde un usuario resuelva el nombre de otro a partir de un id de perfil arbitrario, fuera del contexto de una `Asesoria` que comparten. La señal de revisión de la Fase 3 (panel de administración, que necesita listar todos los roles de todos los usuarios) sigue vigente y no se resolvió aquí.
