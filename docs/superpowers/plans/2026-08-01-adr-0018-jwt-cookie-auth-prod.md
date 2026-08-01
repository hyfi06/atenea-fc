# ADR 0018 — Cookies JWT funcionales en producción — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar la brecha entre lo que [ADR 0018](../../decisions/0018-contrato-autenticacion-frontend-backend.md) decidió para producción (JWT como cookies `httpOnly`+`Secure`, nunca en JS) y lo que el código realmente hace hoy, para que el flujo de autenticación funcione en `docker-compose.prod.yml` sin cambios en el frontend.

**Architecture:** Dos defectos puntuales en `backend/config/settings/`, verificados empíricamente contra el código real (no solo leídos): (1) `prod.py` fija `JWT_AUTH_HTTPONLY=True` pero nunca define `JWT_AUTH_COOKIE`/`JWT_AUTH_REFRESH_COOKIE` — sin nombre de cookie, `dj-rest-auth` nunca ejecuta `response.set_cookie(...)`; (2) `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` en `base.py` usa `JWTAuthentication` (solo header `Authorization`), no `JWTCookieAuthentication` de `dj-rest-auth` (header con fallback a cookie) — así que aunque la cookie existiera, ninguna vista la leería para autenticar. Se corrigen ambos con cambios de configuración; no se toca lógica de negocio ni se agregan endpoints nuevos.

**Tech Stack:** Django 6, Django REST Framework, `dj-rest-auth` 7.x, `djangorestframework-simplejwt`, `django-allauth`.

## Global Constraints

- No se modifica el frontend (`/frontend`) — el contrato HTTP que consume no cambia, solo se hace funcional lo que ya prometía.
- No se introduce ninguna variable de entorno nueva: los nombres de cookie no son secretos, se fijan como constantes en `prod.py`, igual que el resto de las banderas de seguridad de ese archivo (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, etc.).
- El comportamiento de **dev** (`config/settings/dev.py`) no debe cambiar: login sigue devolviendo `access`/`refresh` en el body, el SPA los guarda en `localStorage` y los manda por header — esto ya está verificado como no afectado por el cambio de clase de autenticación (`JWTCookieAuthentication` da prioridad al header cuando está presente, y en dev no hay nombre de cookie configurado).
- No se instala `rest_framework_simplejwt.token_blacklist` ni se toca el comportamiento de logout respecto a invalidación server-side del refresh token — eso sigue siendo deuda técnica aceptada ([0007](../../technical-debt/0007-logout-sin-invalidacion-refresh-token.md)), fuera de alcance de este plan.
- No se activa `JWT_AUTH_COOKIE_USE_CSRF` — la ADR 0018 ya razonó explícitamente que se prefiere "el modo soportado directamente por la librería" (default sin CSRF en cookie); activarlo requeriría trabajo de frontend no pedido aquí. Se documenta como deuda técnica nueva en la Tarea 3.
- Todos los tests nuevos corren bajo `config.settings.dev` (el que usa `manage.py test`/`uv run manage.py test`) — no se cambia `DJANGO_SETTINGS_MODULE` para testear; el comportamiento de "prod" se simula parcheando el singleton `dj_rest_auth.app_settings.api_settings` (confirmado empíricamente que esto SÍ propaga a `jwt_auth.py`/`views.py`, a diferencia de `django.test.override_settings(REST_AUTH=...)`, que **no** tiene efecto porque `dj_rest_auth` no conecta su `api_settings` a la señal `setting_changed` de Django — se cachea una sola vez al importarse el módulo).

---

## File Structure

- **Modificar** `backend/config/settings/base.py` — cambia la clase de autenticación default de DRF de `JWTAuthentication` (solo header) a `dj_rest_auth.jwt_auth.JWTCookieAuthentication` (header con fallback a cookie). Afecta a **todos** los entornos (dev y prod heredan de aquí), pero es seguro para dev porque no hay nombre de cookie configurado ahí y el header sigue teniendo prioridad.
- **Modificar** `backend/config/settings/prod.py` — agrega `JWT_AUTH_COOKIE`, `JWT_AUTH_REFRESH_COOKIE`, `JWT_AUTH_SECURE` al diccionario `REST_AUTH` ya existente.
- **Modificar** `backend/accounts/tests/test_auth.py` — agrega las clases de test que prueban el mecanismo de cookies (nombre, atributos `httponly`/`secure`, autenticación solo-por-cookie, refresh solo-por-cookie, logout limpia ambas cookies) y una prueba aislada (subproceso) de que `config.settings.prod` trae los valores correctos.
- **Modificar** `docs/decisions/0018-contrato-autenticacion-frontend-backend.md` — nueva entrada de Changelog documentando el fix.
- **Modificar** `docs/development/api-frontend.md` — actualiza el callout de advertencia (⚠️) que documentaba el bug, para reflejar que ya está resuelto.
- **Crear** `docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md` — deuda técnica: no hay protección CSRF en el transporte de JWT por cookie en prod (se acepta el default de la librería, apoyado en el mismo supuesto de topología conocida que ya usa ADR 0018).
- **Modificar** `docs/technical-debt/README.md` — agrega la entrada 0009 al índice.

---

### Task 1: Cookies JWT con nombre, `httponly` y `secure` en prod

**Files:**
- Modify: `backend/config/settings/prod.py`
- Test: `backend/accounts/tests/test_auth.py`

**Interfaces:**
- Consumes: `REST_AUTH` dict ya definido en `backend/config/settings/base.py:138-144` (trae `JWT_AUTH_HTTPONLY` heredado, sobreescrito a `True` en `prod.py:15`).
- Produces: `REST_AUTH["JWT_AUTH_COOKIE"] = "atenea-access-token"`, `REST_AUTH["JWT_AUTH_REFRESH_COOKIE"] = "atenea-refresh-token"`, `REST_AUTH["JWT_AUTH_SECURE"] = True` en `prod.py` — nombres que la Tarea 2 y los tests de esta tarea usan tal cual.

- [x] **Step 1: Escribir el test de valores de settings (subproceso aislado) — RED**

Este test importa `config.settings.prod` en un proceso Python **separado** (no dentro del test runner de Django, que ya corre bajo `config.settings.dev`) para no contaminar el `SOCIALACCOUNT_PROVIDERS`/otros globals mutados por `prod.py` al importarse. Agregar al final de `backend/accounts/tests/test_auth.py`:

```python
import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


class ProdSettingsJWTCookieTests(TestCase):
    def test_prod_settings_configure_jwt_cookies(self):
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings.prod",
            "DJANGO_SECRET_KEY": "test-secret",
            "DATABASE_URL": "postgres://u:p@localhost:5432/db",
            "REDIS_URL": "redis://localhost:6379/0",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "GOOGLE_OAUTH_CLIENT_ID": "fake-id",
            "GOOGLE_OAUTH_CLIENT_SECRET": "fake-secret",
        }
        script = (
            "import django, json\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "print(json.dumps({\n"
            "    'REST_AUTH': {\n"
            "        k: settings.REST_AUTH.get(k)\n"
            "        for k in ('JWT_AUTH_HTTPONLY', 'JWT_AUTH_COOKIE', 'JWT_AUTH_REFRESH_COOKIE', 'JWT_AUTH_SECURE')\n"
            "    },\n"
            "    'AUTH_CLASSES': settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'],\n"
            "}))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)

        self.assertEqual(output["REST_AUTH"]["JWT_AUTH_HTTPONLY"], True)
        self.assertEqual(output["REST_AUTH"]["JWT_AUTH_COOKIE"], "atenea-access-token")
        self.assertEqual(output["REST_AUTH"]["JWT_AUTH_REFRESH_COOKIE"], "atenea-refresh-token")
        self.assertEqual(output["REST_AUTH"]["JWT_AUTH_SECURE"], True)
```

Agregar `from django.test import TestCase` al bloque de imports existente al inicio del archivo (junto a `from rest_framework.test import APITestCase`) si no está ya presente.

- [x] **Step 2: Correr el test y confirmar que falla**

Run: `uv run manage.py test accounts.tests.test_auth.ProdSettingsJWTCookieTests -v 2`
Expected: FAIL — `AssertionError: None != 'atenea-access-token'` (hoy `JWT_AUTH_COOKIE` no está definido en `prod.py`, así que `settings.REST_AUTH.get(...)` da `None`).

- [x] **Step 3: Agregar los valores a `prod.py`**

En `backend/config/settings/prod.py`, reemplazar:

```python
# ADR 0018: en prod, dj-rest-auth entrega el JWT como cookie httpOnly en vez
# de en el body — el frontend nunca lo lee ni lo guarda en JS.
REST_AUTH = {**REST_AUTH, "JWT_AUTH_HTTPONLY": True}
CORS_ALLOW_CREDENTIALS = True
```

por:

```python
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
```

- [x] **Step 4: Correr el test y confirmar que pasa**

Run: `uv run manage.py test accounts.tests.test_auth.ProdSettingsJWTCookieTests -v 2`
Expected: PASS

- [x] **Step 5: Escribir el test de comportamiento (cookies se setean con los atributos correctos) — RED**

Este test sí corre bajo `config.settings.dev`, pero simula la configuración de prod parcheando el singleton de `dj-rest-auth` directamente (ver "Global Constraints" — `override_settings(REST_AUTH=...)` no tiene efecto sobre este paquete). Agregar a `backend/accounts/tests/test_auth.py`:

```python
from dj_rest_auth.app_settings import api_settings as dra_settings

PROD_COOKIE_SETTINGS = dict(
    JWT_AUTH_COOKIE="atenea-access-token",
    JWT_AUTH_REFRESH_COOKIE="atenea-refresh-token",
    JWT_AUTH_SECURE=True,
    JWT_AUTH_HTTPONLY=True,
)


class CookieBasedLoginTests(APITestCase):
    def test_login_sets_httponly_secure_cookies_when_configured(self):
        user = User.objects.create_user("cookies@ciencias.unam.mx", password="ClaveSegura123!")

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            response = self.client.post(
                "/api/auth/login/",
                {"email": user.email, "password": "ClaveSegura123!"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_cookie = response.cookies["atenea-access-token"]
        refresh_cookie = response.cookies["atenea-refresh-token"]
        self.assertTrue(access_cookie["httponly"])
        self.assertTrue(access_cookie["secure"])
        self.assertTrue(refresh_cookie["httponly"])
        self.assertTrue(refresh_cookie["secure"])
        # dj-rest-auth vacía 'refresh' del body cuando JWT_AUTH_HTTPONLY=True
        self.assertEqual(response.data["refresh"], "")

    def test_logout_clears_both_cookies_when_configured(self):
        user = User.objects.create_user("cookies-logout@ciencias.unam.mx", password="ClaveSegura123!")

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            login_response = self.client.post(
                "/api/auth/login/",
                {"email": user.email, "password": "ClaveSegura123!"},
                format="json",
            )
            self.client.cookies["atenea-access-token"] = login_response.cookies["atenea-access-token"].value

            logout_response = self.client.post(
                "/api/auth/logout/",
                {},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}",
            )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.cookies["atenea-access-token"].value, "")
        self.assertEqual(logout_response.cookies["atenea-access-token"]["max-age"], 0)
        self.assertEqual(logout_response.cookies["atenea-refresh-token"].value, "")
        self.assertEqual(logout_response.cookies["atenea-refresh-token"]["max-age"], 0)
```

Agregar `from unittest.mock import patch` ya está importado (línea 2 del archivo); confirmar que sigue ahí.

- [x] **Step 6: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth.CookieBasedLoginTests -v 2`
Expected: PASS — estos dos tests **ya pasan sin tocar código de producción**, porque solo dependen de que exista *algún* nombre de cookie configurado (aquí, vía el parche). Sirven como base para la Tarea 2, que sí depende de un cambio real de código. Si fallan aquí, el problema está en el test, no en `prod.py`.

- [x] **Step 7: Commit**

```bash
git add backend/config/settings/prod.py backend/accounts/tests/test_auth.py
git commit -m "fix(backend): configurar nombres de cookie JWT y flag secure en prod"
```

---

### Task 2: Autenticar requests leyendo la cookie (no solo el header)

**Files:**
- Modify: `backend/config/settings/base.py`
- Test: `backend/accounts/tests/test_auth.py`

**Interfaces:**
- Consumes: nombres de cookie `atenea-access-token`/`atenea-refresh-token` producidos en la Tarea 1 (vía `PROD_COOKIE_SETTINGS`, ya definido en el archivo de test).
- Produces: `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = ["dj_rest_auth.jwt_auth.JWTCookieAuthentication"]` en `base.py` — clase que las Tareas futuras (y cualquier vista nueva) heredan automáticamente vía el default de DRF.

- [x] **Step 1: Escribir el test de autenticación solo-por-cookie — RED**

Agregar `from rest_framework.test import APIClient` al bloque de imports al inicio del archivo. Luego agregar los siguientes tres métodos **dentro del cuerpo de la clase `CookieBasedLoginTests` ya creada en la Tarea 1** (no crear una clase nueva ni redeclarar la existente — solo insertar estos métodos junto a los que ya tiene esa clase):

```python
    def test_cookie_alone_authenticates_protected_endpoint(self):
        user = User.objects.create_user("cookies-auth@ciencias.unam.mx", password="ClaveSegura123!")

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            login_response = self.client.post(
                "/api/auth/login/",
                {"email": user.email, "password": "ClaveSegura123!"},
                format="json",
            )

            cookie_only_client = APIClient()
            cookie_only_client.cookies["atenea-access-token"] = login_response.cookies["atenea-access-token"].value

            response = cookie_only_client.get("/api/auth/user/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)

    def test_cookie_alone_refreshes_access_token(self):
        user = User.objects.create_user("cookies-refresh@ciencias.unam.mx", password="ClaveSegura123!")

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            login_response = self.client.post(
                "/api/auth/login/",
                {"email": user.email, "password": "ClaveSegura123!"},
                format="json",
            )

            refresh_only_client = APIClient()
            refresh_only_client.cookies["atenea-refresh-token"] = login_response.cookies["atenea-refresh-token"].value

            response = refresh_only_client.post("/api/auth/token/refresh/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_header_auth_still_works_without_cookie_config(self):
        """Regresión: el flujo de dev (sin nombres de cookie configurados) no se rompe."""
        user = User.objects.create_user("header-only@ciencias.unam.mx", password="ClaveSegura123!")

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "ClaveSegura123!"},
            format="json",
        )
        response = self.client.get(
            "/api/auth/user/", HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
```

- [x] **Step 2: Correr los tests y confirmar que fallan donde corresponde**

Run: `uv run manage.py test accounts.tests.test_auth.CookieBasedLoginTests -v 2`
Expected:
- `test_cookie_alone_authenticates_protected_endpoint` → FAIL con `401` (`Las credenciales de autenticación no se proveyeron.`) — es exactamente el bug: la cookie existe pero `JWTAuthentication` (header-only) no la lee.
- `test_cookie_alone_refreshes_access_token` → PASS ya (el endpoint de refresh usa `CookieTokenRefreshSerializer`, que lee la cookie por su cuenta desde antes, independiente de `DEFAULT_AUTHENTICATION_CLASSES`) — confirma que este bug es específicamente de autenticación de vistas protegidas, no del refresh.
- `test_header_auth_still_works_without_cookie_config` → PASS ya (nada roto todavía).

- [x] **Step 3: Cambiar la clase de autenticación default**

En `backend/config/settings/base.py`, reemplazar:

```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}
```

por:

```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # JWTCookieAuthentication extiende JWTAuthentication: revisa el header
    # Authorization primero (así es como sigue funcionando dev sin cambios) y
    # cae a la cookie JWT_AUTH_COOKIE solo si no hay header — necesario para
    # que el flujo de cookie httpOnly de prod (ADR 0018) autentique requests.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ],
}
```

- [x] **Step 4: Correr los tests y confirmar que todos pasan**

Run: `uv run manage.py test accounts.tests.test_auth.CookieBasedLoginTests accounts.tests.test_auth.ProdSettingsJWTCookieTests -v 2`
Expected: PASS — los 6 tests (4 de `CookieBasedLoginTests` + `test_prod_settings_configure_jwt_cookies`).

- [x] **Step 5: Correr la suite completa del backend para descartar regresiones**

Run: `uv run manage.py test`
Expected: todos los tests existentes (incluyendo `GoogleLoginTests`, `PasswordResetLoginFlowTests`, y toda la suite de `asesorias`/`materias`/`carreras`) siguen en PASS. Presta atención en particular a cualquier test que dependa de `DEFAULT_AUTHENTICATION_CLASSES` — no debería haber ninguno acoplado a la clase exacta, solo al comportamiento (header `Authorization` funciona).

- [x] **Step 6: Verificar que el login social también setea cookies (mismo codepath)**

Agregar a la clase `GoogleLoginTests` existente en `backend/accounts/tests/test_auth.py`:

```python
    @patch.object(GoogleOAuth2Adapter, "complete_login")
    def test_sets_cookies_when_httponly_configured(self, mock_complete_login):
        user = User.objects.create_user("google-cookies@ciencias.unam.mx")
        mock_complete_login.side_effect = _complete_login_as(user.email)

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            response = self._post_google_login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("atenea-access-token", response.cookies)
        self.assertIn("atenea-refresh-token", response.cookies)
```

Esto reusa `dra_settings` y `PROD_COOKIE_SETTINGS`, definidos a nivel de módulo por la Tarea 1 (Step 5) más abajo en el archivo (después de `GoogleLoginTests`, que está al inicio). Esto no es un problema: el cuerpo de un método de test solo se ejecuta cuando el test runner lo llama, momento en el que el módulo completo ya terminó de cargarse y ambos nombres ya existen en el namespace del módulo — el orden físico de las definiciones en el archivo es irrelevante para la resolución de nombres en tiempo de ejecución.

Run: `uv run manage.py test accounts.tests.test_auth.GoogleLoginTests -v 2`
Expected: PASS — confirma que `GoogleLoginView` (que hereda `get_response()` de `LoginView`, la misma vía que ya se probó en `CookieBasedLoginTests`) también setea las cookies correctamente, sin necesitar cambios de código adicionales.

- [x] **Step 7: Commit**

```bash
git add backend/config/settings/base.py backend/accounts/tests/test_auth.py
git commit -m "fix(backend): autenticar requests contra la cookie JWT, no solo el header"
```

---

### Task 3: Documentar el fix y la deuda técnica de CSRF-en-cookie

**Files:**
- Modify: `docs/decisions/0018-contrato-autenticacion-frontend-backend.md`
- Modify: `docs/development/api-frontend.md`
- Create: `docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md`
- Modify: `docs/technical-debt/README.md`

**Interfaces:**
- Consumes: nombres de cookie y comportamiento verificado en las Tareas 1 y 2.
- Produces: nada consumido por código — son artefactos de documentación.

- [x] **Step 1: Agregar entrada de Changelog a la ADR 0018**

Al final de `docs/decisions/0018-contrato-autenticacion-frontend-backend.md`, en la sección `## Changelog` (después de la entrada del 2026-08-01 sobre eliminar el flujo Authorization Code), agregar:

```markdown
- **2026-08-01** — Se implementa en el backend el transporte de cookie httpOnly para prod descrito en la decisión 2, que hasta ahora solo estaba documentado pero no era funcional: `config/settings/prod.py` fijaba `JWT_AUTH_HTTPONLY=True` sin definir `JWT_AUTH_COOKIE`/`JWT_AUTH_REFRESH_COOKIE` (sin nombre, dj-rest-auth nunca llama a `response.set_cookie(...)`), y `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]` usaba `JWTAuthentication` (solo header) en vez de `JWTCookieAuthentication` (header con fallback a cookie), así que ninguna vista protegida podía autenticar con la cookie aunque existiera. Se corrigen ambos puntos; el comportamiento de dev no cambia. El default de la librería para CSRF en cookie (`JWT_AUTH_COOKIE_USE_CSRF=False`) se deja sin activar, tal como ya razonaba esta ADR en "Alternatives considered" — registrado explícitamente como deuda técnica en [`docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md`](../technical-debt/0009-sin-csrf-en-cookie-jwt.md).
```

- [x] **Step 2: Actualizar el callout de advertencia en la guía de frontend**

En `docs/development/api-frontend.md`, ubicar el bloque que empieza con `> ⚠️ **Discrepancia verificada en el código actual...**` (dentro de la sección "Transporte del JWT — difiere entre dev y prod") y reemplazarlo completo por:

```markdown
> **Estado (2026-08-01):** el flujo de cookies de prod ya es funcional — `config/settings/prod.py` define `JWT_AUTH_COOKIE`/`JWT_AUTH_REFRESH_COOKIE`/`JWT_AUTH_SECURE`, y `DEFAULT_AUTHENTICATION_CLASSES` usa `JWTCookieAuthentication` (lee el header si está presente, si no cae a la cookie) — verificado con tests en `accounts/tests/test_auth.py::CookieBasedLoginTests`. Un detalle a tener presente: `access` sigue apareciendo en el body JSON de `/api/auth/login/` y `/api/auth/google/` incluso con `JWT_AUTH_HTTPONLY=True` (comportamiento default de `dj-rest-auth`, no algo que este proyecto controle sin sobreescribir la vista) — el SPA en prod debe simplemente ignorar ese campo del body y depender solo de la cookie (`credentials: 'include'`), nunca leerlo ni guardarlo.
```

- [x] **Step 3: Crear el ítem de deuda técnica 0009**

Crear `docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md`:

```markdown
# 0009 — Sin protección CSRF explícita en el transporte de JWT por cookie

**Estado:** Activa
**Origen:** [ADR 0018](../decisions/0018-contrato-autenticacion-frontend-backend.md)

## Qué se simplificó

En prod, el JWT viaja como cookie `httpOnly`+`Secure` (`JWTCookieAuthentication`). La librería (`dj-rest-auth`) soporta forzar validación CSRF sobre requests autenticados por cookie vía `JWT_AUTH_COOKIE_USE_CSRF`, pero el proyecto deja ese flag en su default (`False`): las requests que autentican vía cookie no requieren un header CSRF adicional.

## Por qué era razonable

`JWT_AUTH_SAMESITE` queda en su default (`Lax`), y ADR 0018 ya asume que en prod frontend y backend se despliegan bajo una topología conocida (mismo sitio/subdominios de Atenea, no orígenes arbitrarios) — con `SameSite=Lax`, el navegador no adjunta la cookie en requests cross-site iniciados por JS desde un origen ajeno, lo que ya mitiga el escenario clásico de CSRF contra este endpoint. Activar `JWT_AUTH_COOKIE_USE_CSRF` exigiría además que el frontend lea y reenvíe un token CSRF en cada request de escritura (`POST`/`PATCH`/`DELETE`), trabajo de frontend no pedido en este pase.

## Señal de revisión

Si la topología de despliegue cambia (frontend y backend dejan de compartir dominio/subdominio — p. ej. frontend servido desde un CDN con dominio propio), o si se detecta/sospecha un intento de CSRF contra un endpoint autenticado por cookie, activar `JWT_AUTH_COOKIE_USE_CSRF=True` y coordinar el trabajo correspondiente en `api/client.ts` del frontend.
```

- [x] **Step 4: Agregar la entrada al índice de deuda técnica**

En `docs/technical-debt/README.md`, en la sección `### Activa`, después de la línea de `0008`, agregar:

```markdown
- [0009 — Sin protección CSRF explícita en el transporte de JWT por cookie](0009-sin-csrf-en-cookie-jwt.md)
```

- [x] **Step 5: Verificar que todos los enlaces markdown nuevos resuelven**

Run:
```bash
cd /home/hyfi/Development/atenea-fc
for f in docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md docs/decisions/0018-contrato-autenticacion-frontend-backend.md docs/development/api-frontend.md docs/technical-debt/README.md; do
  [ -f "$f" ] && echo "OK $f" || echo "MISSING $f"
done
```
Expected: las 4 líneas dicen `OK`.

- [x] **Step 6: Commit**

```bash
git add docs/decisions/0018-contrato-autenticacion-frontend-backend.md \
        docs/development/api-frontend.md \
        docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md \
        docs/technical-debt/README.md
git commit -m "docs: documentar fix de cookies JWT en prod y deuda técnica de CSRF"
```

---

## Self-Review

**Cobertura de la ADR 0018:**
- Decisión 1 (Google login vía GIS Token Client) — ya implementada antes de este plan, sin cambios; fuera de alcance porque no tiene brecha.
- Decisión 2 (JWT por cookie httpOnly en prod) — cubierta por Tareas 1 y 2, la brecha central de este plan.
- Decisión 3 (logout no invalida refresh server-side) — deliberadamente fuera de alcance, ya aceptada como deuda técnica 0007; Task 1 sí verifica que logout limpia las cookies del cliente correctamente, que es lo que la ADR promete para esa parte.

**Placeholder scan:** sin `TBD`/`implementar después`; cada paso trae código completo y comandos ejecutables con su output esperado.

**Consistencia de nombres:** `atenea-access-token`/`atenea-refresh-token` se usan idénticos en Task 1 (definición), Task 2 (consumo) y Task 3 (docs). `PROD_COOKIE_SETTINGS`/`dra_settings` se definen una vez en Task 1 y se reusan en Task 2 sin redefinir.

**Validación empírica previa a este plan:** los tres puntos críticos —(a) `patch.multiple` sobre `dj_rest_auth.app_settings.api_settings` sí propaga entre módulos, (b) sin el cambio de Task 2 la autenticación solo-por-cookie da `401`, (c) con el cambio de Task 2 la autenticación solo-por-cookie da `200` y el header sigue funcionando— se corrieron contra el código real de este repo antes de escribir el plan, no son inferencias sobre el comportamiento de la librería.
