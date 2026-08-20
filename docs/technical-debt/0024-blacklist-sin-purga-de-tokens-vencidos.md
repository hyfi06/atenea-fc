# 0024 — Las tablas del blacklist de tokens crecen sin purga

**Estado:** Activa
**Origen:** [ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md)

## Qué se simplificó

Con `rest_framework_simplejwt.token_blacklist` instalado, cada login escribe una fila en `OutstandingToken` y cada logout una en `BlacklistedToken`. `simplejwt` trae el comando `flushexpiredtokens` para borrar las que ya expiraron, pero no está agendado: no hay ninguna tarea periódica en `celery-beat` que lo corra.

## Por qué era razonable

El proyecto todavía no tiene ningún `beat_schedule` definido (`celery-beat` corre sin tareas periódicas propias), así que agendar esto implicaba estrenar esa infraestructura por una tabla que, con el volumen actual —la SAE de una facultad, refresh de 7 días—, crece del orden de unas pocas filas por usuario y semana. Es medible y reversible en cualquier momento.

## Señal de revisión

Cuando se agende la primera tarea periódica real en `celery-beat` (el cierre automático de sesiones vencidas de la [deuda 0004](0004-sin-cierre-automatico-recordatorios.md) es la candidata natural): agregar `flushexpiredtokens` diario en el mismo commit. Antes de eso, si `token_blacklist_outstandingtoken` pasa de unos cuantos cientos de miles de filas.
