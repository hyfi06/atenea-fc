# 0021 — Envío de correo depende de una cuenta de Workspace dedicada y su app password

**Estado:** Activa
**Origen:** [ADR 0028](../decisions/0028-envio-correo-smtp-cuenta-dedicada.md)

## Qué se simplificó

En vez de pedir a un admin del Workspace institucional que habilite el SMTP
relay de Google (sin autenticación, sin límite de 2000 msj/día, configurado por
IP), el envío de correo de Atenea se autentica como una cuenta de Workspace
dedicada (`EMAIL_HOST_USER`) usando una contraseña de aplicación
(`EMAIL_HOST_PASSWORD`) contra `smtp.gmail.com`.

## Por qué era razonable

No hay acceso de administrador al Workspace disponible hoy, y esperar a
tramitarlo habría bloqueado el envío de correo real indefinidamente. La cuenta
dedicada + app password no requiere permisos especiales — solo que las
contraseñas de aplicación no estén deshabilitadas a nivel organización — y deja
un camino de migración a la opción sin deuda (SMTP relay) que no toca código,
solo variables de entorno.

## Señal de revisión

Revisar/migrar a SMTP relay si:

- El volumen de correo se acerca al límite de ~2000 mensajes/día de una cuenta
  individual de Gmail, o Google empieza a marcar los envíos como sospechosos
  por volumen/ritmo.
- Se obtiene acceso de administrador al Workspace institucional (o alguien con
  ese acceso puede hacer el alta puntual).
- La cuenta dedicada requiere rotación de contraseña de aplicación y se vuelve
  una fricción operativa recurrente.
