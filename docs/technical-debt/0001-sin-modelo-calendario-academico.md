# 0001 — Sin modelo de calendario/periodo académico real

**Estado:** Activa
**Origen:** [ADR 0015](../decisions/0015-catalogo-academico.md), [ADR 0016](../decisions/0016-asesorias-academicas.md), [ADR 0017](../decisions/0017-asesorias-academicas-api.md)

## Qué se simplificó

Ni `materias.OfertaMateria` ni `asesorias` modelan fechas concretas de inicio/fin de semestre — el semestre es un `CharField` (`AAAAN`) sin fechas asociadas. La ventana de fechas agendables en Asesorías Académicas (ver ADR 0017) es una regla fija en código (semana en curso + siguiente), no derivada de un periodo real.

## Por qué era razonable

No hay todavía un segundo servicio de la SAE que necesite fechas reales de semestre; modelar un calendario completo antes de tener un segundo consumidor es especular sobre requisitos no confirmados.

## Señal de revisión

En cuanto un segundo servicio (o Asesorías mismo) necesite saber "¿estamos en periodo de exámenes?" o alinear la ventana agendable al calendario escolar real, hace falta un modelo `PeriodoAcademico` con fechas.
