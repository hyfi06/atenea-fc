# 0022 — Detección de rol por usuario, no por sesión, en pantallas de asesoría

**Estado:** Activa
**Origen:** [Spec: fixes de staging B1–B5](../superpowers/specs/2026-08-19-fixes-staging-design.md)

## Qué se simplificó

`DetalleAsesoria.tsx` y `TarjetaAsesoria.tsx` deciden qué rol tiene quien
mira una asesoría (`esAsesor = useEsAsesor()`) a partir del rol del
**usuario autenticado**, no del rol que ese usuario tiene **en esa
asesoría en particular**. Para un usuario mono-rol (solo alumno, o solo
asesor) esto es correcto siempre. Pero el backend ya contempla usuarios
de doble rol: `AsesoriaViewSet.get_queryset` (`backend/asesorias/views.py`)
une las sesiones donde el usuario participa como alumno con las que
participa como asesor (ver deuda [0011](0011-doble-rol-alumno-asesor-solo-ve-alumno.md)
y el comentario en `get_queryset`, `backend/asesorias/views.py:256-258`).

Para un usuario con doble rol que abre una asesoría donde participa como
**alumno** (no como asesor), la pantalla lo trata como si fuera el asesor
de esa sesión: etiqueta la fila de la contraparte como "Alumno" y muestra
su propio nombre, ofrece los botones de marcar asistencia para una sesión
que no puede marcar, y —más grave— intenta leer/editar `asesoria.notas`,
campo que el serializer omite para quien no es el asesor dueño de esa
sesión específica ([ADR 0021](../decisions/0021-asesorias-alumno-api.md);
gate en `AsesoriaSerializer.to_representation`,
`backend/asesorias/serializers.py:215-216`).

## Por qué era razonable

El plan que introdujo esto (fixes de staging B3/B4, agosto 2026) resuelve
5 bugs concretos de una revisión manual; ningún usuario de producción
tiene hoy doble rol simultáneo (alumno y asesor), así que el caso no es
alcanzable en el despliegue actual. Corregirlo bien requiere un
discriminador por-sesión (comparar `asesoria.alumno` contra el id del
perfil de alumno del usuario, en vez de `useEsAsesor()` a secas), que es
un cambio de diseño más amplio que el alcance de "corregir 5 bugs de
staging" — se documenta en vez de improvisarse dentro de ese plan.

## Señal de revisión

Revisar en cuanto exista al menos un usuario real con perfil de alumno Y
perfil de asesor activo simultáneamente (hoy 0). Cuando eso ocurra,
reemplazar `useEsAsesor()` en `DetalleAsesoria.tsx` y `TarjetaAsesoria.tsx`
por un discriminador por-sesión, por ejemplo
`asesoria.alumno === user.perfil_alumno?.id ? 'alumno' : 'asesor'`, y
agregar un test que monte un usuario con ambos perfiles abriendo una
sesión donde participa como alumno.
