# 0012 — Oferta/asesores/búsqueda no acotan por semestre vigente

**Estado:** Resuelta — 2026-08-15 ([ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md))
**Origen:** [spec `2026-08-08-asesorias-alumno-api-design`](../decisions/0021-asesorias-alumno-api.md) / [ADR 0021](../decisions/0021-asesorias-alumno-api.md)

## Qué se simplificó

`OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` derivan la oferta que ve el alumno de `Disponibilidad.activa` sin filtrar por el semestre vigente, aunque la spec habla del "semestre vigente". Un `RegistroAsesor` de un semestre pasado cuyas `Disponibilidad` quedaron con `activa=True` sigue apareciendo en la oferta, en la lista de asesores y en la búsqueda de horarios — y, por lo tanto, sigue siendo agendable.

## Por qué era razonable

No existe una fuente de verdad del semestre vigente: es justamente la deuda [0001](0001-sin-modelo-calendario-academico.md) (sin modelo de calendario/periodo académico real). Sin ese modelo, la única forma de acotar sería hardcodear una clave de semestre, lo que sería más frágil y más difícil de mantener que derivar de `activa`: quedaría desactualizado en silencio en cada cambio de periodo. Mientras el asesor mantenga sus disponibilidades al día (desactivando las de semestres cerrados), la oferta refleja lo agendable.

## Señal de revisión

Cuando exista el modelo de calendario académico (deuda [0001](0001-sin-modelo-calendario-academico.md)), acotar estas tres vistas al periodo vigente en lugar de depender únicamente de `Disponibilidad.activa`.

## Cómo se resolvió

`OfertaView`, `AsesoresDeMateriaView` y `BuscarDisponibilidadView` filtran por `registro__semestre == semestre_vigente()` y `registro__asesor__activo=True`, además de `Disponibilidad.activa`. La fuente del semestre vigente es `academico.servicios.semestre_vigente`.
