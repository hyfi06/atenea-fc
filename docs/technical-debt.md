# Deuda técnica

Registro vivo de decisiones "suficientes por ahora" — simplificaciones deliberadas, tomadas conscientemente para no bloquear una entrega, que alguien debería revisar si el supuesto que las sostiene deja de cumplirse. No es un backlog de features: es la lista de "esto es más frágil de lo que parece, y así es por qué".

Cada ítem nace en un ADR o spec concreto y se referencia desde ahí. Cuando un ítem se resuelve, se mueve a "Resuelta" con la fecha y el commit/ADR que lo cerró, en vez de borrarse.

## Cómo usar este documento

- Al tomar una decisión de diseño que deja algo pendiente a propósito, agrégalo aquí con una entrada nueva, no solo en la sección "Alternatives considered" del ADR — el ADR explica la decisión puntual, este documento la hace buscable junto con toda la demás deuda del proyecto.
- Cada entrada: **qué se simplificó**, **por qué fue razonable en su momento**, **la señal que indicaría que ya no lo es**, y **origen** (ADR/spec).

## Activa

### Sin modelo de calendario/periodo académico real

Ni `materias.OfertaMateria` ni `asesorias` modelan fechas concretas de inicio/fin de semestre — el semestre es un `CharField` (`AAAAN`) sin fechas asociadas. La ventana de fechas agendables en Asesorías Académicas (ver ADR 0017) es una regla fija en código (semana en curso + siguiente), no derivada de un periodo real.

**Por qué era razonable:** no hay todavía un segundo servicio de la SAE que necesite fechas reales de semestre; modelar un calendario completo antes de tener un segundo consumidor es especular sobre requisitos no confirmados.

**Señal de revisión:** en cuanto un segundo servicio (o Asesorías mismo) necesite saber "¿estamos en periodo de exámenes?" o alinear la ventana agendable al calendario escolar real, hace falta un modelo `PeriodoAcademico` con fechas.

**Origen:** [ADR 0015](decisions/0015-catalogo-academico.md), [ADR 0016](decisions/0016-asesorias-academicas.md), [ADR 0017](decisions/0017-asesorias-academicas-api.md).

### Alta de `PerfilAsesorAcademico` solo por admin

No existe endpoint ni flujo self-service para que un académico se registre como asesor — lo da de alta la SAE manualmente vía Django admin. El área queda fija tras la creación, sin flujo de edición propio.

**Por qué era razonable:** el volumen esperado de asesores es bajo (altas ocasionales, gestionadas por la SAE), y automatizarlo antes de validar el flujo con usuarios reales es prematuro.

**Señal de revisión:** si el volumen de altas crece lo suficiente para volverse un cuello de botella operativo para la SAE, o si academia pide autoservicio.

**Origen:** [ADR 0016](decisions/0016-asesorias-academicas.md), [ADR 0017](decisions/0017-asesorias-academicas-api.md).

### Sin límites de uso en Asesorías (sesiones simultáneas, cancelaciones, ventana mínima)

Un alumno puede agendar cualquier número de sesiones simultáneas y cancelar sin restricción de tiempo mínimo antes de la sesión ni límite de cancelaciones.

**Por qué era razonable:** el MVP prioriza validar el flujo completo con usuarios reales antes de diseñar límites que podrían no corresponder al patrón de abuso real (si lo hay).

**Señal de revisión:** evidencia de abuso en producción (acaparamiento de horarios, cancelaciones sistemáticas de último minuto que dejan al asesor sin aviso).

**Origen:** [ADR 0016](decisions/0016-asesorias-academicas.md).

### Sin cierre automático de sesiones vencidas ni recordatorios periódicos

Una `Asesoria` en estado `agendada` cuya fecha ya pasó sin que el asesor marque asistencia se queda así indefinidamente — no hay tarea Celery Beat que la cierre. Tampoco hay recordatorio por email antes de la sesión, solo confirmación al agendar y notificación al cancelar.

**Por qué era razonable:** requiere Celery Beat (no solo tareas async puntuales) y una decisión de producto sobre qué hacer con una sesión "abandonada" (¿marcarla como no-asistida automáticamente? ¿dejarla pendiente?) que no estaba resuelta al diseñar el MVP.

**Señal de revisión:** cuando el volumen de sesiones "huérfanas" (agendadas, vencidas, sin marcar) sea alto en los reportes que use la SAE, o cuando se necesite el dato de asistencia agregado sin depender de que el asesor la marque manualmente.

**Origen:** [ADR 0016](decisions/0016-asesorias-academicas.md).

### Editar una `Disponibilidad` no se propaga a sesiones ya agendadas

`Asesoria` guarda un snapshot de `formato`/`ubicacion`/`liga_virtual` al momento de agendar. Si el asesor corrige un dato erróneo en la `Disponibilidad` (ej. una liga de Zoom mal escrita) después de que ya hay sesiones agendadas sobre ese bloque, la corrección no llega a esas sesiones — hay que corregirlas una por una.

**Por qué era razonable:** el snapshot es deliberado (una `Asesoria` no debe cambiar de lugar/formato retroactivamente sin que el alumno se entere), y el caso de "corregir un typo después de agendar" se juzgó infrecuente frente a la complejidad de decidir cuándo propagar y cuándo no.

**Señal de revisión:** si se vuelve un problema operativo recurrente, la opción más simple es un endpoint/acción de admin para "reemplazar el snapshot de una Asesoria agendada desde su Disponibilidad actual", no cambiar el modelo de snapshot en sí.

**Origen:** [ADR 0016](decisions/0016-asesorias-academicas.md).

### Sin paginación en los endpoints de listado

Los endpoints DRF de Fase 2 (catálogo, `RegistroAsesor`, `Disponibilidad`, `Asesoria`) no configuran paginación — devuelven la lista completa. No hay convención de paginación establecida todavía en el proyecto (`REST_FRAMEWORK` en `config/settings/base.py` no la define).

**Por qué era razonable:** el volumen esperado por usuario (asesorías de un alumno o un asesor, materias de un área) es pequeño; introducir paginación antes de tener un segundo endpoint que la necesite es prematuro, y la convención debería decidirse una vez, a nivel de proyecto, no ad-hoc por app.

**Señal de revisión:** el primer endpoint cuyo listado crezca sin límite natural (ej. historial de sesiones de un asesor con años de antigüedad) es la señal para decidir la convención de paginación del proyecto — no debería resolverse solo para ese endpoint.

**Origen:** [ADR 0017](decisions/0017-asesorias-academicas-api.md).

## Resuelta

_(vacío por ahora)_
