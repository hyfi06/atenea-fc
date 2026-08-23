# 0025 — El endpoint de resincronización de `Disponibilidad` no tiene botón en el SPA

**Estado:** Activa
**Origen:** [ADR 0030](../decisions/0030-limites-cierre-y-propagacion-asesorias.md)

## Qué se simplificó

`POST /api/asesorias/disponibilidades/{id}/resincronizar/` (Task 4 del plan de límites y propagación) ya propaga formato/ubicación/liga_virtual del bloque a sus sesiones futuras y notifica a los alumnos afectados — pero ningún botón del SPA lo dispara. El asesor puede corregir un dato de su `Disponibilidad` desde "Mi horario" (`useActualizarDisponibilidad`), pero esa corrección sigue sin llegar a las sesiones ya agendadas hasta que alguien llame al endpoint a mano — el síntoma original de la deuda 0005 sigue siendo la experiencia real del asesor en el producto.

## Por qué era razonable

El alcance de ese plan (ver sus Global Constraints) fijó "Tasks 1–5: 100% backend" para las deudas 0003/0005; exponer el botón en el SPA no estaba en ese alcance, y el backend correcto y probado era la parte que más urgía cerrar — bloquea cualquier UI futura que quiera ofrecerlo.

## Señal de revisión

Un asesor reporta o se observa que corrige un dato de su horario y las sesiones ya agendadas no se actualizan — evidencia de que el hueco en el SPA le está costando tiempo real (contactar alumnos manualmente, etc.).
