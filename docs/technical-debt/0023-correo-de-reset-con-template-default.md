# 0023 — El correo de recuperación usa el template default de allauth

**Estado:** Activa
**Origen:** [ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md)

## Qué se simplificó

El correo que recibe quien pide recuperar su contraseña se arma con el template default de allauth (`account/email/password_reset_key*`), sin branding de la SAE, sin remitente con nombre propio y con la redacción genérica de la librería. Lo único que este proyecto sobreescribe es la URL del enlace (`atenea_password_reset_url_generator`, en `accounts/serializers.py`), para que apunte al SPA y no a una vista de Django que no existe.

## Por qué era razonable

Nadie pidió contenido de correo, y personalizarlo obliga a decidir tono, firma y qué hacer con el resto de los correos transaccionales que ya manda Atenea (notificaciones de asesorías) — es una iteración de contenido, no un bloqueante del flujo. El mensaje default es funcional y ya sale en español (`LANGUAGE_CODE = "es-mx"`).

## Señal de revisión

Que la SAE pida branding en los correos, que un usuario reporte el correo como confuso o sospechoso de phishing, o que se agregue un segundo correo transaccional de cuenta (verificación, bienvenida) y convenga fijar un template base compartido.
