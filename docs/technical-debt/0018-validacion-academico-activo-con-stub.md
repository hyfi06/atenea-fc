# 0018 — La vigencia del académico no se valida: `validar_academico_activo` es un stub

**Estado:** Activa
**Origen:** [ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md)

## Qué se simplificó

`asesorias/validacion_externa.py::validar_academico_activo(numero_trabajador)` devuelve siempre `False`. El servicio externo que responde si un número de trabajador corresponde a un académico vigente existe, pero su contrato (endpoint, autenticación, forma de la respuesta) no está definido todavía. En consecuencia, todo `PerfilAsesorAcademico` creado por autoservicio nace con `activo=False` y necesita que la SAE lo active a mano desde el admin de Django.

## Por qué era razonable

El autoservicio ya elimina la mitad del trabajo manual (la SAE deja de crear el perfil y de capturar el área; solo revisa y activa), y el stub es la variante segura: con `True` un académico sin nombramiento vigente podría publicar disponibilidad y recibir alumnos sin que nadie lo revisara. Aislar la pregunta en una sola función deja la integración real como un cambio de una función, no del flujo.

## Señal de revisión

En cuanto se defina el contrato del servicio externo. El cambio es reescribir el cuerpo de `validar_academico_activo` (y agregar sus variables de entorno); ni la vista ni el modelo deberían tener que tocarse. Revisar también qué hacer ante caída del servicio: hoy no hay decisión tomada.
