// Configuración inyectada en runtime.
//
// En producción, el entrypoint del contenedor del frontend escribe `/config.js`
// con el client id de Google tomado de una variable de entorno del deploy
// (`ATENEA_GOOGLE_CLIENT_ID` en `services/.env`; ver
// docs/development/despliegue-produccion.md). Así la MISMA imagen prehorneada en
// CI sirve para cualquier entorno sin rebuild, y el client id no vive en el CI.
//
// En dev no hay `/config.js` con valor real (el `public/config.js` va vacío), así
// que cae al valor horneado por Vite en build desde `.env`.
interface AteneaRuntimeConfig {
  googleClientId?: string
}

declare global {
  interface Window {
    __ATENEA_CONFIG__?: AteneaRuntimeConfig
  }
}

export function googleClientId(): string {
  return window.__ATENEA_CONFIG__?.googleClientId || import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID
}
