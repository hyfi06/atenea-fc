from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# El TLS lo termina Cloudflare; el nginx central sirve HTTP y propaga el esquema
# original en X-Forwarded-Proto (ver runbook de despliegue). Sin este header,
# SECURE_SSL_REDIRECT ve "http" en cada request tras el proxy y entra en un loop
# de redirección 301. Confiar en X-Forwarded-Proto es seguro únicamente porque el
# backend nunca se expone directo a internet — solo lo alcanza el nginx interno.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Origins de confianza para CSRF (POST del admin/allauth con cookie de sesión).
# Default al dominio de prod; override por env para otros entornos.
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS", default=["https://atenea.unam.dev"]
)

# ADR 0018: en prod, dj-rest-auth entrega el JWT como cookie httpOnly en vez
# de en el body — el frontend nunca lo lee ni lo guarda en JS.
#
# JWT_AUTH_COOKIE/JWT_AUTH_REFRESH_COOKIE son los nombres de cookie que
# dj-rest-auth requiere para efectivamente llamar a response.set_cookie(...)
# (sin nombre, JWT_AUTH_HTTPONLY=True no tiene ningún efecto observable).
# No son secretos, por eso van hardcodeados aquí y no como variable de entorno.
#
# JWT_AUTH_SAMESITE se fija explícitamente (en vez de dejarlo en el default
# de la librería) porque la evaluación de riesgo CSRF de la deuda técnica
# 0009 depende de este valor exacto — que quede pinneado aquí evita que un
# upgrade de dj-rest-auth o un override futuro lo cambie en silencio.
REST_AUTH = {
    **REST_AUTH,
    "JWT_AUTH_HTTPONLY": True,
    "JWT_AUTH_COOKIE": "atenea-access-token",
    "JWT_AUTH_REFRESH_COOKIE": "atenea-refresh-token",
    "JWT_AUTH_SECURE": True,
    "JWT_AUTH_SAMESITE": "Lax",
    # Cierra la deuda 0009 (explotada en el pentest de staging, 2026-08-18):
    # toda escritura autenticada por cookie exige además el header X-CSRFToken.
    # SameSite=Lax no bastaba: se evalúa sobre el dominio registrable, así que
    # un subdominio hermano sigue siendo "same-site" y podía postear con la
    # cookie. Solo en prod: en dev el JWT viaja en el header Authorization y
    # JWTCookieAuthentication nunca llega a enforce_csrf.
    "JWT_AUTH_COOKIE_USE_CSRF": True,
}
# CORS_ALLOW_CREDENTIALS ahora vive en base.py (aplica igual en dev y prod).

# Fail-fast: sin credenciales de Google configuradas, mejor no arrancar que
# dejar el login de Google roto en silencio (ver ADR 0018).
SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"] = env("GOOGLE_OAUTH_CLIENT_ID")
SOCIALACCOUNT_PROVIDERS["google"]["APP"]["secret"] = env("GOOGLE_OAUTH_CLIENT_SECRET")
