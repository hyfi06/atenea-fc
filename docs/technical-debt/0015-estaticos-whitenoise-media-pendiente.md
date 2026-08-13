# 0015 — Estáticos por WhiteNoise; media en MinIO/S3 pendiente

**Estado:** Activa
**Origen:** [ADR 0025](../decisions/0025-despliegue-produccion-ghcr.md)

## Qué se simplificó

Los archivos estáticos (admin de Django, DRF) se sirven con **WhiteNoise** desde el
propio contenedor del backend (`CompressedManifestStaticFilesStorage`, `collectstatic`
en build). El stack `services/` ya tiene un MinIO desplegado (`outline-storage`), pero
**no se integra** para servir estáticos ni media. `config/settings/base.py` deja el
backend de estáticos seleccionable por env (`DJANGO_STATIC_BACKEND`, default
`whitenoise`; el valor `s3` es solo un gancho documentado, no cableado — no se instaló
`django-storages`). Atenea hoy no tiene subidas de archivos de usuario (media), así que
tampoco hay almacenamiento de media configurado.

## Por qué era razonable

Para estáticos, MinIO/S3 no aporta valor de escalamiento: son pocos archivos,
inmutables, con nombres hasheados y `Cache-Control` far-future, y **Cloudflare ya los
cachea en el edge**. WhiteNoise los sirve precomprimidos sin depender del nginx central
y funciona igual en dev y prod. Integrarlos a MinIO exigiría `django-storages`, subir el
bundle al bucket en cada deploy y gestionar política de lectura/CORS del bucket —
complejidad sin beneficio. El lugar donde MinIO sí importa es la **media** (adjuntos de
trámites, PDFs generados), que este pase no necesita porque la app aún no acepta uploads.

## Señal de revisión

Cuando se agregue la primera feature con **subida de archivos de usuario** (p. ej. los
`TramiteArchivo` de la arquitectura SAE): integrar `django-storages` + MinIO para media
(bucket propio de Atenea, claves en env), y evaluar si conviene mover también los
estáticos al mismo bucket detrás de Cloudflare. El gancho `DJANGO_STATIC_BACKEND=s3`
queda listo para ese momento.
