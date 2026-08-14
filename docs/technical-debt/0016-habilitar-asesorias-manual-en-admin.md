# 0016 — `Materia.habilitada_asesorias` se cura manualmente en el admin

**Estado:** Activa
**Origen:** [ADR 0015](../decisions/0015-catalogo-academico.md)

## Qué se simplificó

Qué materias quedan habilitadas para Asesorías no viene del CSV de carga del catálogo (`cargar_materias`, que solo trae `Carrera,Clave,Materia,Nivel,Plan`) ni de ninguna regla codificada: es un criterio que define la SAE por convocatoria (qué materias entran ese semestre según los requisitos que ellos mismos fijan), y se aplica a mano seleccionando materias en el admin de Django y corriendo una acción batch (`habilitar_asesorias` / `deshabilitar_asesorias` en `MateriaAdmin`). Toda carga nueva del catálogo entra con `habilitada_asesorias=False` por default y depende de esa curación posterior.

## Por qué era razonable

El criterio de habilitación cambia por convocatoria y lo decide la SAE, no es un dato estructural del catálogo académico — no hay una regla estable que codificar todavía. Una acción batch en el admin (en vez de una columna en el CSV) permite que cualquier miembro de la SAE con acceso al admin la opere, no solo quien puede generar el CSV.

## Señal de revisión

Si aparece un criterio estable y repetible entre convocatorias (ej. "todas las materias de nivel ≤ N de tal carrera"), o si el volumen de materias a curar por semestre crece lo suficiente para que la selección manual en el admin sea un cuello de botella.
