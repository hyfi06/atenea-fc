from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ADR 0018: en prod, dj-rest-auth entrega el JWT como cookie httpOnly en vez
# de en el body — el frontend nunca lo lee ni lo guarda en JS.
#
# JWT_AUTH_COOKIE/JWT_AUTH_REFRESH_COOKIE son los nombres de cookie que
# dj-rest-auth requiere para efectivamente llamar a response.set_cookie(...)
# (sin nombre, JWT_AUTH_HTTPONLY=True no tiene ningún efecto observable).
# No son secretos, por eso van hardcodeados aquí y no como variable de entorno.
REST_AUTH = {
    **REST_AUTH,
    "JWT_AUTH_HTTPONLY": True,
    "JWT_AUTH_COOKIE": "atenea-access-token",
    "JWT_AUTH_REFRESH_COOKIE": "atenea-refresh-token",
    "JWT_AUTH_SECURE": True,
}
CORS_ALLOW_CREDENTIALS = True

# Fail-fast: sin credenciales de Google configuradas, mejor no arrancar que
# dejar el login de Google roto en silencio (ver ADR 0018).
SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"] = env("GOOGLE_OAUTH_CLIENT_ID")
SOCIALACCOUNT_PROVIDERS["google"]["APP"]["secret"] = env("GOOGLE_OAUTH_CLIENT_SECRET")
