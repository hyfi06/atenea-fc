# 0010 — API no expone perfil ni rol del usuario autenticado

**Estado:** Activa
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
