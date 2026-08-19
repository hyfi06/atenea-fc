from datetime import timedelta
from pathlib import Path

import environ
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")

AUTH_USER_MODEL = "accounts.User"

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_ADAPTER = "accounts.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"

SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID", default=""),
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET", default=""),
            "key": "",
        },
    },
}

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "dj_rest_auth",
]

LOCAL_APPS = [
    "accounts",
    "academico",
    "carreras",
    "materias",
    "asesorias",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve los estáticos (admin/DRF) desde el propio contenedor, justo
    # debajo de SecurityMiddleware como exige su documentación. Evita depender del
    # nginx central para servir /static/ y funciona igual en dev y prod.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Backend de estáticos seleccionable por env. Default: WhiteNoise con manifest
# comprimido (hashea nombres + gzip/brotli, ideal detrás del CDN de Cloudflare).
# El valor "s3" queda como gancho documentado para servir media/estáticos desde
# MinIO/S3 a futuro — requiere django-storages y está fuera de alcance por ahora.
_STATIC_BACKENDS = {
    "whitenoise": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    "django": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": _STATIC_BACKENDS[env("DJANGO_STATIC_BACKEND", default="whitenoise")],
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # ScopedRateThrottle solo actúa sobre vistas que declaran throttle_scope
    # (allow_request retorna True de inmediato si la vista no lo tiene). Las
    # vistas de dj-rest-auth ya traen throttle_scope = "dj_rest_auth" de
    # fábrica; el resto de la API (asesorias, materias, carreras, academico)
    # no lo declara y queda sin límite. Hallazgo H3 del pentest 2026-08-18.
    "DEFAULT_THROTTLE_CLASSES": [
        "accounts.throttling.CloudflareScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "dj_rest_auth": "5/min",
    },
    # JWTCookieAuthentication extiende JWTAuthentication: revisa el header
    # Authorization primero (así es como sigue funcionando dev sin cambios) y
    # cae a la cookie JWT_AUTH_COOKIE solo si no hay header — necesario para
    # que el flujo de cookie httpOnly de prod (ADR 0018) autentique requests.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ],
}

REST_AUTH = {
    "TOKEN_MODEL": None,
    "USE_JWT": True,
    "SESSION_LOGIN": False,
    "JWT_AUTH_HTTPONLY": False,
    "PASSWORD_RESET_SERIALIZER": "accounts.serializers.PasswordResetSerializer",
    # Deuda técnica 0010: el payload default de dj-rest-auth solo trae
    # {pk, email, first_name}; el SPA necesita perfil/rol para decidir qué
    # renderizar sin sondear un endpoint por cada rol.
    "USER_DETAILS_SERIALIZER": "accounts.serializers.UserDetailsSerializer",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
}

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@atenea.ciencias.unam.mx")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

CORS_ALLOWED_ORIGINS = [FRONTEND_URL]

# Directorio público de la Facultad de Ciencias, usado por
# asesorias.validacion_externa para confirmar la vigencia de un académico
# (ADR 0027 decisión 7, Task 13). No es un servicio con contrato propio ni
# credenciales, pero la URL no se hardcodea ni se versiona: sin este valor
# configurado, validar_academico_activo() no intenta la validación y deja el
# perfil pendiente de revisión de la SAE (nunca bloquea la solicitud).
DIRECTORIO_FC_URL_BASE = env("DIRECTORIO_FC_URL_BASE", default="")
# CORS_ALLOWED_ORIGINS ya restringe a un único origin exacto (sin wildcard),
# así que habilitar credenciales es seguro también en dev — y necesario:
# frontend/src/api/client.ts manda `credentials: 'include'` de forma uniforme
# en dev y prod (ADR 0018), y sin este flag el navegador descarta toda
# respuesta cross-origin credenciada como error de red.
CORS_ALLOW_CREDENTIALS = True

# Cache compartido entre workers de gunicorn (varios procesos, ver
# docker-entrypoint.sh). Sin esto, DEFAULT_THROTTLE_CLASSES cae a LocMemCache
# (por proceso) y el límite real depende de cuántos workers atienden la
# request — hallazgo del review final del branch de fixes de seguridad,
# 2026-08-19. Redis ya es dependencia dura (Celery), no agrega infraestructura.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_ALWAYS_EAGER = "test" in sys.argv
CELERY_TASK_EAGER_PROPAGATES = True
