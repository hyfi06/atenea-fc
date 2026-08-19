# Auth: password reset, blacklist de logout y CSRF en cookie JWT — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exponer recuperación de contraseña end-to-end (acotada a cuentas con password usable, con rate limit propio), invalidar el refresh token en el logout (deuda 0007) y exigir CSRF en las requests de escritura autenticadas por cookie JWT (deuda 0009).

**Architecture:** Backend: subclases delgadas de las vistas de `dj-rest-auth` en `accounts/views.py` montadas antes del `include` en `accounts/urls.py` (mismo patrón que `AteneaLoginView` ya usa); el filtro de "solo cuentas con password" vive en `accounts/serializers.py` vaciando `reset_form.users`, lo que reusa el camino de no-enumeración que allauth ya tiene. Frontend: dos pantallas nuevas que siguen literalmente el layout de `Login.tsx`, apoyadas en un `CampoTexto` extraído de ahí y en un módulo `auth/password.ts` que encapsula las dos llamadas.

**Tech Stack:** Django 6 + DRF 3.17 + dj-rest-auth 7.2 + django-allauth 65 + simplejwt 5.5 (backend, `uv`); React 19 + TypeScript + Vite + React Router 7 + Tailwind 4 + vitest/RTL (frontend).

**Spec:** [`docs/superpowers/specs/2026-08-19-auth-reset-blacklist-csrf-design.md`](../specs/2026-08-19-auth-reset-blacklist-csrf-design.md)

---

## Global Constraints

- **Rates fijados por este plan** (el spec los dejaba "a definir"): `password_reset = "3/hour"`, `password_reset_confirm = "10/hour"`. Dos scopes, no uno: fallar el confirm (contraseña débil, contraseñas distintas) no debe quemar el cupo de pedir el enlace. `dj_rest_auth = "5/min"` no se toca.
- **`JWT_AUTH_COOKIE_USE_CSRF = True` solo en `prod.py`.** En dev el JWT viaja en el header `Authorization` y `JWTCookieAuthentication` nunca llega a `enforce_csrf`.
- **Los tests de CSRF usan `APIClient(enforce_csrf_checks=True)`.** El `APIClient` default de DRF pone `request._dont_enforce_csrf_checks = True` y el middleware CSRF acepta todo: sin ese flag el test negativo pasa en verde sin probar nada.
- **Nombres exactos ya usados en el repo** que este plan reutiliza: `dra_settings` y `PROD_COOKIE_SETTINGS` (definidos a mitad de `backend/accounts/tests/test_auth.py`, líneas 215-223), `CloudflareScopedRateThrottle`, `FOCO_VISIBLE`.
- **Comando de tests backend:** desde `backend/`, `uv run manage.py test <ruta> -v 2`. Requiere Postgres y Redis: `docker compose -f docker-compose.dev.yml up -d postgres redis` desde la raíz. Alternativa: `docker compose -f docker-compose.dev.yml run --rm backend python manage.py test <ruta> -v 2`.
- **Comandos frontend** (desde `frontend/`): test puntual `npx vitest run <ruta>`; suite `npm test`; build `npm run build`; lint `npm run lint`.
- **Commits:** formato `[type][scope] resumen` + bullets + `Signed-off-by`. Usar `git commit -s`. Ver [`docs/development/commit-conventions.md`](../../development/commit-conventions.md).
- **Rama:** `dev`. No abrir PR ni hacer push salvo que Héctor lo pida.
- **Motion:** las pantallas nuevas solo reusan `entrada-lista`, que ya existe en `frontend/src/index.css` y ya está en el bloque `@media (prefers-reduced-motion: reduce)`. **Prohibido agregar `@keyframes` nuevos** en este plan (ADR 0026: toda animación nueva exige token de easing + entrada en ese bloque, en el mismo commit).
- **Accesibilidad obligatoria en cada pantalla nueva:** `htmlFor` en todo input (lo resuelve `CampoTexto`), `role="alert"` para errores, `role="status"` para confirmaciones, foco visible en todo interactivo.
- **No tocar** nada fuera de los archivos listados en cada tarea. Fuera de alcance explícito: personalizar el template del correo de reset, endpoint de auto-registro, migrar `Login.tsx`/`Boton.tsx` a la clase `.foco-visible`.
- **No "mejorar" el código de este plan.** Los bloques se pegan tal cual, incluidos comentarios y textos en español.

---

## File Structure

| Archivo | Responsabilidad | Acción | Tarea |
|---|---|---|---|
| `backend/config/settings/base.py` | `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS`, scopes de throttle, `token_blacklist` en `THIRD_PARTY_APPS` | Modificar | 1, 2, 3 |
| `backend/accounts/serializers.py` | `PasswordResetSerializer.validate_email` filtra usuarios sin password usable | Modificar | 1 |
| `backend/accounts/views.py` | Subclases con `throttle_scope` propio + `ensure_csrf_cookie` en login/google/user | Modificar | 2, 5 |
| `backend/accounts/urls.py` | Rutas override antes del `include("dj_rest_auth.urls")` | Modificar | 2, 5 |
| `backend/config/settings/prod.py` | `JWT_AUTH_COOKIE_USE_CSRF = True` | Modificar | 5 |
| `backend/accounts/tests/test_auth.py` | Tests de reset acotado, throttle dedicado, blacklist y CSRF | Modificar | 1, 2, 3, 5 |
| `frontend/src/auth/AuthContext.tsx` | Logout manda `refresh` en el body en dev | Modificar | 4 |
| `frontend/src/api/client.ts` | Lee cookie `csrftoken` y reenvía `X-CSRFToken` en métodos no seguros | Modificar | 6 |
| `frontend/src/components/ui/CampoTexto.tsx` | Campo de formulario con label flotante + `FOCO_VISIBLE` | Crear | 7 |
| `frontend/src/screens/Login.tsx` | Consume `CampoTexto`; el botón de "¿Olvidaste tu contraseña?" navega | Modificar | 7, 9 |
| `frontend/src/auth/password.ts` | `solicitarResetDePassword`, `confirmarResetDePassword` | Crear | 8 |
| `frontend/src/screens/ForgotPassword.tsx` | Pantalla: pide correo, dispara el envío del enlace | Crear | 9 |
| `frontend/src/screens/ResetPassword.tsx` | Pantalla: `/reset-password/:uid/:token`, fija la contraseña nueva | Crear | 10 |
| `frontend/src/App.tsx` | Rutas `/forgot-password` y `/reset-password/:uid/:token` | Modificar | 9, 10 |
| `docs/decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md` | ADR de las tres decisiones | Crear | 11 |
| `docs/technical-debt/0007-*.md`, `0009-*.md` | Estado → Resuelta | Modificar | 11 |
| `docs/technical-debt/0022-*.md`, `0023-*.md` | Deuda nueva: template de correo default; blacklist sin purga | Crear | 11 |
| `docs/technical-debt/README.md` | Índice | Modificar | 11 |
| `docs/development/api-frontend.md` | Contrato: logout, reset, CSRF | Modificar | 11 |

---

## Especificación ligera de componente — `ForgotPassword` / `ResetPassword`

> **Gate visual (leer antes de la Tarea 9).** `docs/development/contribuir-componentes.md` § "Cuándo necesita revisión visual antes de código" pide `superpowers:brainstorming` + mockup para una pantalla nueva. El spec aprobado es de backend/arquitectura y no trae esa tabla. Esta sección la suple con la especificación ligera que ese mismo documento define (§ "Especificación ligera de componente") y **necesita un OK explícito de Héctor antes de ejecutar las Tareas 9 y 10**; las Tareas 1-8 y 11 no dependen de él. No hay patrón de interacción nuevo: ambas pantallas son el formulario de `Login.tsx` con otro contenido.

**Anatomía (ambas, de arriba abajo):** botón circular de volver (`aria-label="Volver"`, ícono chevron, idéntico al de `Login.tsx`) → `<h1>` → párrafo de contexto → formulario (`CampoTexto` × N → mensaje `role="alert"` si hay error → `Boton` de envío).

**Estados** (prioridad `disabled > loading > default`; el `disabled` visual lo da `Boton` con `cargando`):

| Pantalla | default | enviando | resuelto |
|---|---|---|---|
| `ForgotPassword` | formulario con 1 campo (Correo) | `Boton cargando` (spinner, `disabled`) | formulario reemplazado por `role="status"` con el mensaje de no-enumeración |
| `ResetPassword` | formulario con 2 campos (Contraseña nueva / Confirmar) | `Boton cargando` | `role="status"` + `Boton` "Ir a iniciar sesión" |

**Casos de error (`role="alert"`, el formulario permanece montado y editable):**

| Caso | Copy |
|---|---|
| `ForgotPassword`, 429 | Demasiadas solicitudes. Espera una hora antes de volver a intentar. |
| `ForgotPassword`, cualquier otro fallo | No se pudo enviar el correo. Intenta de nuevo. |
| `ResetPassword`, contraseñas distintas (validado en cliente, sin request) | Las contraseñas no coinciden. |
| `ResetPassword`, 400 con `uid`/`token` | El enlace no es válido o ya expiró. Solicita uno nuevo. |
| `ResetPassword`, 400 con `new_password1`/`new_password2` | El mensaje que manda el backend (validadores de Django, ya traducidos por `LANGUAGE_CODE = "es-mx"`). |
| `ResetPassword`, 429 | Demasiados intentos. Espera una hora antes de volver a intentar. |
| `ResetPassword`, cualquier otro fallo | No se pudo cambiar la contraseña. Intenta de nuevo. |

**Variantes:** ninguna. Ambas pantallas tienen una sola forma; todo el color sale de tokens ya existentes (`text-on-background`, `text-on-surface-variant`, `text-error`, `bg-background`).

---

## Task 1: Password reset acotado a cuentas con contraseña usable

**Files:**
- Modify: `backend/config/settings/base.py:21` (bloque `ACCOUNT_*`)
- Modify: `backend/accounts/serializers.py:71-73`
- Test: `backend/accounts/tests/test_auth.py`

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces: `accounts.serializers.PasswordResetSerializer` (ya registrado en `REST_AUTH["PASSWORD_RESET_SERIALIZER"]`, no cambia el registro).

**Contexto imprescindible:** hoy, un correo desconocido entra a `allauth.account.internal.flows.password_reset.request_password_reset` con `users=[]`, que llama `send_unknown_account_mail` → `get_signup_url` → `reverse("account_signup")`. **`allauth.urls` no está incluido en `backend/config/urls.py`**, así que eso revienta con `NoReverseMatch` (500). Al filtrar cuentas Google-only caemos en ese mismo camino, así que hay que apagar ese correo — que además no tiene sentido en Atenea: no hay auto-registro (`is_open_for_signup = False`).

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `backend/accounts/tests/test_auth.py`:

```python
class PasswordResetSoloCuentasConPasswordTests(APITestCase):
    """El reset existe para las cuentas que entran con contraseña (staff, SAE,
    asesores no-alumnos). Una cuenta que solo entra por Google no tiene
    contraseña que restablecer: pedirla no debe mandar ningún correo, y la
    respuesta debe ser idéntica a la de un correo que no existe (no-enumeración).
    """

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _post_reset(self, email):
        return self.client.post(
            "/api/auth/password/reset/", {"email": email}, format="json"
        )

    def test_cuenta_sin_password_usable_no_recibe_enlace(self):
        user = User.objects.create_user("solo-google@ciencias.unam.mx")
        self.assertFalse(user.has_usable_password())

        response = self._post_reset(user.email)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mail.outbox, [])

    def test_correo_inexistente_no_revienta_y_no_manda_nada(self):
        response = self._post_reset("nadie@ciencias.unam.mx")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mail.outbox, [])

    def test_respuesta_indistinguible_entre_google_only_y_correo_inexistente(self):
        User.objects.create_user("google-only@ciencias.unam.mx")

        respuesta_google = self._post_reset("google-only@ciencias.unam.mx")
        correos_google = list(mail.outbox)
        mail.outbox = []
        cache.clear()
        respuesta_inexistente = self._post_reset("nadie@ciencias.unam.mx")

        self.assertEqual(respuesta_google.status_code, respuesta_inexistente.status_code)
        self.assertEqual(respuesta_google.data, respuesta_inexistente.data)
        self.assertEqual(len(correos_google), len(mail.outbox))

    def test_cuenta_con_password_usable_sigue_recibiendo_el_enlace(self):
        user = User.objects.create_user(
            "con-password@ciencias.unam.mx", password="ClaveSegura123!"
        )

        response = self._post_reset(user.email)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/reset-password/", mail.outbox[0].body)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `uv run manage.py test accounts.tests.test_auth.PasswordResetSoloCuentasConPasswordTests -v 2`
Expected: FAIL — `test_cuenta_sin_password_usable_no_recibe_enlace` con 1 correo en `outbox`; `test_correo_inexistente_no_revienta_y_no_manda_nada` con `NoReverseMatch: Reverse for 'account_signup' not found`.

- [ ] **Step 3: Apagar el correo de "cuenta desconocida"**

En `backend/config/settings/base.py`, justo debajo de la línea `ACCOUNT_EMAIL_VERIFICATION = "none"`, agregar:

```python
# Atenea no tiene auto-registro (`AccountAdapter.is_open_for_signup` -> False),
# así que el correo de allauth "no existe esa cuenta, regístrate aquí" no aplica:
# invita a una ruta que no existe y además revienta con NoReverseMatch, porque
# `allauth.urls` no está incluido en config/urls.py y su plantilla resuelve
# `reverse("account_signup")`. Apagarlo es también lo que hace indistinguibles
# las respuestas de "correo desconocido" y "cuenta que solo entra por Google".
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
```

- [ ] **Step 4: Filtrar las cuentas sin contraseña usable**

En `backend/accounts/serializers.py`, reemplazar la clase `PasswordResetSerializer` completa por:

```python
class PasswordResetSerializer(BasePasswordResetSerializer):
    def get_email_options(self):
        return {"url_generator": atenea_password_reset_url_generator}

    def validate_email(self, value):
        """Acota el reset a cuentas password-based.

        No existe un campo de "tipo de cuenta" en `User`: la distinción es de
        comportamiento. Los alumnos se dan de alta con `.create()` (password no
        usable) y entran por Google; las cuentas con contraseña se crean desde el
        admin. `has_usable_password()` es el criterio verificable.

        Se vacía `reset_form.users` en vez de levantar un error para caer en el
        MISMO camino que un correo desconocido (`request_password_reset` con
        `users=[]`): la respuesta queda indistinguible y no filtra ni qué cuentas
        existen ni de qué tipo son.
        """
        value = super().validate_email(value)
        self.reset_form.users = [
            user
            for user in getattr(self.reset_form, "users", [])
            if user.has_usable_password()
        ]
        return value
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth.PasswordResetSoloCuentasConPasswordTests accounts.tests.test_auth.PasswordResetLoginFlowTests -v 2`
Expected: PASS (8 tests).

- [ ] **Step 6: Correr la suite de accounts**

Run: `uv run manage.py test accounts -v 2`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/config/settings/base.py backend/accounts/serializers.py backend/accounts/tests/test_auth.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] acotar el password reset a cuentas con contraseña usable

- filtrar `reset_form.users` por `has_usable_password()` en PasswordResetSerializer
- apagar ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS: el correo de cuenta desconocida revienta
  con NoReverseMatch porque allauth.urls no está incluido, y no aplica sin autoregistro
- tests: sin correo para cuentas Google-only, respuesta indistinguible de un correo inexistente
EOF
)"
```

---

## Task 2: Rate limit dedicado para el flujo de reset

**Files:**
- Modify: `backend/config/settings/base.py:161-163` (`DEFAULT_THROTTLE_RATES`)
- Modify: `backend/accounts/views.py`
- Modify: `backend/accounts/urls.py`
- Test: `backend/accounts/tests/test_auth.py`

**Interfaces:**
- Consumes: `accounts.throttling.CloudflareScopedRateThrottle` (ya es `DEFAULT_THROTTLE_CLASSES`).
- Produces: `accounts.views.AteneaPasswordResetView`, `accounts.views.AteneaPasswordResetConfirmView`; scopes `"password_reset"` y `"password_reset_confirm"`.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `backend/accounts/tests/test_auth.py`:

```python
class PasswordResetThrottleTests(APITestCase):
    """El reset tenía el scope `dj_rest_auth` (5/min) compartido con el login:
    un atacante golpeando reset consumía el cupo de quien intenta entrar, y
    viceversa. Scope propio y más estricto: 3/hour pedir el enlace, 10/hour
    confirmarlo."""

    CORREO = "reset-throttle@ciencias.unam.mx"

    def setUp(self):
        cache.clear()
        User.objects.create_user(self.CORREO, password="ClaveSegura123!")

    def tearDown(self):
        cache.clear()

    def _post_reset(self, **extra):
        return self.client.post(
            "/api/auth/password/reset/", {"email": self.CORREO}, format="json", **extra
        )

    def _post_confirm(self):
        return self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uid": "abc",
                "token": "token-invalido",
                "new_password1": "NuevaClave123!",
                "new_password2": "NuevaClave123!",
            },
            format="json",
        )

    def test_cuarta_solicitud_de_enlace_devuelve_429(self):
        for _ in range(3):
            self.assertEqual(self._post_reset().status_code, status.HTTP_200_OK)

        self.assertEqual(self._post_reset().status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_agotar_el_cupo_de_reset_no_bloquea_el_login(self):
        for _ in range(3):
            self._post_reset()
        self.assertEqual(self._post_reset().status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        response = self.client.post(
            "/api/auth/login/",
            {"email": self.CORREO, "password": "ClaveSegura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_tiene_su_propio_cupo(self):
        for _ in range(4):
            self.assertEqual(self._post_confirm().status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(self._post_reset().status_code, status.HTTP_200_OK)

    def test_reset_usa_cf_connecting_ip_no_x_forwarded_for(self):
        for i in range(3):
            response = self._post_reset(
                HTTP_X_FORWARDED_FOR=f"1.2.3.{i}",  # distinto en cada intento
                HTTP_CF_CONNECTING_IP="9.9.9.9",  # mismo cliente real
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self._post_reset(
            HTTP_X_FORWARDED_FOR="1.2.3.99", HTTP_CF_CONNECTING_IP="9.9.9.9"
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `uv run manage.py test accounts.tests.test_auth.PasswordResetThrottleTests -v 2`
Expected: FAIL — la 4ª solicitud responde 200 (el scope compartido permite 5/min).

- [ ] **Step 3: Declarar los scopes**

En `backend/config/settings/base.py`, reemplazar el bloque `"DEFAULT_THROTTLE_RATES"` por:

```python
    "DEFAULT_THROTTLE_RATES": {
        "dj_rest_auth": "5/min",
        # Scopes propios para el flujo de recuperación de contraseña: con el
        # scope compartido, quien golpea reset consume el cupo de quien intenta
        # entrar (y viceversa). Pedir el enlace dispara un correo y es una acción
        # rarísima en operación normal -> 3/hour. Confirmarlo no manda correo y
        # está protegido por el token del enlace, pero el usuario puede fallar
        # los validadores de contraseña varias veces -> cupo propio, más holgado.
        "password_reset": "3/hour",
        "password_reset_confirm": "10/hour",
    },
```

- [ ] **Step 4: Agregar las subclases de vista**

En `backend/accounts/views.py`, cambiar la línea 2 de imports y agregar las clases al final del archivo:

```python
from dj_rest_auth.views import LoginView, PasswordResetConfirmView, PasswordResetView
```

```python
class AteneaPasswordResetView(PasswordResetView):
    """Solo cambia el scope de throttle (ver DEFAULT_THROTTLE_RATES)."""

    throttle_scope = "password_reset"


class AteneaPasswordResetConfirmView(PasswordResetConfirmView):
    throttle_scope = "password_reset_confirm"
```

- [ ] **Step 5: Montar las rutas antes del include**

Reemplazar `backend/accounts/urls.py` completo por:

```python
from django.urls import include, path, re_path

from .views import (
    AteneaLoginView,
    AteneaPasswordResetConfirmView,
    AteneaPasswordResetView,
    GoogleLoginView,
)

urlpatterns = [
    # Overrides de dj_rest_auth.urls: Django usa el primer match, así que estos
    # paths ganan. El include de abajo no se toca (sigue sirviendo logout, user,
    # token/refresh, password/change). Mantener los mismos `name` que usa
    # dj_rest_auth.urls, por si algo hace reverse().
    re_path(r"^login/?$", AteneaLoginView.as_view(), name="rest_login"),
    path(
        "password/reset/",
        AteneaPasswordResetView.as_view(),
        name="rest_password_reset",
    ),
    path(
        "password/reset/confirm/",
        AteneaPasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    path("", include("dj_rest_auth.urls")),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
]
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth.PasswordResetThrottleTests accounts.tests.test_auth.PasswordResetLoginFlowTests accounts.tests.test_auth.LoginThrottleTests -v 2`
Expected: PASS.

- [ ] **Step 7: Correr la suite de accounts**

Run: `uv run manage.py test accounts -v 2`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/config/settings/base.py backend/accounts/views.py backend/accounts/urls.py backend/accounts/tests/test_auth.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] dar scope de throttle propio al flujo de password reset

- agregar los scopes password_reset (3/hour) y password_reset_confirm (10/hour)
- montar AteneaPasswordResetView/AteneaPasswordResetConfirmView antes del include de dj_rest_auth
- tests: cupo propio, no comparte con login, e ident por CF-Connecting-IP
EOF
)"
```

---

## Task 3: Blacklist del refresh token en el logout (deuda 0007)

**Files:**
- Modify: `backend/config/settings/base.py:50-58` (`THIRD_PARTY_APPS`)
- Test: `backend/accounts/tests/test_auth.py:252-274` (test existente que hay que adaptar) y clase nueva al final

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces: comportamiento de `POST /api/auth/logout/` — exige `{"refresh": "<token>"}` en el body cuando `JWT_AUTH_HTTPONLY=False` (dev), y la cookie `atenea-refresh-token` cuando es `True` (prod). Lo consume la Tarea 4.

**Contexto imprescindible:** `dj_rest_auth.views.LogoutView.logout()` (líneas 183-206 de la librería) ya trae toda la lógica, condicionada a que `'rest_framework_simplejwt.token_blacklist'` esté en `INSTALLED_APPS`. Al activarla, un logout **sin** refresh (body o cookie según el modo) pasa a responder **401**: por eso el test existente `test_logout_clears_both_cookies_when_configured` deja de pasar y hay que darle la cookie de refresh.

- [ ] **Step 1: Escribir los tests que fallan**

(a) En `backend/accounts/tests/test_auth.py`, dentro de `test_logout_clears_both_cookies_when_configured`, justo debajo de la línea que asigna `self.client.cookies["atenea-access-token"]`, agregar:

```python
            # Con token_blacklist activo, LogoutView necesita el refresh token:
            # en modo httpOnly lo lee de esta cookie o responde 401.
            self.client.cookies["atenea-refresh-token"] = login_response.cookies["atenea-refresh-token"].value
```

(b) Agregar al final del archivo:

```python
class LogoutBlacklistTests(APITestCase):
    """Deuda 0007: el logout limpiaba el estado del cliente pero el refresh
    seguía siendo válido en el servidor hasta su expiración natural (7 días)."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _login(self, email):
        return self.client.post(
            "/api/auth/login/", {"email": email, "password": "ClaveSegura123!"}, format="json"
        )

    def test_refresh_despues_de_logout_es_rechazado(self):
        user = User.objects.create_user("blacklist@ciencias.unam.mx", password="ClaveSegura123!")
        login = self._login(user.email)
        refresh = login.data["refresh"]

        logout = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": refresh}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_sin_refresh_en_el_body_devuelve_401(self):
        """Contrato que el frontend tiene que respetar en dev: sin el refresh en
        el body no hay nada que invalidar y la librería responde 401."""
        user = User.objects.create_user("blacklist-sin@ciencias.unam.mx", password="ClaveSegura123!")
        login = self._login(user.email)

        response = self.client.post(
            "/api/auth/logout/",
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_de_una_sesion_viva_sigue_funcionando_despues_de_otro_logout(self):
        user = User.objects.create_user("blacklist-otra@ciencias.unam.mx", password="ClaveSegura123!")
        primera = self._login(user.email)
        segunda = self._login(user.email)

        self.client.post(
            "/api/auth/logout/",
            {"refresh": primera.data["refresh"]},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {primera.data['access']}",
        )

        response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": segunda.data["refresh"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `uv run manage.py test accounts.tests.test_auth.LogoutBlacklistTests -v 2`
Expected: FAIL — `test_refresh_despues_de_logout_es_rechazado` da 200 en el refresh final; `test_logout_sin_refresh_en_el_body_devuelve_401` da 200.

- [ ] **Step 3: Instalar la app de blacklist**

En `backend/config/settings/base.py`, reemplazar el bloque `THIRD_PARTY_APPS` por:

```python
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "dj_rest_auth",
    # Cierra la deuda 0007: con esta app instalada, dj_rest_auth.views.LogoutView
    # manda el refresh token al blacklist en cada logout (su lógica ya existe,
    # condicionada solo a que la app esté en INSTALLED_APPS). Ojo: a partir de
    # aquí el logout EXIGE el refresh — en el body si JWT_AUTH_HTTPONLY=False
    # (dev), en la cookie si es True (prod) — o responde 401.
    "rest_framework_simplejwt.token_blacklist",
]
```

- [ ] **Step 4: Aplicar la migración de la app nueva**

Run: `uv run manage.py migrate token_blacklist`
Expected: aplica `token_blacklist.0001_initial` … `0012_*` (crea `OutstandingToken` y `BlacklistedToken`). No se genera ninguna migración propia del proyecto.

Verificar que no quedó nada pendiente:
Run: `uv run manage.py makemigrations --check --dry-run`
Expected: "No changes detected".

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth.LogoutBlacklistTests accounts.tests.test_auth.CookieBasedLoginTests -v 2`
Expected: PASS.

- [ ] **Step 6: Correr la suite completa del backend**

Run: `uv run manage.py test`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/config/settings/base.py backend/accounts/tests/test_auth.py
git commit -s -m "$(cat <<'EOF'
[feat][backend] invalidar el refresh token en el logout (deuda 0007)

- instalar rest_framework_simplejwt.token_blacklist
- adaptar test_logout_clears_both_cookies_when_configured: el logout httpOnly ahora exige la cookie de refresh
- tests: un refresh usado después del logout es rechazado; otras sesiones no se ven afectadas
EOF
)"
```

---

## Task 4: El logout del frontend manda el refresh token en dev

**Files:**
- Modify: `frontend/src/auth/AuthContext.tsx:66-75`
- Test: `frontend/src/auth/AuthContext.test.tsx`

**Interfaces:**
- Consumes: el contrato de la Tarea 3 (`POST /api/auth/logout/` responde 401 en dev si el body no trae `refresh`).
- Produces: nada nuevo — `logout()` mantiene su firma `() => Promise<void>`.

- [ ] **Step 1: Escribir el test que falla**

(a) En `frontend/src/auth/AuthContext.test.tsx`, reemplazar el componente `Sonda` completo por:

```tsx
function Sonda() {
  const { status, user, roles, loginWithPassword, loginWithGoogle, logout } = useAuth()
  return (
    <>
      <div data-testid="estado">{status}:{user?.email ?? 'sin-usuario'}</div>
      <div data-testid="roles">{roles.join(',') || 'sin-roles'}</div>
      <button type="button" onClick={() => loginWithPassword('a@ciencias.unam.mx', 'x')}>
        Entrar con contraseña
      </button>
      <button type="button" onClick={() => loginWithGoogle()}>
        Entrar con Google
      </button>
      <button type="button" onClick={() => logout()}>
        Salir
      </button>
    </>
  )
}
```

(b) Agregar este test dentro del `describe('AuthProvider', ...)`, antes de su llave de cierre:

```tsx
  it('el logout manda el refresh token en el body (dev): sin él el blacklist responde 401', async () => {
    vi.spyOn(client, 'apiGet').mockRejectedValue(new client.ApiError(401, { detail: 'no autenticado' }))
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({
      access: 'jwt-access',
      refresh: 'jwt-refresh',
      user: usuarioDePrueba({ roles: ['alumno'] }),
    })

    montar()
    await waitFor(() => expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated'))
    fireEvent.click(screen.getByRole('button', { name: 'Entrar con contraseña' }))
    await waitFor(() => expect(screen.getByTestId('roles')).toHaveTextContent('alumno'))

    fireEvent.click(screen.getByRole('button', { name: 'Salir' }))

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/auth/logout/', { refresh: 'jwt-refresh' }),
    )
    await waitFor(() =>
      expect(screen.getByTestId('estado')).toHaveTextContent('unauthenticated:sin-usuario'),
    )
  })
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run (desde `frontend/`): `npx vitest run src/auth/AuthContext.test.tsx`
Expected: FAIL — `apiPost` fue llamado con `('/api/auth/logout/', {})`.

- [ ] **Step 3: Mandar el refresh en el body en dev**

En `frontend/src/auth/AuthContext.tsx`, reemplazar la función `logout` completa por:

```tsx
  async function logout() {
    try {
      // Con `token_blacklist` instalado (deuda 0007), el logout invalida el
      // refresh en el servidor: en prod lo toma de la cookie httpOnly, en dev
      // hay que mandárselo explícito o responde 401 y no invalida nada.
      // Mismo criterio que `refrescarToken` en api/client.ts.
      const body = import.meta.env.PROD ? {} : { refresh: localStorage.getItem(CLAVE_REFRESH) }
      await apiPost('/api/auth/logout/', body)
    } catch {
      // el logout limpia el lado del cliente igual aunque el request falle
    }
    limpiarSesion()
    setUser(null)
    setStatus('unauthenticated')
  }
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `npx vitest run src/auth/AuthContext.test.tsx`
Expected: PASS.

- [ ] **Step 5: Suite, lint y build**

Run: `npm test && npm run lint && npm run build`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/auth/AuthContext.tsx frontend/src/auth/AuthContext.test.tsx
git commit -s -m "$(cat <<'EOF'
[fix][frontend] mandar el refresh token en el logout de dev

- sin el refresh en el body, el logout con token_blacklist activo responde 401 y no invalida nada
- test: logout llama a /api/auth/logout/ con { refresh } y limpia la sesión local
EOF
)"
```

---

## Task 5: CSRF en el transporte por cookie JWT — backend (deuda 0009)

**Files:**
- Modify: `backend/config/settings/prod.py:39-46`
- Modify: `backend/accounts/views.py`
- Modify: `backend/accounts/urls.py`
- Test: `backend/accounts/tests/test_auth.py:186-192` (script de `ProdSettingsJWTCookieTests`) y clase nueva al final

**Interfaces:**
- Consumes: `AteneaPasswordResetView`/`AteneaPasswordResetConfirmView` de la Tarea 2 (el import de `urls.py` crece).
- Produces: `accounts.views.AteneaUserDetailsView`; toda respuesta de `/api/auth/login/`, `/api/auth/google/` y `/api/auth/user/` emite la cookie `csrftoken`. Lo consume la Tarea 6.

**Contexto imprescindible:** `JWTCookieAuthentication.enforce_csrf` (dj-rest-auth `jwt_auth.py:121-133`) corre el `CSRFCheck` de Django cuando el request se autentica **por cookie** y `JWT_AUTH_COOKIE_USE_CSRF` está en `True`. Django exige la cookie `csrftoken` **y** el header `X-CSRFToken`; esa cookie solo se emite si alguna vista llama `get_token(request)` — por eso hacen falta los `ensure_csrf_cookie`. Los métodos seguros (`GET`/`HEAD`/`OPTIONS`) nunca se rechazan, así que el `GET /api/auth/user/` que el SPA hace al montar sirve para sembrar la cookie.

- [ ] **Step 1: Escribir los tests que fallan**

(a) En `backend/accounts/tests/test_auth.py`, dentro del `script` de `ProdSettingsJWTCookieTests.test_prod_settings_configure_jwt_cookies`, reemplazar la línea de la tupla de claves por:

```python
            "        for k in ('JWT_AUTH_HTTPONLY', 'JWT_AUTH_COOKIE', 'JWT_AUTH_REFRESH_COOKIE', 'JWT_AUTH_SECURE', 'JWT_AUTH_SAMESITE', 'JWT_AUTH_COOKIE_USE_CSRF')\n"
```

y agregar, al final del mismo método:

```python
        self.assertEqual(output["REST_AUTH"]["JWT_AUTH_COOKIE_USE_CSRF"], True)
```

(b) Agregar al final del archivo:

```python
CSRF_COOKIE_SETTINGS = dict(PROD_COOKIE_SETTINGS, JWT_AUTH_COOKIE_USE_CSRF=True)


class CsrfEnCookieJwtTests(APITestCase):
    """Deuda 0009, confirmada explotable en el pentest de staging (2026-08-18):
    una escritura autenticada solo por cookie, sin ningún token CSRF, era
    aceptada por la API.

    Ojo con `enforce_csrf_checks=True`: el APIClient default de DRF marca
    `request._dont_enforce_csrf_checks` y el middleware CSRF acepta todo, así
    que sin ese flag estos tests pasarían sin probar nada.
    """

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("csrf@ciencias.unam.mx", password="ClaveSegura123!")

    def tearDown(self):
        cache.clear()

    def _login(self):
        return self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "ClaveSegura123!"},
            format="json",
        )

    def test_escritura_solo_con_cookie_y_sin_header_csrf_es_403(self):
        with patch.multiple(dra_settings, **CSRF_COOKIE_SETTINGS):
            login = self._login()
            cliente = APIClient(enforce_csrf_checks=True)
            cliente.cookies["atenea-access-token"] = login.cookies["atenea-access-token"].value

            response = cliente.patch("/api/auth/user/", {"first_name": "Ana"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_escritura_con_cookie_csrf_y_header_pasa(self):
        with patch.multiple(dra_settings, **CSRF_COOKIE_SETTINGS):
            login = self._login()
            cliente = APIClient(enforce_csrf_checks=True)
            cliente.cookies["atenea-access-token"] = login.cookies["atenea-access-token"].value
            # GET es método seguro: nunca se rechaza y siembra la cookie CSRF.
            cliente.get("/api/auth/user/")
            csrftoken = cliente.cookies["csrftoken"].value

            response = cliente.patch(
                "/api/auth/user/",
                {"first_name": "Ana"},
                format="json",
                HTTP_X_CSRFTOKEN=csrftoken,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Ana")

    def test_el_login_emite_la_cookie_csrf(self):
        """El SPA se sirve desde nginx: el primer contacto con Django es el
        login (o el GET de /api/auth/user/). Si ninguno emite la cookie, el SPA
        no tiene nada que reenviar."""
        response = self._login()

        self.assertIn("csrftoken", response.cookies)

    def test_el_get_de_user_emite_la_cookie_csrf(self):
        login = self._login()
        cliente = APIClient(enforce_csrf_checks=True)

        response = cliente.get(
            "/api/auth/user/", HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", response.cookies)

    def test_header_authorization_no_exige_csrf(self):
        """Dev (y cualquier cliente con Bearer) no se ve afectado: enforce_csrf
        solo corre cuando la autenticación vino de la cookie."""
        with patch.multiple(dra_settings, **CSRF_COOKIE_SETTINGS):
            login = self._login()
            cliente = APIClient(enforce_csrf_checks=True)

            response = cliente.patch(
                "/api/auth/user/",
                {"first_name": "Ana"},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {login.cookies['atenea-access-token'].value}",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `uv run manage.py test accounts.tests.test_auth.CsrfEnCookieJwtTests accounts.tests.test_auth.ProdSettingsJWTCookieTests -v 2`
Expected: FAIL — `test_escritura_solo_con_cookie_y_sin_header_csrf_es_403` responde 200 (el hallazgo del pentest), los dos tests de la cookie `csrftoken` no la encuentran, y el de prod ve `JWT_AUTH_COOKIE_USE_CSRF = False`.

- [ ] **Step 3: Activar el flag en prod**

En `backend/config/settings/prod.py`, reemplazar el bloque `REST_AUTH = {...}` por:

```python
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
```

- [ ] **Step 4: Emitir la cookie CSRF desde login, google y user**

En `backend/accounts/views.py`, reemplazar las líneas de import del inicio del archivo por:

```python
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import (
    LoginView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from .adapters import GoogleIdTokenAdapter
from .serializers import GoogleLoginSerializer
```

Reemplazar las clases `AteneaLoginView` y `GoogleLoginView` por:

```python
# `ensure_csrf_cookie` fuerza a Django a emitir la cookie `csrftoken` en la
# respuesta. Sin ella, JWT_AUTH_COOKIE_USE_CSRF (prod) rechazaría toda escritura:
# la cookie solo se emite si alguna vista llama get_token(request), y el SPA se
# sirve desde nginx, así que su primer contacto con Django es el login o el
# GET de /api/auth/user/ al montar. La cookie NO es httpOnly a propósito — el
# SPA tiene que poder leerla para reenviarla como header X-CSRFToken.
@method_decorator(ensure_csrf_cookie, name="dispatch")
class AteneaLoginView(LoginResponseSinAccessEnBodyMixin, LoginView):
    pass


@method_decorator(ensure_csrf_cookie, name="dispatch")
class GoogleLoginView(LoginResponseSinAccessEnBodyMixin, SocialLoginView):
    adapter_class = GoogleIdTokenAdapter
    serializer_class = GoogleLoginSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AteneaUserDetailsView(UserDetailsView):
    """Igual que la de dj-rest-auth, solo emite la cookie CSRF.

    Cubre la transición: una sesión abierta desde antes de este cambio no tiene
    cookie `csrftoken`, y el SPA hace GET /api/auth/user/ al montar. GET es un
    método seguro, nunca se rechaza por CSRF, así que ahí se siembra la cookie
    sin obligar a nadie a volver a entrar.
    """
```

**Ojo:** `AteneaUserDetailsView` termina en docstring, sin `pass` — el docstring ya es el cuerpo de la clase.

- [ ] **Step 5: Montar la ruta de user antes del include**

En `backend/accounts/urls.py`, reemplazar el bloque de import y agregar la ruta:

```python
from django.urls import include, path, re_path

from .views import (
    AteneaLoginView,
    AteneaPasswordResetConfirmView,
    AteneaPasswordResetView,
    AteneaUserDetailsView,
    GoogleLoginView,
)
```

y agregar, inmediatamente antes de la línea `path("", include("dj_rest_auth.urls")),`:

```python
    path("user/", AteneaUserDetailsView.as_view(), name="rest_user_details"),
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth.CsrfEnCookieJwtTests accounts.tests.test_auth.ProdSettingsJWTCookieTests accounts.tests.test_auth.CookieBasedLoginTests -v 2`
Expected: PASS.

- [ ] **Step 7: Correr la suite completa del backend**

Run: `uv run manage.py test`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/config/settings/prod.py backend/accounts/views.py backend/accounts/urls.py backend/accounts/tests/test_auth.py
git commit -s -m "$(cat <<'EOF'
[fix][backend] exigir CSRF en las escrituras autenticadas por cookie JWT (deuda 0009)

- activar JWT_AUTH_COOKIE_USE_CSRF en prod
- emitir la cookie csrftoken desde login, google y /api/auth/user/ con ensure_csrf_cookie
- test de regresión del hallazgo del pentest: PATCH solo con cookie y sin X-CSRFToken -> 403
EOF
)"
```

---

## Task 6: CSRF en el transporte por cookie JWT — frontend

**Files:**
- Modify: `frontend/src/api/client.ts`
- Test: `frontend/src/api/client.test.ts`

**Interfaces:**
- Consumes: la cookie `csrftoken` que emite el backend (Tarea 5).
- Produces: `leerCookie(nombre: string): string | null` exportada desde `api/client.ts`; todo `apiPost`/`apiPatch`/`apiDelete` manda `X-CSRFToken` cuando la cookie existe.

- [ ] **Step 1: Escribir los tests que fallan**

En `frontend/src/api/client.test.ts`, cambiar la primera línea de import por:

```ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import { apiGet, apiPost, apiPatch } from './client'
```

y agregar al final del archivo:

```ts
describe('X-CSRFToken', () => {
  afterEach(() => {
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  function mockearFetch() {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    } as Response)
    global.fetch = fetchMock
    return fetchMock
  }

  it('reenvía la cookie csrftoken como header en POST', async () => {
    document.cookie = 'csrftoken=token-de-prueba; path=/'
    const fetchMock = mockearFetch()

    await apiPost('/api/auth/logout/', {})

    const [, init] = fetchMock.mock.calls[0]
    expect(init.headers.get('X-CSRFToken')).toBe('token-de-prueba')
  })

  it('reenvía la cookie csrftoken como header en PATCH', async () => {
    document.cookie = 'csrftoken=token-de-prueba; path=/'
    const fetchMock = mockearFetch()

    await apiPatch('/api/auth/user/', { first_name: 'Ana' })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.headers.get('X-CSRFToken')).toBe('token-de-prueba')
  })

  it('no manda el header en GET (método seguro, Django no lo pide)', async () => {
    document.cookie = 'csrftoken=token-de-prueba; path=/'
    const fetchMock = mockearFetch()

    await apiGet('/api/auth/user/')

    const [, init] = fetchMock.mock.calls[0]
    expect(init.headers.get('X-CSRFToken')).toBeNull()
  })

  it('no manda el header si no hay cookie csrftoken', async () => {
    const fetchMock = mockearFetch()

    await apiPost('/api/auth/logout/', {})

    const [, init] = fetchMock.mock.calls[0]
    expect(init.headers.get('X-CSRFToken')).toBeNull()
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run (desde `frontend/`): `npx vitest run src/api/client.test.ts`
Expected: FAIL — `init.headers.get('X-CSRFToken')` es `null` en los dos primeros tests.

- [ ] **Step 3: Leer y reenviar la cookie**

En `frontend/src/api/client.ts`, agregar debajo de la declaración de `CLAVE_REFRESH`:

```ts
/** Nombre default de la cookie CSRF de Django (`CSRF_COOKIE_NAME`). */
const COOKIE_CSRF = 'csrftoken'
/** Django solo valida CSRF en los métodos que no son seguros. */
const METODOS_SEGUROS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE'])
```

Agregar, debajo de la función `tokenDeAcceso`:

```ts
/** Lee una cookie legible por JS. La `csrftoken` de Django no es httpOnly a
 *  propósito: en prod (ADR 0018 + deuda 0009) el SPA tiene que reenviarla como
 *  header `X-CSRFToken` en toda escritura, porque el JWT viaja en cookie y
 *  `JWT_AUTH_COOKIE_USE_CSRF` está activo. */
export function leerCookie(nombre: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

function agregarCsrf(headers: Headers, metodo: string) {
  if (METODOS_SEGUROS.has(metodo.toUpperCase())) return
  const csrf = leerCookie(COOKIE_CSRF)
  if (csrf) headers.set('X-CSRFToken', csrf)
}
```

En `refrescarToken`, reemplazar el bloque del `fetch` por:

```ts
  const headers = new Headers({ 'Content-Type': 'application/json' })
  agregarCsrf(headers, 'POST')
  const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify(body),
  })
```

En `solicitar`, reemplazar este bloque:

```ts
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  const token = tokenDeAcceso()
  if (token) headers.set('Authorization', `Bearer ${token}`)
```

por este:

```ts
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  agregarCsrf(headers, init.method ?? 'GET')
  const token = tokenDeAcceso()
  if (token) headers.set('Authorization', `Bearer ${token}`)
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/api/client.test.ts`
Expected: PASS.

- [ ] **Step 5: Suite, lint y build**

Run: `npm test && npm run lint && npm run build`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/api/client.test.ts
git commit -s -m "$(cat <<'EOF'
[fix][frontend] reenviar el token CSRF en las escrituras (deuda 0009)

- leer la cookie csrftoken y mandarla como header X-CSRFToken en POST/PATCH/DELETE y en el refresh
- tests: header presente en POST/PATCH, ausente en GET y cuando no hay cookie
EOF
)"
```

---

## Task 7: Extraer `CampoTexto` a `components/ui/`

**Files:**
- Create: `frontend/src/components/ui/CampoTexto.tsx`
- Create: `frontend/src/components/ui/CampoTexto.test.tsx`
- Modify: `frontend/src/screens/Login.tsx:1-39` y sus usos

**Interfaces:**
- Consumes: nada de tareas previas.
- Produces: `CampoTexto({ etiqueta, tipo, valor, autoComplete, onChange })` y la constante `FOCO_VISIBLE`, ambas exportadas desde `frontend/src/components/ui/CampoTexto.tsx`. Las consumen las Tareas 9 y 10.

**Contexto:** el `TextField` local de `Login.tsx` se necesita en tres pantallas. `components/ui/` es plana y sin conocimiento de dominio (ADR 0020), y los componentes propios van en PascalCase español. **No** se migra a la clase `.foco-visible`: `Login.test.tsx` afirma sobre las utilidades de Tailwind y esa convergencia es un cambio aparte.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/components/ui/CampoTexto.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CampoTexto } from './CampoTexto'

describe('CampoTexto', () => {
  it('asocia el label al input y muestra foco visible', () => {
    render(
      <CampoTexto etiqueta="Correo" tipo="email" autoComplete="email" valor="" onChange={vi.fn()} />,
    )

    const input = screen.getByLabelText('Correo')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('type', 'email')
    expect(input).toHaveClass('focus-visible:outline-2')
    expect(input).toHaveClass('focus-visible:outline-primary')
  })

  it('propaga los cambios', () => {
    const onChange = vi.fn()
    render(
      <CampoTexto etiqueta="Correo" tipo="email" autoComplete="email" valor="" onChange={onChange} />,
    )

    fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'ana@ciencias.unam.mx' } })

    expect(onChange).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run (desde `frontend/`): `npx vitest run src/components/ui/CampoTexto.test.tsx`
Expected: FAIL — `Failed to resolve import "./CampoTexto"`.

- [ ] **Step 3: Crear el componente**

Crear `frontend/src/components/ui/CampoTexto.tsx`:

```tsx
import { useId, type ChangeEvent } from 'react'

/** Mismo outline que ya expresan `Boton.tsx`, `Login.tsx` y `Landing.tsx` con
 *  utilidades de Tailwind (herencia de la Decisión 8 del plan de login
 *  frontend). Converger todo eso sobre la clase `.foco-visible` de `index.css`
 *  es un cambio aparte, con sus propios tests — aquí solo se centraliza el
 *  string para no repetirlo en cada pantalla. */
export const FOCO_VISIBLE =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary'

interface CampoTextoProps {
  etiqueta: string
  tipo: string
  valor: string
  autoComplete: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
}

export function CampoTexto({ etiqueta, tipo, valor, autoComplete, onChange }: CampoTextoProps) {
  const id = useId()
  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="absolute -top-2 left-3 z-10 bg-background px-1 text-xs text-on-surface-variant"
      >
        {etiqueta}
      </label>
      <input
        id={id}
        type={tipo}
        value={valor}
        onChange={onChange}
        autoComplete={autoComplete}
        required
        className={`h-14 w-full rounded-md border border-outline bg-transparent px-3.5 text-sm text-on-surface focus:border-primary ${FOCO_VISIBLE}`}
      />
    </div>
  )
}
```

- [ ] **Step 4: Consumirlo desde `Login.tsx`**

En `frontend/src/screens/Login.tsx`, reemplazar las líneas 1-39 (imports, constante `FOCO_VISIBLE`, `TextFieldProps` y la función `TextField`) por:

```tsx
import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ApiError } from '../api/client'
import { Boton } from '../components/ui/Boton'
import { CampoTexto, FOCO_VISIBLE } from '../components/ui/CampoTexto'
import { PantallaCargando } from '../components/PantallaCargando'
```

y reemplazar estas dos líneas de dentro del `<form>`:

```tsx
        <TextField label="Correo" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField label="Contraseña" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
```

por estas:

```tsx
        <CampoTexto etiqueta="Correo" tipo="email" autoComplete="email" valor={email} onChange={(e) => setEmail(e.target.value)} />
        <CampoTexto etiqueta="Contraseña" tipo="password" autoComplete="current-password" valor={password} onChange={(e) => setPassword(e.target.value)} />
```

El resto del archivo (`export function Login()` hacia abajo) no cambia en esta tarea.

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/components/ui/CampoTexto.test.tsx src/screens/Login.test.tsx`
Expected: PASS.

- [ ] **Step 6: Suite, lint y build**

Run: `npm test && npm run lint && npm run build`
Expected: PASS (el build valida que ya no queden imports muertos de `useId`/`ChangeEvent` en `Login.tsx`).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ui/CampoTexto.tsx frontend/src/components/ui/CampoTexto.test.tsx frontend/src/screens/Login.tsx
git commit -s -m "$(cat <<'EOF'
[refactor][frontend] extraer CampoTexto del Login a components/ui/

- mover el campo con label flotante y la constante FOCO_VISIBLE a un componente reusable
- consumirlo desde Login.tsx sin cambiar su marcado ni sus clases
- test del componente: label asociado, foco visible y propagación de cambios
EOF
)"
```

---

## Task 8: Módulo `auth/password.ts`

**Files:**
- Create: `frontend/src/auth/password.ts`
- Create: `frontend/src/auth/password.test.ts`

**Interfaces:**
- Consumes: `apiPost` de `frontend/src/api/client.ts`.
- Produces:
  - `solicitarResetDePassword(email: string): Promise<RespuestaDetalle>`
  - `confirmarResetDePassword(datos: { uid: string; token: string; password1: string; password2: string }): Promise<RespuestaDetalle>`
  - `interface RespuestaDetalle { detail: string }`
  Las consumen las Tareas 9 y 10.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/auth/password.test.ts`:

```ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import * as client from '../api/client'
import { solicitarResetDePassword, confirmarResetDePassword } from './password'

describe('auth/password', () => {
  afterEach(() => vi.restoreAllMocks())

  it('solicitar manda el correo al endpoint de reset', async () => {
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({ detail: 'ok' })

    await solicitarResetDePassword('ana@ciencias.unam.mx')

    expect(apiPost).toHaveBeenCalledWith('/api/auth/password/reset/', {
      email: 'ana@ciencias.unam.mx',
    })
  })

  it('confirmar traduce los nombres de campo que espera dj-rest-auth', async () => {
    const apiPost = vi.spyOn(client, 'apiPost').mockResolvedValue({ detail: 'ok' })

    await confirmarResetDePassword({
      uid: 'MQ',
      token: 'abc-123',
      password1: 'NuevaClave123!',
      password2: 'NuevaClave123!',
    })

    expect(apiPost).toHaveBeenCalledWith('/api/auth/password/reset/confirm/', {
      uid: 'MQ',
      token: 'abc-123',
      new_password1: 'NuevaClave123!',
      new_password2: 'NuevaClave123!',
    })
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run (desde `frontend/`): `npx vitest run src/auth/password.test.ts`
Expected: FAIL — `Failed to resolve import "./password"`.

- [ ] **Step 3: Crear el módulo**

Crear `frontend/src/auth/password.ts`:

```ts
import { apiPost } from '../api/client'

/** Forma de la respuesta de los dos endpoints de reset de dj-rest-auth. */
export interface RespuestaDetalle {
  detail: string
}

/** `POST /api/auth/password/reset/`.
 *
 *  Responde 200 aunque el correo no exista o pertenezca a una cuenta que solo
 *  entra por Google: la respuesta es deliberadamente indistinguible (no
 *  enumeración). La UI no puede —ni debe— decir si el correo existe.
 *  Rate limit dedicado: 3/hour por IP; agotarlo devuelve 429. */
export function solicitarResetDePassword(email: string): Promise<RespuestaDetalle> {
  return apiPost<RespuestaDetalle>('/api/auth/password/reset/', { email })
}

/** `POST /api/auth/password/reset/confirm/`. Rate limit dedicado: 10/hour.
 *
 *  Se mandan las dos contraseñas tal cual las escribió el usuario: el backend
 *  valida que coincidan y que pasen los AUTH_PASSWORD_VALIDATORS, y devuelve el
 *  mensaje ya traducido. */
export function confirmarResetDePassword(datos: {
  uid: string
  token: string
  password1: string
  password2: string
}): Promise<RespuestaDetalle> {
  return apiPost<RespuestaDetalle>('/api/auth/password/reset/confirm/', {
    uid: datos.uid,
    token: datos.token,
    new_password1: datos.password1,
    new_password2: datos.password2,
  })
}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `npx vitest run src/auth/password.test.ts`
Expected: PASS.

- [ ] **Step 5: Lint y build**

Run: `npm run lint && npm run build`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/auth/password.ts frontend/src/auth/password.test.ts
git commit -s -m "$(cat <<'EOF'
[feat][frontend] agregar el módulo auth/password con las llamadas de reset

- solicitarResetDePassword y confirmarResetDePassword sobre apiPost
- tests de la traducción de campos hacia el contrato de dj-rest-auth
EOF
)"
```

---

## Task 9: Pantalla `ForgotPassword` + enlace desde `Login`

> **Requiere el OK del gate visual** (sección "Especificación ligera de componente", arriba).

**Files:**
- Create: `frontend/src/screens/ForgotPassword.tsx`
- Create: `frontend/src/screens/ForgotPassword.test.tsx`
- Modify: `frontend/src/App.tsx:1-26`
- Modify: `frontend/src/screens/Login.tsx` (botón "¿Olvidaste tu contraseña?")
- Test: `frontend/src/screens/Login.test.tsx`

**Interfaces:**
- Consumes: `CampoTexto`, `FOCO_VISIBLE` (Tarea 7); `solicitarResetDePassword` (Tarea 8); `Boton`; `ApiError`.
- Produces: `ForgotPassword` (export nombrado) y la ruta `/forgot-password`.

- [ ] **Step 1: Escribir los tests que fallan**

(a) Crear `frontend/src/screens/ForgotPassword.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ForgotPassword } from './ForgotPassword'
import * as password from '../auth/password'
import { ApiError } from '../api/client'

function montar() {
  render(
    <MemoryRouter initialEntries={['/forgot-password']}>
      <Routes>
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function llenarCorreo() {
  fireEvent.change(screen.getByLabelText('Correo'), {
    target: { value: 'ana@ciencias.unam.mx' },
  })
}

describe('ForgotPassword', () => {
  afterEach(() => vi.restoreAllMocks())

  it('el campo tiene label asociado y foco visible', () => {
    montar()

    const correo = screen.getByLabelText('Correo')
    expect(correo).toBeInTheDocument()
    expect(correo).toHaveClass('focus-visible:outline-primary')
  })

  it('manda el correo y muestra la confirmación sin revelar si la cuenta existe', async () => {
    const solicitar = vi
      .spyOn(password, 'solicitarResetDePassword')
      .mockResolvedValue({ detail: 'ok' })
    montar()

    llenarCorreo()
    fireEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    const confirmacion = await screen.findByRole('status')
    expect(confirmacion).toHaveTextContent('Si ese correo pertenece a una cuenta con contraseña')
    expect(solicitar).toHaveBeenCalledWith('ana@ciencias.unam.mx')
    expect(screen.queryByLabelText('Correo')).not.toBeInTheDocument()
  })

  it('con 429 muestra el mensaje de demasiadas solicitudes y deja el formulario', async () => {
    vi.spyOn(password, 'solicitarResetDePassword').mockRejectedValue(
      new ApiError(429, { detail: 'Request was throttled.' }),
    )
    montar()

    llenarCorreo()
    fireEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiadas solicitudes.')
    expect(screen.getByLabelText('Correo')).toBeInTheDocument()
  })

  it('con cualquier otro fallo muestra el error genérico', async () => {
    vi.spyOn(password, 'solicitarResetDePassword').mockRejectedValue(new Error('sin red'))
    montar()

    llenarCorreo()
    fireEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo enviar el correo.')
  })

  it('el botón de volver regresa al login', async () => {
    montar()

    fireEvent.click(screen.getByRole('button', { name: 'Volver' }))

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
```

(b) En `frontend/src/screens/Login.test.tsx`, agregar la ruta al `montar()` — reemplazar el bloque `<Routes>` por:

```tsx
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<p>pantalla home</p>} />
        <Route path="/forgot-password" element={<p>pantalla recuperar</p>} />
      </Routes>
```

y agregar este test dentro del `describe('Login', ...)`:

```tsx
  it('el botón de contraseña olvidada navega a /forgot-password', async () => {
    montar()

    fireEvent.click(screen.getByRole('button', { name: '¿Olvidaste tu contraseña?' }))

    expect(await screen.findByText('pantalla recuperar')).toBeInTheDocument()
  })
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run (desde `frontend/`): `npx vitest run src/screens/ForgotPassword.test.tsx src/screens/Login.test.tsx`
Expected: FAIL — `Failed to resolve import "./ForgotPassword"`, y el test del Login no encuentra "pantalla recuperar".

- [ ] **Step 3: Crear la pantalla**

Crear `frontend/src/screens/ForgotPassword.tsx`:

```tsx
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { solicitarResetDePassword } from '../auth/password'
import { Boton } from '../components/ui/Boton'
import { CampoTexto, FOCO_VISIBLE } from '../components/ui/CampoTexto'

export function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await solicitarResetDePassword(email)
      setEnviado(true)
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 429
          ? 'Demasiadas solicitudes. Espera una hora antes de volver a intentar.'
          : 'No se pudo enviar el correo. Intenta de nuevo.',
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex min-h-svh flex-col px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/login')}
        aria-label="Volver"
        className={`mb-8 flex h-9 w-9 items-center justify-center rounded-full text-on-background ${FOCO_VISIBLE}`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden>
          <path d="M15 19 L8 12 L15 5" />
        </svg>
      </button>

      <h1 className="mb-2 text-lg font-semibold text-on-background">Recuperar contraseña</h1>
      <p className="mb-8 text-sm text-on-surface-variant">
        Te enviamos un enlace para crear una contraseña nueva. Si entras con tu Correo Ciencias, usa
        el botón de Google en la pantalla de acceso.
      </p>

      {enviado ? (
        <p role="status" className="entrada-lista text-sm text-on-surface-variant">
          Si ese correo pertenece a una cuenta con contraseña, ya va en camino un enlace para
          restablecerla. Revisa tu bandeja de entrada y la carpeta de spam.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <CampoTexto
            etiqueta="Correo"
            tipo="email"
            autoComplete="email"
            valor={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          {error && (
            <p role="alert" className="entrada-lista text-sm text-error">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando}>
            Enviar enlace
          </Boton>
        </form>
      )}
    </main>
  )
}
```

- [ ] **Step 4: Conectar el botón del Login**

En `frontend/src/screens/Login.tsx`, reemplazar el botón sin handler por:

```tsx
        <button
          type="button"
          onClick={() => navigate('/forgot-password')}
          className={`self-end rounded-md text-xs font-medium text-primary ${FOCO_VISIBLE}`}
        >
          ¿Olvidaste tu contraseña?
        </button>
```

- [ ] **Step 5: Registrar la ruta**

En `frontend/src/App.tsx`, agregar el import debajo del de `Login`:

```tsx
import { ForgotPassword } from './screens/ForgotPassword'
```

y agregar la ruta inmediatamente debajo de `<Route path="/login" element={<Login />} />`:

```tsx
        <Route path="/forgot-password" element={<ForgotPassword />} />
```

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `npx vitest run src/screens/ForgotPassword.test.tsx src/screens/Login.test.tsx`
Expected: PASS.

- [ ] **Step 7: Suite, lint y build**

Run: `npm test && npm run lint && npm run build`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/screens/ForgotPassword.tsx frontend/src/screens/ForgotPassword.test.tsx frontend/src/screens/Login.tsx frontend/src/screens/Login.test.tsx frontend/src/App.tsx
git commit -s -m "$(cat <<'EOF'
[feat][frontend] agregar la pantalla de recuperar contraseña

- ForgotPassword en /forgot-password, con confirmación que no revela si la cuenta existe
- conectar el botón "¿Olvidaste tu contraseña?" del Login, que estaba sin handler
- tests: envío, mensaje de 429, error genérico y navegación de vuelta
EOF
)"
```

---

## Task 10: Pantalla `ResetPassword`

> **Requiere el OK del gate visual** (sección "Especificación ligera de componente", arriba).

**Files:**
- Create: `frontend/src/screens/ResetPassword.tsx`
- Create: `frontend/src/screens/ResetPassword.test.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `CampoTexto`, `FOCO_VISIBLE` (Tarea 7); `confirmarResetDePassword` (Tarea 8); `Boton`; `ApiError`.
- Produces: `ResetPassword` (export nombrado) y la ruta `/reset-password/:uid/:token`.

**Contexto:** el enlace que arma `atenea_password_reset_url_generator` termina en slash (`.../reset-password/{uid}/{key}/`); React Router 7 la matchea igual contra `/reset-password/:uid/:token` (su matcher tolera el slash final).

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/screens/ResetPassword.test.tsx`:

```tsx
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ResetPassword } from './ResetPassword'
import * as password from '../auth/password'
import { ApiError } from '../api/client'

function montar() {
  render(
    <MemoryRouter initialEntries={['/reset-password/MQ/abc-123/']}>
      <Routes>
        <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function llenar(nueva: string, confirmacion: string) {
  fireEvent.change(screen.getByLabelText('Contraseña nueva'), { target: { value: nueva } })
  fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { value: confirmacion } })
}

function enviar() {
  fireEvent.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))
}

describe('ResetPassword', () => {
  afterEach(() => vi.restoreAllMocks())

  it('los campos tienen label asociado y foco visible', () => {
    montar()

    expect(screen.getByLabelText('Contraseña nueva')).toHaveClass('focus-visible:outline-primary')
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
  })

  it('manda uid y token de la URL junto con las dos contraseñas', async () => {
    const confirmar = vi
      .spyOn(password, 'confirmarResetDePassword')
      .mockResolvedValue({ detail: 'ok' })
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()

    expect(await screen.findByRole('status')).toHaveTextContent('Tu contraseña quedó actualizada.')
    expect(confirmar).toHaveBeenCalledWith({
      uid: 'MQ',
      token: 'abc-123',
      password1: 'NuevaClave123!',
      password2: 'NuevaClave123!',
    })
  })

  it('si las contraseñas no coinciden avisa sin llamar al backend', async () => {
    const confirmar = vi.spyOn(password, 'confirmarResetDePassword')
    montar()

    llenar('NuevaClave123!', 'OtraClave123!')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent('Las contraseñas no coinciden.')
    expect(confirmar).not.toHaveBeenCalled()
  })

  it('con 400 en token muestra que el enlace ya no sirve', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockRejectedValue(
      new ApiError(400, { token: ['Invalid value'] }),
    )
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent('El enlace no es válido o ya expiró.')
  })

  it('con 400 de validación muestra el mensaje del backend', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockRejectedValue(
      new ApiError(400, { new_password2: ['Esta contraseña es demasiado corta.'] }),
    )
    montar()

    llenar('corta', 'corta')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Esta contraseña es demasiado corta.',
    )
  })

  it('con 429 muestra el mensaje de demasiados intentos', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockRejectedValue(
      new ApiError(429, { detail: 'Request was throttled.' }),
    )
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()

    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiados intentos.')
  })

  it('tras el éxito ofrece ir a iniciar sesión', async () => {
    vi.spyOn(password, 'confirmarResetDePassword').mockResolvedValue({ detail: 'ok' })
    montar()

    llenar('NuevaClave123!', 'NuevaClave123!')
    enviar()
    fireEvent.click(await screen.findByRole('button', { name: 'Ir a iniciar sesión' }))

    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run (desde `frontend/`): `npx vitest run src/screens/ResetPassword.test.tsx`
Expected: FAIL — `Failed to resolve import "./ResetPassword"`.

- [ ] **Step 3: Crear la pantalla**

Crear `frontend/src/screens/ResetPassword.tsx`:

```tsx
import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { confirmarResetDePassword } from '../auth/password'
import { Boton } from '../components/ui/Boton'
import { CampoTexto, FOCO_VISIBLE } from '../components/ui/CampoTexto'

const ERROR_GENERICO = 'No se pudo cambiar la contraseña. Intenta de nuevo.'

/** El backend responde 400 con `{campo: [mensaje]}` (validación de DRF). Los
 *  mensajes de contraseña ya vienen traducidos (LANGUAGE_CODE = "es-mx"), así
 *  que se muestran tal cual; `uid`/`token` sí se traducen a algo accionable. */
function mensajeDeError(err: unknown): string {
  if (!(err instanceof ApiError)) return ERROR_GENERICO
  if (err.status === 429) return 'Demasiados intentos. Espera una hora antes de volver a intentar.'
  const body = err.body as Record<string, string[] | undefined> | null
  if (body?.uid || body?.token) return 'El enlace no es válido o ya expiró. Solicita uno nuevo.'
  return body?.new_password2?.[0] ?? body?.new_password1?.[0] ?? ERROR_GENERICO
}

export function ResetPassword() {
  const navigate = useNavigate()
  const { uid = '', token = '' } = useParams<{ uid: string; token: string }>()
  const [password1, setPassword1] = useState('')
  const [password2, setPassword2] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [listo, setListo] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    // Se valida antes de llamar: el confirm tiene un cupo de 10/hour y no vale
    // la pena gastarlo en un error que el cliente puede ver por su cuenta.
    if (password1 !== password2) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setEnviando(true)
    try {
      await confirmarResetDePassword({ uid, token, password1, password2 })
      setListo(true)
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="flex min-h-svh flex-col px-6 py-6">
      <button
        type="button"
        onClick={() => navigate('/login')}
        aria-label="Volver"
        className={`mb-8 flex h-9 w-9 items-center justify-center rounded-full text-on-background ${FOCO_VISIBLE}`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden>
          <path d="M15 19 L8 12 L15 5" />
        </svg>
      </button>

      <h1 className="mb-2 text-lg font-semibold text-on-background">Nueva contraseña</h1>
      <p className="mb-8 text-sm text-on-surface-variant">
        Escríbela dos veces para confirmar que quedó como querías.
      </p>

      {listo ? (
        <div className="flex flex-col gap-6">
          <p role="status" className="entrada-lista text-sm text-on-surface-variant">
            Tu contraseña quedó actualizada.
          </p>
          <Boton type="button" onClick={() => navigate('/login')}>
            Ir a iniciar sesión
          </Boton>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <CampoTexto
            etiqueta="Contraseña nueva"
            tipo="password"
            autoComplete="new-password"
            valor={password1}
            onChange={(e) => setPassword1(e.target.value)}
          />
          <CampoTexto
            etiqueta="Confirmar contraseña"
            tipo="password"
            autoComplete="new-password"
            valor={password2}
            onChange={(e) => setPassword2(e.target.value)}
          />

          {error && (
            <p role="alert" className="entrada-lista text-sm text-error">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando}>
            Cambiar contraseña
          </Boton>
        </form>
      )}
    </main>
  )
}
```

- [ ] **Step 4: Registrar la ruta**

En `frontend/src/App.tsx`, agregar el import debajo del de `ForgotPassword`:

```tsx
import { ResetPassword } from './screens/ResetPassword'
```

y agregar la ruta inmediatamente debajo de `<Route path="/forgot-password" element={<ForgotPassword />} />`:

```tsx
        <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `npx vitest run src/screens/ResetPassword.test.tsx`
Expected: PASS (7 tests).

- [ ] **Step 6: Suite, lint y build**

Run: `npm test && npm run lint && npm run build`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/screens/ResetPassword.tsx frontend/src/screens/ResetPassword.test.tsx frontend/src/App.tsx
git commit -s -m "$(cat <<'EOF'
[feat][frontend] agregar la pantalla de nueva contraseña

- ResetPassword en /reset-password/:uid/:token, la ruta que genera el correo de reset
- traducir los 400 del backend: enlace vencido, validación de contraseña y 429
- tests: envío, contraseñas distintas sin request, cada caso de error y salida al login
EOF
)"
```

---

## Task 11: Documentación — ADR, deuda y contrato de API

**Files:**
- Create: `docs/decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md`
- Create: `docs/technical-debt/0022-correo-de-reset-con-template-default.md`
- Create: `docs/technical-debt/0023-blacklist-sin-purga-de-tokens-vencidos.md`
- Modify: `docs/technical-debt/0007-logout-sin-invalidacion-refresh-token.md`
- Modify: `docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md`
- Modify: `docs/technical-debt/README.md`
- Modify: `docs/development/api-frontend.md`

**Interfaces:**
- Consumes: todo lo implementado en las Tareas 1-10.
- Produces: nada de código.

- [ ] **Step 1: Escribir el ADR**

Crear `docs/decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md`:

```markdown
# 0029 — Recuperación de contraseña y endurecimiento de la sesión

**Status:** Accepted
**Date:** 2026-08-19

## Context

Tres piezas del bloque Auth del sprint, agrupadas porque comparten código (`accounts/`) y contexto: el pentest de staging del 2026-08-18 y el SMTP de Workspace ya configurado ([ADR 0028](0028-envio-correo-smtp-cuenta-dedicada.md)).

1. Las cuentas que no entran por Google (staff, SAE, asesores no-alumnos) no tenían forma de recuperar su contraseña. El backend de reset de `dj-rest-auth` ya funcionaba end-to-end —había un test pasando— pero no estaba expuesto en el SPA ni acotado a las cuentas a las que aplica.
2. [Deuda 0007](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md): el logout no invalidaba el refresh token en el servidor.
3. [Deuda 0009](../technical-debt/0009-sin-csrf-en-cookie-jwt.md): sin CSRF explícito sobre el JWT en cookie. El pentest lo reprodujo en vivo: una escritura autenticada solo con la cookie, sin ningún token CSRF, era aceptada.

## Decision

**1. El reset se acota a cuentas con contraseña usable.** No se agrega un campo de "tipo de cuenta" a `User`: la distinción es de comportamiento (los alumnos se dan de alta sin contraseña y entran por Google; las cuentas con contraseña se crean desde el admin) y `has_usable_password()` es el criterio verificable. `accounts.serializers.PasswordResetSerializer.validate_email` vacía `reset_form.users` en vez de levantar un error, para caer en el mismo camino que un correo desconocido: la respuesta queda indistinguible y no filtra ni qué cuentas existen ni de qué tipo son. Como efecto lateral se apaga `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS`: ese correo de allauth invita a un auto-registro que Atenea no tiene, y además reventaba con `NoReverseMatch` porque `allauth.urls` no está incluido en `config/urls.py`.

**2. El flujo de reset tiene scopes de throttle propios**, `password_reset` (3/hour) y `password_reset_confirm` (10/hour), sobre `CloudflareScopedRateThrottle`. Antes compartía el scope `dj_rest_auth` (5/min) con el login: quien golpeara reset consumía el cupo de quien intenta entrar, y al revés. Son dos scopes y no uno porque pedir el enlace dispara un correo y es rarísimo en operación normal, mientras que confirmarlo no manda nada y el usuario puede fallar los validadores de contraseña varias veces seguidas. Se montan como subclases delgadas en `accounts/views.py`, antes del `include` de `dj_rest_auth.urls` — el mismo patrón que ya usaba `AteneaLoginView`.

**3. El logout invalida el refresh token**, instalando `rest_framework_simplejwt.token_blacklist`. La lógica ya vivía en `dj_rest_auth.views.LogoutView.logout()`, condicionada únicamente a que la app estuviera en `INSTALLED_APPS`. Consecuencia de contrato: a partir de aquí el logout **exige** el refresh —en el body si `JWT_AUTH_HTTPONLY=False` (dev), en la cookie si es `True` (prod)— o responde 401.

**4. Las escrituras autenticadas por cookie exigen CSRF** (`JWT_AUTH_COOKIE_USE_CSRF = True`, solo en `prod.py`). `SameSite=Lax` no bastaba: se evalúa sobre el dominio registrable, así que un subdominio hermano bajo el mismo dominio padre sigue siendo "same-site" y podía postear con la cookie adjunta. Para que el SPA tenga qué reenviar, las vistas de login, de Google y de `/api/auth/user/` se decoran con `ensure_csrf_cookie`: Django solo emite la cookie `csrftoken` si alguna vista llama `get_token(request)`, y el SPA se sirve desde nginx, así que su primer contacto con Django es una de esas tres. El `GET /api/auth/user/` que el SPA hace al montar cubre además la transición: una sesión abierta desde antes del cambio recibe su cookie sin tener que volver a entrar (GET es método seguro y nunca se rechaza por CSRF).

## Consequences

- Las cuentas con contraseña tienen recuperación real, con dos pantallas nuevas en el SPA (`/forgot-password`, `/reset-password/:uid/:token`) y el botón del login por fin conectado.
- Un refresh token robado deja de servir en cuanto el usuario cierra sesión; se cierra la deuda 0007.
- El vector CSRF confirmado en el pentest queda cerrado, con test de regresión; se cierra la deuda 0009.
- Todo cliente nuevo que escriba contra la API en prod tiene que reenviar `X-CSRFToken`. Ya no basta con la cookie.
- Aparecen dos ítems de deuda nuevos: [0022](../technical-debt/0022-correo-de-reset-con-template-default.md) (el correo usa el template default de allauth) y [0023](../technical-debt/0023-blacklist-sin-purga-de-tokens-vencidos.md) (las tablas del blacklist crecen sin purga).

## Alternatives considered

- **Agregar un campo `tipo_cuenta` a `User`.** Explícito y consultable, pero duplica un estado que ya existe (`has_usable_password()`) y hay que mantenerlo sincronizado con cada alta. Se descarta hasta que exista un caso que necesite distinguir tipos que `has_usable_password()` no distinga.
- **Rechazar con 400 el reset de una cuenta Google-only**, con un mensaje que diga "esa cuenta entra con Google". Es más amable, pero convierte el endpoint en un oráculo de enumeración: distingue correo inexistente de correo existente y además revela el tipo de cuenta.
- **Un solo scope de throttle para todo el flujo de reset.** Más simple, pero fallar dos veces el validador de contraseña dejaría al usuario sin poder pedir un enlace nuevo durante una hora.
- **Rotar el refresh token (`ROTATE_REFRESH_TOKENS = True`) en vez de instalar el blacklist.** Acota la ventana de un token robado, pero no resuelve el caso pedido —"cerré sesión, el token ya no debe servir"— y obliga al SPA a reescribir su token guardado en cada refresh.
- **`JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED = True`.** Exigiría CSRF también en el login, que es justo el request donde el SPA todavía no tiene cookie. Se descarta.
```

- [ ] **Step 2: Crear los dos ítems de deuda nuevos**

Crear `docs/technical-debt/0022-correo-de-reset-con-template-default.md`:

```markdown
# 0022 — El correo de recuperación usa el template default de allauth

**Estado:** Activa
**Origen:** [ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md)

## Qué se simplificó

El correo que recibe quien pide recuperar su contraseña se arma con el template default de allauth (`account/email/password_reset_key*`), sin branding de la SAE, sin remitente con nombre propio y con la redacción genérica de la librería. Lo único que este proyecto sobreescribe es la URL del enlace (`atenea_password_reset_url_generator`, en `accounts/serializers.py`), para que apunte al SPA y no a una vista de Django que no existe.

## Por qué era razonable

Nadie pidió contenido de correo, y personalizarlo obliga a decidir tono, firma y qué hacer con el resto de los correos transaccionales que ya manda Atenea (notificaciones de asesorías) — es una iteración de contenido, no un bloqueante del flujo. El mensaje default es funcional y ya sale en español (`LANGUAGE_CODE = "es-mx"`).

## Señal de revisión

Que la SAE pida branding en los correos, que un usuario reporte el correo como confuso o sospechoso de phishing, o que se agregue un segundo correo transaccional de cuenta (verificación, bienvenida) y convenga fijar un template base compartido.
```

Crear `docs/technical-debt/0023-blacklist-sin-purga-de-tokens-vencidos.md`:

```markdown
# 0023 — Las tablas del blacklist de tokens crecen sin purga

**Estado:** Activa
**Origen:** [ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md)

## Qué se simplificó

Con `rest_framework_simplejwt.token_blacklist` instalado, cada login escribe una fila en `OutstandingToken` y cada logout una en `BlacklistedToken`. `simplejwt` trae el comando `flushexpiredtokens` para borrar las que ya expiraron, pero no está agendado: no hay ninguna tarea periódica en `celery-beat` que lo corra.

## Por qué era razonable

El proyecto todavía no tiene ningún `beat_schedule` definido (`celery-beat` corre sin tareas periódicas propias), así que agendar esto implicaba estrenar esa infraestructura por una tabla que, con el volumen actual —la SAE de una facultad, refresh de 7 días—, crece del orden de unas pocas filas por usuario y semana. Es medible y reversible en cualquier momento.

## Señal de revisión

Cuando se agende la primera tarea periódica real en `celery-beat` (el cierre automático de sesiones vencidas de la [deuda 0004](0004-sin-cierre-automatico-recordatorios.md) es la candidata natural): agregar `flushexpiredtokens` diario en el mismo commit. Antes de eso, si `token_blacklist_outstandingtoken` pasa de unos cuantos cientos de miles de filas.
```

- [ ] **Step 3: Cerrar las deudas 0007 y 0009**

En `docs/technical-debt/0007-logout-sin-invalidacion-refresh-token.md`, reemplazar la línea `**Estado:** Activa` por:

```markdown
**Estado:** Resuelta — 2026-08-19 ([ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md))
```

y agregar al final del archivo:

```markdown
## Cómo se resolvió (2026-08-19)

Se instaló `rest_framework_simplejwt.token_blacklist`: la lógica de invalidación ya vivía en `dj_rest_auth.views.LogoutView.logout()`, condicionada solo a que la app estuviera en `INSTALLED_APPS`. Consecuencia de contrato: el logout ahora **exige** el refresh token —en el body en dev, en la cookie `atenea-refresh-token` en prod— o responde 401; `frontend/src/auth/AuthContext.tsx` lo manda en dev. Cubierto por `accounts/tests/test_auth.py::LogoutBlacklistTests`. Queda abierta la [deuda 0023](0023-blacklist-sin-purga-de-tokens-vencidos.md): las tablas del blacklist no se purgan.
```

En `docs/technical-debt/0009-sin-csrf-en-cookie-jwt.md`, reemplazar la línea `**Estado:** Activa` por:

```markdown
**Estado:** Resuelta — 2026-08-19 ([ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md))
```

y agregar al final del archivo:

```markdown
## Cómo se resolvió (2026-08-19)

`JWT_AUTH_COOKIE_USE_CSRF = True` en `config/settings/prod.py`: toda escritura autenticada por cookie exige el header `X-CSRFToken`. Para que el SPA tenga qué reenviar, las vistas de login, de Google y de `/api/auth/user/` se decoran con `ensure_csrf_cookie` (Django solo emite la cookie `csrftoken` si alguna vista llama `get_token(request)`), y `frontend/src/api/client.ts` la lee y la manda en todo `POST`/`PATCH`/`DELETE`. El POST del pentest quedó como test de regresión en `accounts/tests/test_auth.py::CsrfEnCookieJwtTests`.
```

- [ ] **Step 4: Actualizar el índice de deuda**

En `docs/technical-debt/README.md`:

(a) Borrar de la sección "Activa" las dos líneas de 0007 y 0009.

(b) Agregar al final de la sección "Activa":

```markdown
- [0022 — El correo de recuperación usa el template default de allauth](0022-correo-de-reset-con-template-default.md)
- [0023 — Las tablas del blacklist de tokens crecen sin purga](0023-blacklist-sin-purga-de-tokens-vencidos.md)
```

(c) Agregar al final de la sección "Resuelta":

```markdown
- [0007 — Logout no invalida el refresh token en el servidor](0007-logout-sin-invalidacion-refresh-token.md) — resuelta 2026-08-19
- [0009 — Sin protección CSRF explícita en el transporte de JWT por cookie](0009-sin-csrf-en-cookie-jwt.md) — resuelta 2026-08-19
```

- [ ] **Step 5: Actualizar el contrato de API**

En `docs/development/api-frontend.md`:

(a) Reemplazar el párrafo completo de la sección `### Logout` por:

```markdown
`POST /api/auth/logout/` limpia el estado del lado del cliente (cookie si aplica) **y manda el refresh token al blacklist** — desde 2026-08-19 está instalada `rest_framework_simplejwt.token_blacklist` ([ADR 0029](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md), cierra la [deuda 0007](../technical-debt/0007-logout-sin-invalidacion-refresh-token.md)). Un refresh usado después del logout es rechazado con `401` por `/api/auth/token/refresh/`.

El refresh token es obligatorio en el request o el logout responde `401` sin invalidar nada:

- **Dev:** body `{"refresh": "<token>"}`.
- **Prod:** body vacío `{}`; la vista lo toma de la cookie `atenea-refresh-token`.
```

(b) Reemplazar las dos filas de `password/reset` de la tabla de "Otros endpoints de `accounts`" por:

```markdown
| `POST` | `/api/auth/password/reset/` | `AllowAny` | `{email}` → siempre `200`, con el mismo cuerpo si el correo no existe **o si la cuenta solo entra por Google** (no manda correo en ninguno de esos dos casos). El link generado apunta a `{FRONTEND_URL}/reset-password/:uid/:token` — el SPA la sirve en `screens/ResetPassword.tsx`. Throttle propio: `3/hour` por IP → `429` |
| `POST` | `/api/auth/password/reset/confirm/` | `AllowAny` | `{uid, token, new_password1, new_password2}`. Errores `400`: `{"token": [...]}`/`{"uid": [...]}` si el enlace venció, `{"new_password1"/"new_password2": [...]}` si la contraseña no pasa los validadores. Throttle propio: `10/hour` por IP |
```

(c) Agregar, inmediatamente después del blockquote de "Estado (2026-08-01)" de la sección "Transporte del JWT":

```markdown
#### CSRF en prod (desde 2026-08-19)

`JWT_AUTH_COOKIE_USE_CSRF = True` en prod: todo `POST`/`PATCH`/`DELETE` que se autentique **por cookie** exige además el header `X-CSRFToken`, o responde `403 {"detail": "CSRF Failed: ..."}`. Cierra la [deuda 0009](../technical-debt/0009-sin-csrf-en-cookie-jwt.md), confirmada explotable en el pentest de staging.

- La cookie `csrftoken` la emiten `/api/auth/login/`, `/api/auth/google/` y `GET /api/auth/user/` (decoradas con `ensure_csrf_cookie`). No es `httpOnly`: el SPA tiene que poder leerla.
- El SPA la reenvía desde `frontend/src/api/client.ts` (`leerCookie('csrftoken')` → header `X-CSRFToken`) en todo método que no sea seguro.
- Los métodos seguros (`GET`/`HEAD`/`OPTIONS`) nunca se rechazan, y un request autenticado con `Authorization: Bearer` tampoco: `enforce_csrf` solo corre cuando la autenticación vino de la cookie (por eso dev no cambia).
```

(d) En la sección "Ver también", reemplazar la última línea por:

```markdown
- [ADR 0029 — Recuperación de contraseña y endurecimiento de la sesión](../decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md)
- [Deuda técnica](../technical-debt/README.md) — en particular 0001 (sin calendario académico), 0006 (sin paginación), 0022 (correo de reset con template default), 0023 (blacklist sin purga)
```

- [ ] **Step 6: Verificar que no quedan enlaces rotos**

Run (desde la raíz del repo): `grep -rn "0007-logout-sin-invalidacion-refresh-token\|0009-sin-csrf-en-cookie-jwt\|0029-recuperacion-password" docs/ | grep -v "^docs/superpowers/"`
Expected: solo apariciones en `docs/technical-debt/README.md`, los dos archivos de deuda, el ADR 0029 y `docs/development/api-frontend.md` — ningún enlace apuntando a un archivo inexistente.

Run: `ls docs/decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md docs/technical-debt/0022-correo-de-reset-con-template-default.md docs/technical-debt/0023-blacklist-sin-purga-de-tokens-vencidos.md`
Expected: los tres archivos existen.

- [ ] **Step 7: Commit**

```bash
git add docs/decisions/0029-recuperacion-password-y-endurecimiento-de-sesion.md docs/technical-debt/ docs/development/api-frontend.md
git commit -s -m "$(cat <<'EOF'
[docs] registrar ADR 0029 y cerrar las deudas 0007 y 0009

- ADR 0029: reset acotado, throttle dedicado, blacklist de logout y CSRF en cookie
- marcar resueltas 0007 y 0009; abrir 0022 (template de correo default) y 0023 (blacklist sin purga)
- actualizar api-frontend.md: contrato de logout, de reset y sección de CSRF en prod
EOF
)"
```

- [ ] **Step 8: Verificación final de todo el plan**

Run (desde `backend/`): `uv run manage.py test`
Expected: PASS.

Run (desde `frontend/`): `npm test && npm run lint && npm run build`
Expected: PASS.

Run (desde la raíz): `git status`
Expected: working tree limpio, 11 commits nuevos sobre `dev`.
