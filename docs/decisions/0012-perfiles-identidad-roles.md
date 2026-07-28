# 0012 — Perfiles de identidad y roles de negocio (no Django Groups)

**Status:** Accepted
**Date:** 2026-07-28

## Context

Atenea tiene varios tipos de persona con necesidades de acceso distintas: alumnos (con número de cuenta, pueden estar inscritos en más de una carrera), académicos (con número de trabajador, pueden ser asesores de servicio social y/o tutores), personas externas sin número de cuenta ni de trabajador (pueden ser asesoras de servicio social externas), un grupo reducido de revisores/aprobadores de trámites (siempre académicos, asignados a una o más carreras), y contactos de empresas en la bolsa de trabajo. Una misma persona puede acumular varios de estos roles a la vez.

El mecanismo de permisos estándar de Django (`django.contrib.auth.Group` + `Permission`) opera a nivel de modelo ("puede editar objetos de tipo X"), no a nivel de instancia — no tiene forma de cargar "sobre qué carrera" o "de qué empresa" sin una tabla de alcance aparte, duplicando el mecanismo de asignación.

## Decision

- **Identidad**: `PerfilAlumno` (`numero_cuenta`, único) y `PerfilAcademico` (`numero_trabajador`, único), ambos `OneToOneField` a `accounts.User`, no mutuamente excluyentes. Una persona "externa" es un `User` sin ninguno de los dos perfiles.
- **Roles de negocio también como perfiles**, no como Django Groups: `PerfilAsesorServicioSocial` (aplica con o sin `PerfilAcademico`), `PerfilTutor` (requiere `PerfilAcademico`), `PerfilRevisor` (requiere `PerfilAcademico`, con `carreras = ManyToManyField` para el alcance por carrera), `PerfilContactoEmpresa` (`ForeignKey` a `User` + `ForeignKey` a `Empresa`, no `OneToOne`, porque una empresa puede tener varios contactos).
- El alcance fino de cada rol (qué carrera revisa, qué empresa administra) vive como campo/relación en el mismo modelo `PerfilX`, no en una tabla de mapeo separada.
- Reglas como "Tutor y Revisor requieren `PerfilAcademico`" se validan en la lógica de la aplicación (`clean()` del modelo o el flujo que crea el perfil), no mediante constraints de Groups.
- `Empresa` es una entidad propia (no un `User`); sus contactos se vinculan vía `PerfilContactoEmpresa`.
- Comprobar "¿tiene este rol?" sigue un patrón uniforme para todo — identidad y roles por igual: `hasattr(user, "perfil_alumno")`, `hasattr(user, "perfil_revisor")`, etc.
- Django `Group` / `Permission` / `is_staff` quedan reservados exclusivamente para controlar acceso al **admin de Django** (staff interno administrando datos crudos) — un concern separado de estos roles de negocio, no resuelto por esta ADR.

Esta ADR no crea los modelos `Carrera`, `HistoriaAcademica`, `ServicioSocial`, `Empresa`, `Vacante` ni `Evento` — son de apps de dominio futuras, cada una con su propia ADR. Esta decisión solo fija el patrón que esas apps usarán para conectar sus datos a `accounts.User`.

## Consequences

- Un solo patrón (perfil = `OneToOne`/`FK` a `User` + sus propios campos/relaciones) para identidad y para roles, en vez de mezclar Groups (sin parámetros) con tablas de alcance aparte.
- Agregar un rol nuevo en el futuro es agregar un modelo `PerfilX` más siguiendo el mismo patrón — mecánico y consistente con `PerfilAlumno`/`PerfilAcademico`.
- Una sola consulta resuelve "¿tiene el rol?" y "¿sobre qué aplica?" a la vez, ej. `user.perfil_revisor.carreras.all()`.
- Los permission classes de DRF deben chequear estos perfiles explícitamente en código propio — no hay integración declarativa con `DjangoModelPermissions` ni con el admin de Django para gatear features de negocio.
- Si en el futuro aparece una necesidad genuina de permisos arbitrarios por objeto (no capturable como un perfil con relaciones fijas), esta decisión se revisita.

## Alternatives considered

- **Django Groups + Permissions puros**: rechazado — son de nivel de modelo, no de instancia; no cargan "qué carrera" o "qué empresa" sin una tabla de alcance aparte.
- **Groups para el rol + tabla relacional aparte para el alcance**: funcional (fue la primera propuesta discutida), pero son dos mecanismos para un mismo concepto cuando un solo modelo `PerfilX` ya cubre ambos (identidad del rol + alcance) en un solo lugar.
- **`django-guardian`** (permisos por objeto genéricos): resuelve un problema más general del que tenemos — el alcance real es un número pequeño y conocido de relaciones (revisor↔carrera, asesor↔servicio, contacto↔empresa), no permisos arbitrarios por objeto. Agregar esa dependencia sería complejidad sin beneficio aquí.
