#!/bin/sh
# Hook de arranque de la imagen nginx (se ejecuta desde /docker-entrypoint.d/
# ANTES de que la propia imagen arranque nginx — por eso NO llama a nginx aquí).
#
# Regenera /config.js con el client id de Google tomado del entorno del deploy,
# de modo que la misma imagen prehorneada sirva para cualquier entorno sin rebuild
# (ver src/config.ts).
set -e

cat > /usr/share/nginx/html/config.js <<EOF
window.__ATENEA_CONFIG__ = { googleClientId: "${ATENEA_GOOGLE_CLIENT_ID}" };
EOF
