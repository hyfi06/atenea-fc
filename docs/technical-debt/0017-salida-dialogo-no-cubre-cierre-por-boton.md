# 0017 — La salida animada del diálogo modal no cubre el cierre por botón

**Estado:** Activa
**Origen:** [spec de animaciones de feedback y deleite](../superpowers/specs/2026-08-14-animaciones-feedback-deleite-frontend-design.md), ítem B3

## Qué se simplificó

`frontend/src/components/ui/dialog.tsx` intercepta `onOpenChange(false)` y difiere 150ms para que corran `.salida-dialogo`/`.salida-velo` antes de propagar el cierre real. Esa interceptación solo se dispara en las rutas que pasan por Radix: Escape y click en el velo. Los botones de acción de `Dialogo.tsx` (`BotonDialogo`, incluido el de "Volver"/"Cerrar" y cada acción de confirmación) llaman a `onCerrar`/`accion.onClick` directo, sin pasar por `DialogPrimitive.Root`, así que ese camino de cierre —el que de hecho usan los cinco diálogos de features (`DialogoCancelar`, `DialogoAgregarMateria`, `DialogoNuevoBloque`, `DialogoBloqueActivo`, `DialogoDesactivarConSesiones`) en el caso común— sigue cerrando de golpe, sin animación de salida.

Se descubrió en la revisión final de todo el branch (no en la revisión por task, que no tiene visibilidad cruzada de cómo se usa `Dialogo` en producción), después de que las 14 tasks del plan ya habían pasado su revisión individual conforme al spec tal como estaba escrito. El spec no distinguía "cierre por Radix" de "cierre por botón" al describir B3.

## Por qué era razonable

Corregirlo implica cambiar cómo `Dialogo.tsx` invoca el cierre (enrutar `accionSalir`/las acciones de confirmación a través de `DialogPrimitive.Root` en vez de llamar `onCerrar` directo), lo cual toca el contrato de cierre de los cinco diálogos de features y su testing — un cambio de mayor alcance que las 14 tasks ya ejecutadas, y fuera de lo que el plan original cubría. El plan de esta feature dice explícitamente "sin ADR ni ítem de deuda nuevos"; esta excepción se decide en la revisión final porque el hallazgo es real y no estaba previsto por el spec, no porque se reabra esa decisión de alcance para el resto del plan.

## Señal de revisión

Si la salida animada del diálogo se vuelve un requisito de producto explícito (no solo "se ve bien cuando cierra con Escape"), enrutar el cierre por botón a través de `onOpenChange` en `Dialogo.tsx`, con tests que cubran los cinco diálogos de features.
