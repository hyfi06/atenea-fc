# 0027 — Usuarios reales: historia académica, periodo académico y autoservicio de asesor

**Status:** Accepted
**Date:** 2026-08-15

## Context

Atenea abre a usuarios reales para el semestre 20271. Eso rompe tres supuestos del MVP: que un alumno tiene exactamente una carrera y un correo, que "el semestre vigente" se puede derivar de una heurística de fecha sin fechas reales detrás, y que la SAE puede dar de alta a cada asesor a mano en el admin de Django. Además, la Home pinta nueve servicios mock sin backend a cualquier usuario, y ni el alumno ni el académico tienen una entrada a `/asesorias` desde ahí.

## Decision

1. **`HistoriaAcademica(perfil_alumno, carrera, generacion)` reemplaza `PerfilAlumno.carrera`/`generacion`.** Sin `unique_together` sobre `perfil_alumno`: un alumno puede tener varias filas (carrera simultánea o segunda carrera bajo el mismo `numero_cuenta`). Deja de existir una "carrera activa" denormalizada. Vive en `accounts`, junto a `PerfilAlumno`: es identidad del alumno y la lee `UserDetailsSerializer`, así que ponerla en otra app obligaría a `accounts` a importar esa app.
2. **`Asesoria.carrera` no cambia**: sigue siendo un snapshot explícito del payload (ADR 0021). Con una sola fila de historia el backend la infiere por conveniencia; con dos o más, exige el campo y el frontend pregunta.
3. **`PerfilAlumno.correos_alternos`** (`ArrayField(EmailField)`) guarda los correos que la SAE conoce además del de login. Nunca se expone al propio alumno ni participa en la autenticación: solo en el admin de Django y en endpoints con permiso `EsMiembroSAE`.
4. **App nueva `academico`** con `PeriodoAcademico(semestre, fecha_inicio, fecha_fin, registro_asesores_inicio, registro_asesores_fin)`, gestionado a mano desde el admin por la SAE cada semestre (mismo criterio que `PerfilSAE`). La heurística `semestre_vigente()` se porta ahí desde el frontend, y `asesorias.servicios.semestre_vigente` pasa a delegar en ella — la copia que vivía en `asesorias` usaba la convención vieja y estaba mal.
5. **`GET /api/academico/periodo-vigente/`** devuelve el detalle del periodo cuya clave coincide con la heurística, o 404 si la SAE todavía no lo dio de alta. El frontend conserva su propia copia de la heurística para etiquetar sin pegarle a la red, y consulta el endpoint solo para fechas y ventanas.
6. **La oferta se acota al semestre vigente y al asesor activo.** `OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` filtran por `registro__semestre == semestre_vigente()` y `registro__asesor__activo=True`, además de `Disponibilidad.activa`.
7. **Autoservicio de asesor.** Un `PerfilAcademico` sin `PerfilAsesorAcademico` puede solicitarlo eligiendo área. La activación depende de un servicio externo de vigencia de académicos cuyo contrato no está definido: se aísla en `validar_academico_activo(numero_trabajador) -> bool`, con un stub que devuelve `False` (el perfil nace `activo=False` y la SAE lo activa en el admin). El stub es deliberadamente pesimista: nunca concede acceso operativo sin validación humana.
8. **Autoservicio de `RegistroAsesor`** del semestre vigente, permitido solo dentro de `registro_asesores_inicio..registro_asesores_fin` del periodo vigente. La gestión de un registro ya existente (materias, horario) no se restringe por esa ventana.
9. **Home sin mocks.** `services.ts` se borra. Los tiles son reales y gateados por rol; sin ningún tile aplicable se muestra una leyenda en vez de una grilla vacía.

## Consequences

- Un alumno con dos carreras es representable sin duplicar `PerfilAlumno` ni su `numero_cuenta`.
- `PerfilAlumno` deja de responder "¿cuál es su carrera?" en una sola lectura: quien lo necesite recorre `perfil.historial`.
- La SAE gana una tarea recurrente: dar de alta el `PeriodoAcademico` de cada semestre antes de que abra el registro. Sin él, `/api/academico/periodo-vigente/` da 404 y el autoservicio de registro no se ofrece.
- Un `RegistroAsesor` de un semestre pasado deja de aparecer en la oferta aunque sus disponibilidades sigan `activa=True`.
- Mientras el stub de validación externa devuelva `False`, el autoservicio reduce el trabajo de la SAE de "crear el perfil" a "activarlo" — no lo elimina.
- Los nueve servicios mock desaparecen de la vista del usuario sin nada que los reemplace: la Home de un usuario sin rol queda con una leyenda.

## Alternatives considered

- **Conservar `PerfilAlumno.carrera` como "carrera principal" junto al historial**: rechazado — dos fuentes de verdad para el mismo dato, y ninguna regla no arbitraria para elegir la principal cuando hay dos carreras simultáneas.
- **Derivar el semestre vigente solo de `PeriodoAcademico` (buscar el periodo que contiene hoy)**: rechazado como fuente primaria — dejaría al sistema sin semestre en cuanto la SAE olvide dar de alta un periodo, y rompería `RegistroAsesor` y el historial, que solo necesitan la clave. La heurística siempre responde; el modelo aporta las fechas.
- **Un endpoint que devuelva la clave del semestre para que el frontend no la calcule**: rechazado — obligaría a una llamada de red para dibujar una etiqueta, y a un estado de carga en pantallas que hoy son síncronas.
- **Activar el `PerfilAsesorAcademico` en cuanto se solicita, y validar después**: rechazado — un académico no vigente podría publicar disponibilidad y recibir alumnos antes de la validación.
- **Reemplazar los nueve mocks por tiles deshabilitados "próximamente"**: rechazado — anuncia fechas que nadie se comprometió a cumplir.
