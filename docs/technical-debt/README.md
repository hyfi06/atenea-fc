# Deuda técnica

Registro vivo de decisiones "suficientes por ahora" — simplificaciones deliberadas, tomadas conscientemente para no bloquear una entrega, que alguien debería revisar si el supuesto que las sostiene deja de cumplirse. No es un backlog de features: es la lista de "esto es más frágil de lo que parece, y así es por qué".

Cada ítem es un archivo numerado consecutivamente (`NNNN-titulo.md`, secuencia propia de esta carpeta, no compartida con `docs/decisions/`), con el mismo espíritu que un ADR: nace referenciado desde el ADR o spec que lo originó, y no se borra al resolverse — su `Estado` cambia a `Resuelta` y queda como registro histórico.

El formato estándar de cada archivo está documentado en [`CLAUDE.md`](../../CLAUDE.md) (sección "Documentando deuda técnica").

## Índice

### Activa

- [0001 — Sin modelo de calendario/periodo académico real](0001-sin-modelo-calendario-academico.md)
- [0002 — Alta de `PerfilAsesorAcademico` solo por admin](0002-alta-perfil-asesor-solo-admin.md)
- [0003 — Sin límites de uso en Asesorías](0003-sin-limites-uso-asesorias.md)
- [0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos](0004-sin-cierre-automatico-recordatorios.md)
- [0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas](0005-editar-disponibilidad-no-propaga.md)
- [0006 — Sin paginación en los endpoints de listado](0006-sin-paginacion-listados.md)
- [0007 — Logout no invalida el refresh token en el servidor](0007-logout-sin-invalidacion-refresh-token.md)
- [0008 — `PerfilAlumno` solo registra una carrera vigente](0008-perfil-alumno-una-sola-carrera.md)
- [0009 — Sin protección CSRF explícita en el transporte de JWT por cookie](0009-sin-csrf-en-cookie-jwt.md)

### Resuelta

_(vacío por ahora)_
