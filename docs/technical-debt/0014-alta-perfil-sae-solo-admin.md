# 0014 — Alta de `PerfilSAE` solo por admin

**Estado:** Activa
**Origen:** [ADR 0023](../decisions/0023-asesorias-sae-admin-api.md)

## Qué se simplificó

No existe endpoint ni flujo self-service para dar de alta a un miembro de la SAE — lo crea un administrador manualmente vía Django admin, creando el `PerfilSAE` OneToOne al `User`. Tampoco hay gestión desde la app (activar/desactivar, listar miembros).

## Por qué era razonable

El número de miembros de la SAE es muy bajo y estable (altas excepcionales, gestionadas internamente), y el rol es de confianza alta (acceso casi-administrador de solo lectura al servicio). Automatizar el alta antes de validar el área con usuarios reales es prematuro, y sigue exactamente el mismo criterio ya aceptado para el alta de asesores ([deuda 0002](0002-alta-perfil-asesor-solo-admin.md)).

## Señal de revisión

Si el número de miembros SAE crece lo suficiente para que el alta manual se vuelva un cuello de botella, o si se necesita gestionar altas/bajas y permisos de SAE desde la propia app (p. ej. delegar la administración fuera del equipo con acceso al Django admin).
