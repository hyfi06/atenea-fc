// Placeholder para dev y build. En producción, el entrypoint del contenedor lo
// sobrescribe con el client id real tomado de ATENEA_GOOGLE_CLIENT_ID.
// Vacío => src/config.ts cae al valor de Vite (.env) en dev.
window.__ATENEA_CONFIG__ = { googleClientId: '' };
