# 0019 — Home arma sus tiles en el cliente, sin catálogo de servicios en el backend

**Estado:** Activa
**Origen:** [ADR 0027](../decisions/0027-usuarios-reales-academico-autoservicio.md)

## Qué se simplificó

`Home.tsx` declara sus tiles como un arreglo literal en el propio componente y los filtra con los hooks de rol (`useEsAlumno`, `useEsAcademico`, `useEsMiembroSAE`). No hay endpoint que diga "estos son los servicios que este usuario puede usar": agregar un servicio nuevo de la SAE implica editar y desplegar el frontend.

## Por qué era razonable

Hay exactamente dos tiles y un solo servicio integrado (Asesorías). Un endpoint de catálogo con su modelo, su admin y su gating por rol sería más código que los dos tiles que sirve, y su forma correcta depende de cómo se vean los siguientes servicios — que todavía no existen. Los nueve servicios que había aquí antes eran mocks sin backend: retirarlos, no reemplazarlos, es lo que evita seguir prometiendo lo que no existe.

## Señal de revisión

Cuando se integre el segundo servicio real de la SAE, o cuando aparezca un servicio cuya visibilidad no se derive de un rol (por carrera, por generación, por convocatoria abierta). Ahí conviene el endpoint de catálogo que anticipaba el comentario original de `data/services.ts`.
