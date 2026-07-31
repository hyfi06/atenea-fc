# 0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas

**Estado:** Activa
**Origen:** [ADR 0016](../decisions/0016-asesorias-academicas.md)

## Qué se simplificó

`Asesoria` guarda un snapshot de `formato`/`ubicacion`/`liga_virtual` al momento de agendar. Si el asesor corrige un dato erróneo en la `Disponibilidad` (ej. una liga de Zoom mal escrita) después de que ya hay sesiones agendadas sobre ese bloque, la corrección no llega a esas sesiones — hay que corregirlas una por una.

## Por qué era razonable

El snapshot es deliberado (una `Asesoria` no debe cambiar de lugar/formato retroactivamente sin que el alumno se entere), y el caso de "corregir un typo después de agendar" se juzgó infrecuente frente a la complejidad de decidir cuándo propagar y cuándo no.

## Señal de revisión

Si se vuelve un problema operativo recurrente, la opción más simple es un endpoint/acción de admin para "reemplazar el snapshot de una Asesoria agendada desde su Disponibilidad actual", no cambiar el modelo de snapshot en sí.
