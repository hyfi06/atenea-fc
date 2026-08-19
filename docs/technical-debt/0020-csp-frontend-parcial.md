# 0020 — CSP del frontend con `unsafe-inline` en `style-src`, sin CSP en el backend

**Estado:** Activa
**Origen:** [spec fixes-seguridad-pentest-design §M3](../superpowers/specs/2026-08-18-fixes-seguridad-pentest-design.md) / [plan de fixes de seguridad, Task 4 y 6](../superpowers/plans/2026-08-18-fixes-seguridad-pentest.md)

## Qué se simplificó

La CSP agregada en `frontend/nginx.conf` (hallazgo M3 del pentest) tiene tres huecos deliberados:

1. `style-src` incluye `'unsafe-inline'`. Se agregó durante la verificación manual en
   navegador: el SPA usa ~20 atributos `style={{...}}` inline en React (`Home.tsx`,
   `Landing.tsx`, `features/asesorias/**`), y sin `'unsafe-inline'` el navegador los
   bloquea. `'unsafe-inline'` en `style-src` reabre el vector principal que la CSP
   busca cerrar (inyección de `<style>`/`style=` arbitrario).
2. El origin del backend (Django admin, DRF browsable API) no tiene ninguna CSP —
   la spec lo puso explícitamente fuera de alcance del pase M3.
3. `location = /config.js` en `frontend/nginx.conf` no hereda los 5 headers nuevos
   (M1+M3): nginx descarta las directivas `add_header` heredadas en cualquier
   `location` que declare las suyas propias, y ese bloque ya declara
   `Cache-Control`. De los 5, solo se pierde `X-Content-Type-Options: nosniff`
   con efecto real (CSP y HSTS en la respuesta de un script son inertes).

## Por qué era razonable

Cerrar M3 sin `'unsafe-inline'` requeriría mover ~20 estilos inline a clases o a
nonces/hashes por build — trabajo de frontend no pedido en este pase, y bloquear
el merge por eso habría dejado sin cerrar los 3 hallazgos altos (H1/H2/H3) que sí
tenían fix inmediato. El backend nunca sirve contenido para usuarios finales fuera
de `/admin/` (solo staff) y la API (JSON, sin ejecución de script del response),
así que el riesgo de no tener CSP ahí es menor que en el SPA. El caso de
`/config.js` es una limitación conocida de nginx, no una decisión de producto: se
documentó en el propio `nginx.conf` y en el plan (Task 4) para no arreglarla a
ciegas fuera del alcance revisado.

## Señal de revisión

Si se agrega XSS reflejado o cualquier vector de inyección de HTML/CSS en el SPA,
o si el admin/API empiezan a servir contenido no confiable (uploads, HTML de
terceros), priorizar: (a) mover los estilos inline a clases/CSS modules y quitar
`'unsafe-inline'` de `style-src`; (b) agregar CSP al origin del backend; (c) mover
`Cache-Control` de `location = /config.js` al bloque `server` con `map`/`if` en vez
de un `location` propio, para que herede los 5 headers.
