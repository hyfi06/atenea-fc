# Deuda técnica

Registro vivo de decisiones "suficientes por ahora" — simplificaciones deliberadas, tomadas conscientemente para no bloquear una entrega, que alguien debería revisar si el supuesto que las sostiene deja de cumplirse. No es un backlog de features: es la lista de "esto es más frágil de lo que parece, y así es por qué".

Cada ítem es un archivo numerado consecutivamente (`NNNN-titulo.md`, secuencia propia de esta carpeta, no compartida con `docs/decisions/`), con el mismo espíritu que un ADR: nace referenciado desde el ADR o spec que lo originó, y no se borra al resolverse — su `Estado` cambia a `Resuelta` y queda como registro histórico.

El formato estándar de cada archivo está documentado en [`CLAUDE.md`](../../CLAUDE.md) (sección "Documentando deuda técnica").

## Índice

### Activa

- [0001 — Sin modelo de calendario/periodo académico real](0001-sin-modelo-calendario-academico.md)
- [0003 — Sin límites de uso en Asesorías](0003-sin-limites-uso-asesorias.md)
- [0004 — Sin cierre automático de sesiones vencidas ni recordatorios periódicos](0004-sin-cierre-automatico-recordatorios.md)
- [0005 — Editar una `Disponibilidad` no se propaga a sesiones ya agendadas](0005-editar-disponibilidad-no-propaga.md)
- [0006 — Sin paginación en los endpoints de listado](0006-sin-paginacion-listados.md)
- [0007 — Logout no invalida el refresh token en el servidor](0007-logout-sin-invalidacion-refresh-token.md)
- [0009 — Sin protección CSRF explícita en el transporte de JWT por cookie](0009-sin-csrf-en-cookie-jwt.md)
- [0014 — Alta de `PerfilSAE` solo por admin](0014-alta-perfil-sae-solo-admin.md)
- [0015 — Estáticos por WhiteNoise; media en MinIO/S3 pendiente](0015-estaticos-whitenoise-media-pendiente.md)
- [0016 — `Materia.habilitada_asesorias` se cura manualmente en el admin](0016-habilitar-asesorias-manual-en-admin.md)
- [0017 — La salida animada del diálogo modal no cubre el cierre por botón](0017-salida-dialogo-no-cubre-cierre-por-boton.md)
- [0018 — La vigencia del académico no se valida: `validar_academico_activo` es un stub](0018-validacion-academico-activo-con-stub.md)
- [0019 — Home arma sus tiles en el cliente, sin catálogo de servicios en el backend](0019-home-sin-catalogo-de-servicios.md)

### Resuelta

- [0010 — API no expone perfil ni rol del usuario autenticado](0010-api-no-expone-perfil-usuario-autenticado.md) — resuelta 2026-08-04
- [0011 — Un usuario con doble rol (alumno y asesor) solo ve el lado de alumno](0011-doble-rol-alumno-asesor-solo-ve-alumno.md) — resuelta 2026-08-08
- [0002 — Alta de `PerfilAsesorAcademico` solo por admin](0002-alta-perfil-asesor-solo-admin.md) — resuelta 2026-08-15
- [0008 — `PerfilAlumno` solo registra una carrera vigente](0008-perfil-alumno-una-sola-carrera.md) — resuelta 2026-08-15
- [0012 — Oferta/asesores/búsqueda no acotan por semestre vigente](0012-oferta-asesorias-sin-scope-de-semestre.md) — resuelta 2026-08-15
- [0013 — Agendar no valida que la materia pertenezca al registro del asesor](0013-agendar-sin-validar-materia-del-registro.md) — resuelta 2026-08-18
