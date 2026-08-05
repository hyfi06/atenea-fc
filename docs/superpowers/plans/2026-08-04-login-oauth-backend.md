# Backend — Login con id_token (ADR 0019), perfil/rol en la API (deuda 0010) y superficie nueva de Asesorías — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en `backend/` las tres piezas que las specs del paso 2 y del paso 3 ya decidieron y que hoy no existen: el transporte de login con `id_token` de Google ([ADR 0019](../../decisions/0019-transporte-login-google-id-token.md)), la exposición de perfil/rol y de los campos de cancelación en la API ([deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md)), y los cuatro endpoints nuevos de Asesorías que el rediseño de vistas ([spec del paso 3](../specs/2026-08-04-revision-vistas-asesorias-design.md)) dio por requisito de entrada.

**Architecture:** Tres bloques independientes sobre código existente, sin migraciones de esquema salvo ninguna (todos los campos ya existen en los modelos). (1) `accounts/` cambia el transporte social: un `GoogleOAuth2Adapter` propio que sabe construir un `SocialToken` a partir de un `id_token` sin `access_token`, más un `GoogleLoginSerializer` que exige `id_token` y traduce el `OAuth2Error` de la verificación criptográfica de allauth a un `400`. (2) `accounts/serializers.py` gana un `UserDetailsSerializer` propio que expone roles y perfiles derivados de los `OneToOneField` inversos ya existentes, y `asesorias/serializers.py` gana los campos de cancelación y de nombre que el frontend hoy suple con workarounds. (3) `asesorias/` gana tres métodos de modelo nuevos (donde vive la lógica de negocio, según ADR 0016) y cuatro acciones de viewset delgadas que los invocan y traducen `ValidationError` a HTTP, siguiendo exactamente el patrón de ADR 0017.

**Tech Stack:** Django 6, Django REST Framework 3.17, `dj-rest-auth` 7.2+, `django-allauth` 65.18+, `djangorestframework-simplejwt` 5.5+, `PyJWT` (transitiva de allauth), PostgreSQL 16, `uv` para tooling de Python.

## Global Constraints

- **No se toca `frontend/`.** Este plan es exclusivamente backend. El frontend consume estos cambios en los pasos 8 y 9 del ledger (`docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`).
- **Cero variables de entorno nuevas.** `GOOGLE_OAUTH_CLIENT_ID` (ya existente) es la única variable funcionalmente necesaria para verificar `audience`; `GOOGLE_OAUTH_CLIENT_SECRET` se mantiene configurada pero deja de ejercitarse en esta ruta (ADR 0019).
- **Cero dependencias nuevas.** Todo lo que se usa (`allauth.socialaccount.internal.jwtkit`, `PyJWT`, `cryptography`) ya está instalado.
- **Cero migraciones de base de datos.** `motivo_cancelacion`, `cancelado_por`, `Disponibilidad.activa`, `RegistroAsesor.materias` y todos los perfiles ya existen en los modelos. Si algún paso genera una migración, algo salió mal — revisar antes de seguir.
- **No se reabren decisiones ya tomadas.** El transporte (`id_token`, no `access_token`, no Authorization Code) está fijado por ADR 0019. El storage/transporte del JWT propio de Atenea (split dev/prod) está fijado por la decisión 2 de ADR 0018 y no cambia. El logout sin invalidación de refresh token (deuda 0007) y el CSRF en cookie JWT (deuda 0009) no se tocan.
- **TDD estricto, commits atómicos.** Cada task escribe el test primero, lo corre para verlo fallar, implementa lo mínimo, lo corre para verlo pasar, y comitea. Es el patrón que este repo ya sigue (ver commit `d6ade66`).
- **Convención de commits del repo** (`docs/development/commit-conventions.md`, ADR 0007): `[type][scope] resumen` en la primera línea, bullets de detalle en el cuerpo, y `Signed-off-by` generado con `git commit -s`. Tipos usados aquí: `feat`, `fix`, `refactor`, `docs`.
- **Comando de tests:** siempre desde `backend/`, con `uv run manage.py test ...`. Los tests corren bajo `config.settings.dev` (el default de `manage.py`).
- **Formato de errores existente:** las reglas de negocio que viven en el modelo se traducen a `400 {"detail": ["mensaje"]}` — una **lista**, incluso con un solo mensaje (es lo que produce `exc.messages` de `DjangoValidationError`). Los errores de validación de serializer producen `{"campo": ["mensaje"]}` o `{"non_field_errors": [...]}`. No unificar esto aquí; está documentado así en `docs/development/api-frontend.md`.
- **Restricción de DRF a tener presente en todo el plan:** un campo declarado explícitamente en el cuerpo del serializer (`x = serializers.CharField(...)`) **no** puede además listarse en `Meta.read_only_fields` — DRF lanza un `AssertionError` al instanciarlo ("Cannot both declare the field ... and include it in read_only_fields"). Los campos declarados se hacen read-only con `read_only=True` (o siendo `SerializerMethodField`, que ya lo es). Solo los campos que vienen del modelo sin declaración explícita van en `read_only_fields`.

---

## File Structure

**`backend/accounts/` — transporte de login y perfil del usuario autenticado**

- **Modificar** `backend/accounts/adapters.py` — hoy contiene los dos adapters de allauth que bloquean el autoregistro (`AccountAdapter`, `SocialAccountAdapter`). Gana un tercer adapter, `GoogleIdTokenAdapter`, subclase de `GoogleOAuth2Adapter` que sobreescribe `parse_token`. Es el archivo cuya responsabilidad ya es "adapters de allauth de este proyecto"; no se crea un archivo nuevo.
- **Modificar** `backend/accounts/views.py` — `GoogleLoginView.adapter_class` pasa de `GoogleOAuth2Adapter` a `GoogleIdTokenAdapter`.
- **Modificar** `backend/accounts/serializers.py` — `GoogleLoginSerializer.validate` exige `id_token` en vez de `access_token` y captura `OAuth2Error`. Se agrega `UserDetailsSerializer` (perfil/rol del usuario autenticado).
- **Modificar** `backend/accounts/models.py` — `User` gana la propiedad `nombre_completo` (sin campo nuevo, sin migración).
- **Modificar** `backend/config/settings/base.py` — `REST_AUTH` gana `USER_DETAILS_SERIALIZER`.
- **Modificar** `backend/accounts/tests/test_auth.py` — los tests de `GoogleLoginTests` pasan a `id_token`; se agrega el rechazo de `access_token`-solo y una clase nueva que ejercita la verificación real de firma/`audience`.
- **Crear** `backend/accounts/tests/test_user_details.py` — tests de `GET /api/auth/user/` con perfil/rol. Archivo aparte porque su sujeto es la forma de datos del usuario, no el flujo de autenticación de `test_auth.py`.

**`backend/asesorias/` — superficie nueva**

- **Modificar** `backend/asesorias/models.py` — `RegistroAsesor.quitar_materia()`, `Disponibilidad.sesiones_futuras()`, `Disponibilidad.desactivar()`. Toda la lógica de negocio vive aquí (ADR 0016); las vistas solo traducen errores a HTTP.
- **Modificar** `backend/asesorias/serializers.py` — `AsesoriaSerializer` gana los campos de cancelación y de nombre; se agrega `SesionFuturaSerializer` y `DesactivarDisponibilidadSerializer`; `AgregarMateriaSerializer` se renombra a `MateriaDelRegistroSerializer` (lo usan tanto agregar como quitar).
- **Modificar** `backend/asesorias/views.py` — cuatro acciones nuevas y el filtro de semestre.
- **Modificar** `backend/asesorias/tests/test_registro_asesor.py` y `backend/asesorias/tests/test_disponibilidad.py` — tests de los métodos de modelo nuevos.
- **Modificar** `backend/asesorias/tests/test_api_registro.py`, `test_api_disponibilidad.py`, `test_api_asesoria.py` — tests de las rutas nuevas, cada uno en el archivo del recurso al que pertenece la ruta.

**`docs/` — documentación (última task)**

- **Modificar** `docs/development/api-frontend.md`, `docs/decisions/0016-asesorias-academicas.md`, `docs/decisions/0017-asesorias-academicas-api.md`, `docs/decisions/0019-transporte-login-google-id-token.md`, `docs/technical-debt/0006-sin-paginacion-listados.md`, `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md`, `docs/technical-debt/README.md`.

---

## Decisiones de diseño de API tomadas en este plan

Las specs fijaron el *qué*; estas son las decisiones de *forma exacta* que este plan toma para ser ejecutable sin volver a diseño. Cada una lleva su razón en el task correspondiente.

| # | Decisión | Task |
|---|---|---|
| 1 | El adapter propio vive en `accounts/adapters.py` como `GoogleIdTokenAdapter`, no en un módulo nuevo. | 1 |
| 2 | `OAuth2Error` se traduce a `400 {"detail": ["El id_token de Google no es válido."]}`; hoy solo se captura `HTTPError`. | 2 |
| 3 | `GET /api/auth/user/` expone `roles` como lista de claves estables (`"alumno"`, `"asesor_academico"`, `"academico"`) más un objeto por perfil (`perfil_alumno`, `perfil_asesor_academico`, `perfil_academico`), `null` si no aplica. | 3 |
| 4 | Se agregan también `apellido1`/`apellido2`/`nombre_completo` al payload de usuario, todos read-only. | 3 |
| 5 | `roles` incluye `"asesor_academico"` aunque `PerfilAsesorAcademico.activo` sea `False`, para no divergir de la permission class `EsAsesorAcademico`, que solo comprueba existencia; `activo` se expone dentro del objeto anidado. | 3 |
| 6 | `AsesoriaSerializer` gana `cancelado_por_rol` (`"alumno" \| "asesor" \| "otro" \| null`) además del `cancelado_por` crudo. | 4 |
| 7 | El nombre del alumno se resuelve con un campo hermano read-only (`alumno_nombre`), no expandiendo `alumno` a objeto — no rompe a ningún consumidor actual. Se agrega también `asesor_nombre` (simétrico). | 5 |
| 8 | `GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/` responde un sobre `{"total": n, "sesiones": [...]}`, no un array plano. | 6 |
| 9 | "Futura" = `estado="agendada"` **y** la sesión aún no ha comenzado (comparación fecha+hora contra `timezone.localtime()`), no simplemente `fecha >= hoy`. | 6 |
| 10 | Las dos opciones del modal de desactivar se sirven con **un solo** endpoint: `POST /api/asesorias/disponibilidades/{id}/desactivar/ {cancelar_sesiones, motivo}`. | 7 |
| 11 | Si se cancelan sesiones con `motivo` vacío, el backend usa el texto por defecto `"El asesor dio de baja este horario."`. | 7 |
| 12 | Quitar materia es `POST /api/asesorias/registros/{id}/materias/quitar/ {materia_id}`, no `DELETE`, para no habilitar el método `DELETE` en un viewset que deliberadamente lo excluye. | 8 |
| 13 | El filtro de historial es `GET /api/asesorias/asesorias/?semestre=20262`, permisivo: un semestre desconocido devuelve `[]`, no `400`. | 9 |
| 14 | Se agrega `GET /api/asesorias/asesorias/semestres/` (array plano de claves, orden descendente) para que el frontend pueda construir los subtabs sin cargar el historial completo. | 9 |

---

### Task 1: Login con Google acepta `id_token` (y solo `id_token`)

Implementa la decisión central de [ADR 0019](../../decisions/0019-transporte-login-google-id-token.md). Hoy `GoogleLoginSerializer.validate` (`backend/accounts/serializers.py:27-29`) rechaza cualquier petición sin `access_token`, y `OAuth2Adapter.parse_token` de allauth hace `data["access_token"]` sin fallback — por eso hace falta un adapter propio además del cambio de serializer.

**Files:**
- Modify: `backend/accounts/adapters.py`
- Modify: `backend/accounts/serializers.py:12-55`
- Modify: `backend/accounts/views.py`
- Test: `backend/accounts/tests/test_auth.py`

**Interfaces:**
- Consumes: `GoogleOAuth2Adapter` (`allauth.socialaccount.providers.google.views`), `SocialLoginSerializer` (`dj_rest_auth.registration.serializers`), `SocialToken` (`allauth.socialaccount.models`).
- Produces:
  - `accounts.adapters.GoogleIdTokenAdapter` — subclase de `GoogleOAuth2Adapter`; `parse_token(self, data: dict) -> SocialToken` construye el token desde `data["id_token"]`. La Task 2 la usa para resolver `app.client_id` en los tests.
  - `accounts.serializers.GoogleLoginSerializer` — mismo nombre de clase, contrato nuevo: `POST /api/auth/google/` requiere `{"id_token": "<jwt>"}`.

- [ ] **Step 1: Escribir los tests que fijan el contrato nuevo — RED**

En `backend/accounts/tests/test_auth.py`, reemplazar el método helper `_post_google_login` de la clase `GoogleLoginTests` (hoy en las líneas 38-41, posteando `access_token`) por estos dos helpers, y agregar los dos tests nuevos al final de esa misma clase (después de `test_sets_cookies_when_httponly_configured`):

```python
    def _post_google_login(self):
        return self.client.post(
            "/api/auth/google/", {"id_token": "fake-token"}, format="json"
        )

    def _post_google_login_con_access_token(self):
        return self.client.post(
            "/api/auth/google/", {"access_token": "fake-token"}, format="json"
        )

    @patch.object(GoogleOAuth2Adapter, "complete_login")
    def test_rechaza_access_token_sin_id_token(self, mock_complete_login):
        """El transporte de access_token queda cerrado explícitamente (ADR 0019)."""
        user = User.objects.create_user("legacy@ciencias.unam.mx")
        mock_complete_login.side_effect = _complete_login_as(user.email)

        response = self._post_google_login_con_access_token()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_complete_login.assert_not_called()

    def test_rechaza_peticion_sin_ningun_token(self):
        response = self.client.post("/api/auth/google/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

No hay imports nuevos: `patch`, `GoogleOAuth2Adapter`, `status`, `User` y `_complete_login_as` ya existen en ese archivo (líneas 7-34).

Nota sobre el `@patch.object(GoogleOAuth2Adapter, ...)` que usan los tests existentes: sigue funcionando después de este task aunque la vista pase a usar `GoogleIdTokenAdapter`, porque la subclase no sobreescribe `complete_login` y Python resuelve el atributo parcheado en la clase base por herencia. No hay que cambiar el target del patch.

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `uv run manage.py test accounts.tests.test_auth.GoogleLoginTests -v 2`

Expected: FAIL en 3 de los 5 tests.
- `test_rejects_unprovisioned_email` → falla: hoy el serializer contesta `400` por "access_token is required", así que el `assertEqual(400)` **pasa por la razón equivocada**; el `assertEqual(User.objects.count(), 0)` también pasa. Este test puede quedar en verde en este punto — no es señal de nada; el que importa es el siguiente.
- `test_connects_provisioned_email` → FAIL con `400 != 200` y `{"non_field_errors": ["Incorrect input. access_token is required."]}` en `response.data`.
- `test_sets_cookies_when_httponly_configured` → FAIL con `400 != 200`, misma causa.
- `test_rechaza_access_token_sin_id_token` → FAIL: hoy `access_token` **sí** se acepta, así que la respuesta es `200` y además `complete_login` sí se llamó.
- `test_rechaza_peticion_sin_ningun_token` → PASS ya (hoy también da `400`). Es un test de regresión, no de cambio.

- [ ] **Step 3: Agregar el adapter que construye el `SocialToken` desde el `id_token`**

En `backend/accounts/adapters.py`, reemplazar el archivo completo por:

```python
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return False


class GoogleIdTokenAdapter(GoogleOAuth2Adapter):
    """Adapter de Google para el transporte de ID token (ADR 0019).

    `OAuth2Adapter.parse_token` (allauth) hace `data["access_token"]` sin
    fallback, así que no se puede usar tal cual cuando el cliente manda
    únicamente un `id_token`. Se sobreescribe solo eso: el resto del flujo
    —`complete_login` -> `_decode_id_token` -> `_verify_and_decode`, que es
    donde se verifica firma, issuer, expiración y `audience=app.client_id`—
    se hereda sin cambios de `GoogleOAuth2Adapter`.
    """

    def parse_token(self, data):
        return SocialToken(token=data["id_token"])
```

- [ ] **Step 4: Apuntar la vista al adapter nuevo**

En `backend/accounts/views.py`, reemplazar el archivo completo por:

```python
from dj_rest_auth.registration.views import SocialLoginView

from .adapters import GoogleIdTokenAdapter
from .serializers import GoogleLoginSerializer


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleIdTokenAdapter
    serializer_class = GoogleLoginSerializer
```

- [ ] **Step 5: Exigir `id_token` en el serializer**

En `backend/accounts/serializers.py`, reemplazar el cuerpo del método `GoogleLoginSerializer.validate` (líneas 13-55) por:

```python
    def validate(self, attrs):
        view = self.context.get("view")
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(_("View is not defined, pass it as a context variable"))

        adapter_class = getattr(view, "adapter_class", None)
        if not adapter_class:
            raise serializers.ValidationError(_("Define adapter_class in view"))

        adapter = adapter_class(request)
        app = adapter.get_provider().app

        # ADR 0019: el único transporte soportado es el ID token (OIDC). El
        # access_token de OAuth se rechaza a propósito: su ruta de validación
        # en allauth (_fetch_user_info) no verifica que el token se haya
        # emitido para el client_id de Atenea.
        id_token = attrs.get("id_token")
        if not id_token:
            raise serializers.ValidationError(_("Incorrect input. id_token is required."))

        social_token = adapter.parse_token({"id_token": id_token})
        social_token.app = app

        try:
            login = self.get_social_login(adapter, app, social_token, response={"id_token": id_token})
            ret = complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))

        if isinstance(ret, HttpResponseBadRequest):
            raise serializers.ValidationError(ret.content)

        if not login.is_existing:
            raise serializers.ValidationError(
                _("No existe una cuenta para este correo. Contacta a la SAE."),
            )

        attrs["user"] = login.account.user

        return attrs
```

No cambia ningún import del archivo.

- [ ] **Step 6: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth.GoogleLoginTests -v 2`

Expected: PASS — los 5 tests.

- [ ] **Step 7: Correr la suite completa del backend**

Run: `uv run manage.py test`

Expected: PASS — todo. Ningún otro test del repo ejercita `/api/auth/google/`.

- [ ] **Step 8: Commit**

```bash
git add backend/accounts/adapters.py backend/accounts/views.py \
        backend/accounts/serializers.py backend/accounts/tests/test_auth.py
git commit -s -m "[feat][backend] aceptar id_token de Google en el login social" \
  -m "- Nuevo GoogleIdTokenAdapter (accounts/adapters.py): subclase de
    GoogleOAuth2Adapter que sobreescribe parse_token para construir el
    SocialToken desde data['id_token'], porque OAuth2Adapter.parse_token
    de allauth hace data['access_token'] sin fallback.
- GoogleLoginView usa el adapter nuevo; GoogleLoginSerializer exige
    id_token y ya no acepta access_token (ADR 0019).
- TDD: los tests de GoogleLoginTests se movieron a postear id_token y
    fallaron con 400 contra el código viejo; se agregó
    test_rechaza_access_token_sin_id_token para cerrar explícitamente el
    transporte descartado."
```

---

### Task 2: La verificación real de firma y `audience` responde 400, no 500

Los tests de la Task 1 mockean `complete_login`, así que **no** ejercitan la verificación criptográfica — que es justamente el motivo de ADR 0019. Este task la ejercita de verdad y arregla el defecto que sale a la luz al hacerlo: `_verify_and_decode` levanta `OAuth2Error` (`allauth.socialaccount.providers.oauth2.client`), que el serializer no captura, así que un `id_token` inválido revienta como error no manejado en vez de dar `400`.

Los tests firman su propio JWT con HS256 y parchean únicamente `allauth.socialaccount.internal.jwtkit.fetch_key` — el único punto que hace red (descargar las llaves públicas de Google). Todo lo demás (`issuer`, `exp`, `audience`, `verify_jti`) corre real. **Verificado empíricamente contra este repo antes de escribir el plan:** con `fetch_key` parcheado a `("HS256", <clave>)`, `jwtkit.verify_and_decode` decodifica un token con `aud` correcto y levanta `OAuth2Error("Invalid id_token")` con `aud` incorrecto.

**Files:**
- Modify: `backend/accounts/serializers.py`
- Test: `backend/accounts/tests/test_auth.py`

**Interfaces:**
- Consumes: `accounts.adapters.GoogleIdTokenAdapter` (Task 1) para resolver `app.client_id` desde los settings dentro del test.
- Produces: contrato de error de `POST /api/auth/google/` — cualquier `id_token` que no pase la verificación de allauth responde `400 {"detail": ["El id_token de Google no es válido."]}`.

- [ ] **Step 1: Escribir los tests de verificación real — RED**

Agregar al final de `backend/accounts/tests/test_auth.py`:

```python
import time

import jwt
from allauth.socialaccount.internal import jwtkit
from django.test import RequestFactory

from accounts.adapters import GoogleIdTokenAdapter

# Clave simétrica de prueba: los tests firman su propio id_token y parchean
# jwtkit.fetch_key (el único punto que haría red contra las llaves públicas
# de Google) para devolverla. Todo lo demás de la verificación —issuer,
# expiración y sobre todo audience, que es la razón de ser de ADR 0019—
# corre con el código real de allauth, sin mock.
LLAVE_DE_PRUEBA = "llave-simetrica-solo-para-tests-de-id-token-de-google"


def _id_token_de_prueba(*, audience, email):
    return jwt.encode(
        {
            "iss": "https://accounts.google.com",
            "aud": audience,
            "sub": "1234567890",
            "email": email,
            "email_verified": True,
            "given_name": "Nombre",
            "family_name": "Apellido",
            "exp": int(time.time()) + 600,
        },
        LLAVE_DE_PRUEBA,
        algorithm="HS256",
    )


class GoogleIdTokenVerificacionTests(APITestCase):
    """Ejercita la verificación real de allauth, sin mockear complete_login."""

    @staticmethod
    def _client_id_configurado():
        adapter = GoogleIdTokenAdapter(RequestFactory().get("/"))
        return adapter.get_provider().app.client_id

    @patch.object(jwtkit, "fetch_key", return_value=("HS256", LLAVE_DE_PRUEBA))
    def test_id_token_con_audience_correcto_autentica(self, _fetch_key):
        user = User.objects.create_user("audiencia-ok@ciencias.unam.mx")
        token = _id_token_de_prueba(
            audience=self._client_id_configurado(), email=user.email
        )

        response = self.client.post(
            "/api/auth/google/", {"id_token": token}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertTrue(
            SocialAccount.objects.filter(user=user, provider="google").exists()
        )

    @patch.object(jwtkit, "fetch_key", return_value=("HS256", LLAVE_DE_PRUEBA))
    def test_id_token_con_audience_ajeno_devuelve_400(self, _fetch_key):
        """El caso que el transporte viejo de access_token no cubría."""
        user = User.objects.create_user("audiencia-mala@ciencias.unam.mx")
        token = _id_token_de_prueba(
            audience="client-id-de-otra-aplicacion", email=user.email
        )

        response = self.client.post(
            "/api/auth/google/", {"id_token": token}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            SocialAccount.objects.filter(user=user, provider="google").exists()
        )

    @patch.object(jwtkit, "fetch_key", return_value=("HS256", LLAVE_DE_PRUEBA))
    def test_id_token_expirado_devuelve_400(self, _fetch_key):
        user = User.objects.create_user("expirado@ciencias.unam.mx")
        token = jwt.encode(
            {
                "iss": "https://accounts.google.com",
                "aud": self._client_id_configurado(),
                "sub": "1234567890",
                "email": user.email,
                "email_verified": True,
                "exp": int(time.time()) - 60,
            },
            LLAVE_DE_PRUEBA,
            algorithm="HS256",
        )

        response = self.client.post(
            "/api/auth/google/", {"id_token": token}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

Notas para quien implementa:
- `LLAVE_DE_PRUEBA` es una constante **de módulo**, no un atributo de clase, porque el decorador `@patch.object(..., return_value=(..., LLAVE_DE_PRUEBA))` se evalúa al definir la clase, cuando `self` todavía no existe.
- El `id_token` firmado no lleva `kid` en el header; no importa, porque `fetch_key` (el único que lo lee) está parcheado.
- El `client_id` real sale de `.env` (`GOOGLE_OAUTH_CLIENT_ID`, `dev-placeholder-client-id` en el entorno de desarrollo de este repo), por eso se lee dinámicamente en vez de hardcodearse: el test debe pasar en cualquier entorno.

- [ ] **Step 2: Correr los tests y confirmar que fallan donde corresponde**

Run: `uv run manage.py test accounts.tests.test_auth.GoogleIdTokenVerificacionTests -v 2`

Expected:
- `test_id_token_con_audience_correcto_autentica` → **PASS ya**, sin tocar código de producción. Es la contraprueba de que el arnés de test es válido: si este fallara, el problema estaría en el test (firma, claims, o el `client_id` leído), no en el serializer. No sigas al Step 3 si este no está en verde.
- `test_id_token_con_audience_ajeno_devuelve_400` → **FAIL**, pero no con un `assertEqual`: el test aborta con `allauth.socialaccount.providers.oauth2.client.OAuth2Error: Invalid id_token` propagándose desde la vista, porque el `except HTTPError` del serializer no lo cubre.
- `test_id_token_expirado_devuelve_400` → **FAIL** por la misma excepción.

- [ ] **Step 3: Capturar `OAuth2Error` en el serializer**

En `backend/accounts/serializers.py`, agregar el import (después de `from allauth.socialaccount.helpers import complete_social_login`):

```python
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
```

y reemplazar el bloque `try/except` de `GoogleLoginSerializer.validate` por:

```python
        try:
            login = self.get_social_login(adapter, app, social_token, response={"id_token": id_token})
            ret = complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))
        except OAuth2Error:
            # allauth levanta OAuth2Error cuando el id_token no pasa la
            # verificación de firma, issuer, expiración o audience
            # (_verify_and_decode -> jwtkit.verify_and_decode). Sin este
            # except, un token inválido revienta como error no manejado en
            # vez de dar el 400 que fija la spec de login.
            raise serializers.ValidationError(_("El id_token de Google no es válido."))
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test accounts.tests.test_auth -v 2`

Expected: PASS — las 4 clases del archivo (`GoogleLoginTests`, `GoogleIdTokenVerificacionTests`, `PasswordResetLoginFlowTests`, `ProdSettingsJWTCookieTests`, `CookieBasedLoginTests`).

- [ ] **Step 5: Commit**

```bash
git add backend/accounts/serializers.py backend/accounts/tests/test_auth.py
git commit -s -m "[fix][backend] traducir id_token invalido de Google a 400, no a error no manejado" \
  -m "- GoogleLoginSerializer captura OAuth2Error (firma/issuer/expiracion/
    audience invalidos) y responde 400, no una excepcion propagada.
- Tests nuevos que ejercitan la verificacion real de allauth sin mockear
    complete_login: solo se parchea jwtkit.fetch_key (la unica llamada de
    red, a las llaves publicas de Google); audience, issuer y expiracion se
    verifican con el codigo real.
- Cubre el caso concreto que motivo ADR 0019: un id_token emitido para el
    client_id de otra aplicacion ya no autentica."
```

---

### Task 3: `GET /api/auth/user/` expone perfil y rol en una sola llamada

Resuelve el workaround 1 de la [deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md): hoy el frontend detecta el rol sondeando `GET /api/asesorias/registros/` y leyendo 200 vs 403 (`frontend/src/auth/rol.ts`), lo que no escala a más de un rol. La spec del paso 3 decidió explícitamente resolverlo aquí en vez de agregar un segundo sondeo gemelo.

El serializer que dj-rest-auth usa para `GET /api/auth/user/` es el mismo que embebe en la clave `user` de las respuestas de `POST /api/auth/login/` y `POST /api/auth/google/` (`JWTSerializer.get_user`), así que este cambio hace que el rol llegue con el login mismo, sin una llamada extra.

**Decisiones de forma tomadas aquí:**
- `roles` es una lista de claves estables (`"alumno"`, `"asesor_academico"`, `"academico"`), no booleanos sueltos: agregar un rol futuro no cambia la forma del payload.
- Cada perfil se expone como objeto anidado o `null`. Se prefiere sobre aplanar campos con prefijo porque el frontend ya distingue "no tiene el perfil" de "lo tiene vacío".
- `"asesor_academico"` aparece en `roles` aunque `PerfilAsesorAcademico.activo` sea `False`, porque `EsAsesorAcademico` (la permission class que decide el acceso real) solo comprueba `hasattr`. Divergir haría que el frontend ocultara una pantalla a la que el backend sí da acceso. `activo` viaja dentro del objeto para que la UI pueda matizarlo.
- Se agregan `apellido1`, `apellido2` y `nombre_completo`: existen en el modelo `User` desde siempre y `docs/development/api-frontend.md` ya documenta su ausencia como un hueco ("si el frontend necesita nombre completo, hoy no está disponible vía API"). Van read-only — la identidad la aprovisiona la SAE; solo `first_name` sigue siendo editable, como hoy.
- `nombre_completo` cae a `email` si las tres partes del nombre están vacías, para que la UI nunca renderice una cadena vacía.

**Files:**
- Modify: `backend/accounts/models.py`
- Modify: `backend/accounts/serializers.py`
- Modify: `backend/config/settings/base.py:142-148`
- Test: `backend/accounts/tests/test_user_details.py` (crear)

**Interfaces:**
- Consumes: los `related_name` inversos ya existentes — `User.perfil_alumno` (`accounts.PerfilAlumno`), `User.perfil_academico` (`accounts.PerfilAcademico`), `User.perfil_asesor_academico` (`asesorias.PerfilAsesorAcademico`).
- Produces:
  - `accounts.models.User.nombre_completo` — propiedad `str`. La Task 5 la consume desde `asesorias/serializers.py`.
  - `accounts.serializers.UserDetailsSerializer` — registrada en `REST_AUTH["USER_DETAILS_SERIALIZER"]`. Payload:
    ```json
    {
      "pk": 1,
      "email": "alguien@ciencias.unam.mx",
      "first_name": "Ana",
      "apellido1": "López",
      "apellido2": "Ruiz",
      "nombre_completo": "Ana López Ruiz",
      "roles": ["alumno"],
      "perfil_alumno": {"id": 3, "numero_cuenta": "312345678", "carrera": 5, "carrera_nombre": "Actuaría", "generacion": 2023},
      "perfil_academico": null,
      "perfil_asesor_academico": null
    }
    ```

- [ ] **Step 1: Escribir los tests — RED**

Crear `backend/accounts/tests/test_user_details.py`:

```python
from accounts.models import PerfilAcademico, PerfilAlumno, User
from asesorias.models import PerfilAsesorAcademico
from carreras.models import Area, Carrera
from rest_framework.test import APITestCase


class UserDetailsApiTests(APITestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)

    def test_usuario_sin_perfiles_reporta_roles_vacios(self):
        user = User.objects.create_user(email="nadie@ciencias.unam.mx", password="x")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], [])
        self.assertIsNone(response.data["perfil_alumno"])
        self.assertIsNone(response.data["perfil_academico"])
        self.assertIsNone(response.data["perfil_asesor_academico"])

    def test_alumno_reporta_su_rol_y_su_perfil(self):
        user = User.objects.create_user(
            email="alumna@ciencias.unam.mx", password="x", first_name="Ana",
        )
        user.apellido1 = "López"
        user.apellido2 = "Ruiz"
        user.save()
        perfil = PerfilAlumno.objects.create(
            user=user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], ["alumno"])
        self.assertEqual(response.data["nombre_completo"], "Ana López Ruiz")
        self.assertEqual(response.data["apellido1"], "López")
        self.assertEqual(
            response.data["perfil_alumno"],
            {
                "id": perfil.id,
                "numero_cuenta": "312345678",
                "carrera": self.carrera.id,
                "carrera_nombre": "Carrera Test",
                "generacion": 2023,
            },
        )

    def test_asesor_academico_reporta_ambos_roles(self):
        user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="12345")
        perfil_asesor = PerfilAsesorAcademico.objects.create(user=user, area=self.area)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(response.data["roles"]), ["academico", "asesor_academico"])
        self.assertEqual(
            response.data["perfil_asesor_academico"],
            {
                "id": perfil_asesor.id,
                "area": self.area.id,
                "area_nombre": "Area test",
                "activo": True,
            },
        )
        self.assertEqual(response.data["perfil_academico"]["numero_trabajador"], "12345")

    def test_asesor_inactivo_conserva_el_rol_y_reporta_activo_false(self):
        """El rol sigue el criterio de la permission class EsAsesorAcademico,
        que solo comprueba que el perfil exista."""
        user = User.objects.create_user(email="inactivo@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=user, numero_trabajador="54321")
        PerfilAsesorAcademico.objects.create(user=user, area=self.area, activo=False)
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertIn("asesor_academico", response.data["roles"])
        self.assertFalse(response.data["perfil_asesor_academico"]["activo"])

    def test_nombre_completo_cae_al_email_si_no_hay_nombre(self):
        user = User.objects.create_user(email="sin-nombre@ciencias.unam.mx", password="x")
        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/user/")

        self.assertEqual(response.data["nombre_completo"], "sin-nombre@ciencias.unam.mx")

    def test_los_campos_de_perfil_no_son_escribibles(self):
        user = User.objects.create_user(email="rw@ciencias.unam.mx", password="x")
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            "/api/auth/user/",
            {"first_name": "Nuevo", "apellido1": "Hackeado", "roles": ["academico"]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Nuevo")
        self.assertEqual(user.apellido1, "")
        self.assertEqual(response.data["roles"], [])

    def test_el_login_devuelve_los_roles_en_el_body(self):
        """El mismo serializer alimenta la clave 'user' de /api/auth/login/,
        así que el SPA obtiene el rol sin una segunda llamada."""
        user = User.objects.create_user(email="login@ciencias.unam.mx", password="ClaveSegura123!")
        PerfilAlumno.objects.create(
            user=user, numero_cuenta="312345679", carrera=self.carrera, generacion=2024,
        )

        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "ClaveSegura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["roles"], ["alumno"])
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `uv run manage.py test accounts.tests.test_user_details -v 2`

Expected: FAIL — los 7 tests, con `KeyError: 'roles'` / `KeyError: 'nombre_completo'` al indexar `response.data`, porque hoy el payload es solo `{pk, email, first_name}`.

- [ ] **Step 3: Agregar `nombre_completo` al modelo `User`**

En `backend/accounts/models.py`, dentro de la clase `User`, agregar justo antes de `def __str__`:

```python
    @property
    def nombre_completo(self):
        partes = [self.first_name, self.apellido1, self.apellido2]
        return " ".join(p for p in partes if p) or self.email
```

Es una propiedad, no un campo: no genera migración.

- [ ] **Step 4: Escribir el `UserDetailsSerializer`**

En `backend/accounts/serializers.py`, agregar el import (junto a los demás de `dj_rest_auth`):

```python
from dj_rest_auth.serializers import UserDetailsSerializer as BaseUserDetailsSerializer
```

y agregar al final del archivo:

```python
class UserDetailsSerializer(BaseUserDetailsSerializer):
    """Perfil y rol del usuario autenticado en una sola llamada (deuda 0010).

    Alimenta tanto `GET /api/auth/user/` como la clave `user` del body de
    `POST /api/auth/login/` y `POST /api/auth/google/`, así que el SPA
    conoce el rol desde el login mismo, sin sondear endpoints por rol.
    """

    nombre_completo = serializers.CharField(read_only=True)
    roles = serializers.SerializerMethodField()
    perfil_alumno = serializers.SerializerMethodField()
    perfil_academico = serializers.SerializerMethodField()
    perfil_asesor_academico = serializers.SerializerMethodField()

    class Meta(BaseUserDetailsSerializer.Meta):
        fields = (
            "pk",
            "email",
            "first_name",
            "apellido1",
            "apellido2",
            "nombre_completo",
            "roles",
            "perfil_alumno",
            "perfil_academico",
            "perfil_asesor_academico",
        )
        # Solo los campos NO declarados arriba pueden ir aquí; DRF falla con
        # AssertionError si un campo declarado explícitamente aparece también
        # en read_only_fields. Los declarados ya son read-only por su cuenta
        # (SerializerMethodField, o read_only=True).
        read_only_fields = ("pk", "email", "apellido1", "apellido2")

    def get_roles(self, obj):
        roles = []
        if hasattr(obj, "perfil_alumno"):
            roles.append("alumno")
        if hasattr(obj, "perfil_academico"):
            roles.append("academico")
        # Criterio deliberado: el rol depende de que el perfil exista, no de
        # que esté activo — es exactamente lo que comprueba la permission
        # class EsAsesorAcademico. `activo` viaja dentro del objeto anidado.
        if hasattr(obj, "perfil_asesor_academico"):
            roles.append("asesor_academico")
        return roles

    def get_perfil_alumno(self, obj):
        perfil = getattr(obj, "perfil_alumno", None)
        if perfil is None:
            return None
        return {
            "id": perfil.id,
            "numero_cuenta": perfil.numero_cuenta,
            "carrera": perfil.carrera_id,
            "carrera_nombre": perfil.carrera.nombre,
            "generacion": perfil.generacion,
        }

    def get_perfil_academico(self, obj):
        perfil = getattr(obj, "perfil_academico", None)
        if perfil is None:
            return None
        return {"id": perfil.id, "numero_trabajador": perfil.numero_trabajador}

    def get_perfil_asesor_academico(self, obj):
        perfil = getattr(obj, "perfil_asesor_academico", None)
        if perfil is None:
            return None
        return {
            "id": perfil.id,
            "area": perfil.area_id,
            "area_nombre": perfil.area.nombre,
            "activo": perfil.activo,
        }
```

Nota: `getattr(obj, "perfil_alumno", None)` devuelve `None` en vez de levantar `RelatedObjectDoesNotExist` porque `getattr` con default atrapa el `AttributeError` del que esa excepción hereda — es el mismo idioma que `hasattr` ya usa `asesorias/permissions.py`.

- [ ] **Step 5: Registrar el serializer en los settings**

En `backend/config/settings/base.py`, reemplazar el bloque `REST_AUTH` (líneas 142-148) por:

```python
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
```

- [ ] **Step 6: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test accounts.tests.test_user_details -v 2`

Expected: PASS — los 7 tests.

- [ ] **Step 7: Correr la suite completa y verificar que nada se rompió**

Run: `uv run manage.py test`

Expected: PASS. Presta atención a `accounts.tests.test_auth.PasswordResetLoginFlowTests` y `CookieBasedLoginTests`, que leen `response.data["email"]` de `/api/auth/user/` — ese campo sigue presente, así que deben pasar sin cambios.

- [ ] **Step 8: Commit**

```bash
git add backend/accounts/models.py backend/accounts/serializers.py \
        backend/config/settings/base.py backend/accounts/tests/test_user_details.py
git commit -s -m "[feat][backend] exponer perfil y rol del usuario en /api/auth/user/" \
  -m "- UserDetailsSerializer propio, registrado en REST_AUTH: agrega roles
    (alumno/academico/asesor_academico), un objeto por perfil (o null),
    apellido1/apellido2 y nombre_completo, todos de solo lectura.
- User.nombre_completo (propiedad, sin migracion): first_name + apellidos,
    con el email como respaldo si no hay nombre.
- Resuelve el workaround 1 de la deuda tecnica 0010: el SPA ya no necesita
    sondear /api/asesorias/registros/ y leer 200 vs 403 para saber el rol.
    El mismo serializer alimenta la clave 'user' del body de login, asi que
    el rol llega con el login mismo."
```

---

### Task 4: `AsesoriaSerializer` expone el motivo y el autor de la cancelación

Resuelve el tercer punto de la [deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md): `Asesoria.motivo_cancelacion` y `Asesoria.cancelado_por` existen en el modelo y `Asesoria.cancelar()` los llena (`backend/asesorias/models.py:140-148`), pero `AsesoriaSerializer.Meta.fields` no los incluye, así que el panel de "asesoría cancelada" del detalle no puede mostrar el motivo.

**Decisión de forma tomada aquí:** además de los dos campos que pide la deuda, se agrega `cancelado_por_rol`. `cancelado_por` es un id de `User`, y ni el alumno ni el asesor conocen el id de `User` de la contraparte (el asesor solo ve `PerfilAlumno.id`), así que el id crudo no permite renderizar "canceló el alumno" vs "canceló el asesor" — que es la única pregunta que la UI hace con ese dato. `cancelado_por_rol` la responde sin exponer identidades adicionales.

**Files:**
- Modify: `backend/asesorias/serializers.py:68-114`
- Test: `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**
- Consumes: `Asesoria.cancelar(usuario, motivo="")` — ya existente, sin cambios.
- Produces: `AsesoriaSerializer` con tres campos nuevos de solo lectura: `motivo_cancelacion` (`str`), `cancelado_por` (`int | null`, id de `User`), `cancelado_por_rol` (`"alumno" | "asesor" | "otro" | null`).

- [ ] **Step 1: Escribir los tests — RED**

Agregar a `backend/asesorias/tests/test_api_asesoria.py`, dentro de la clase `CicloDeVidaAsesoriaApiTests` ya existente (al final de su cuerpo):

```python
    def test_cancelacion_expone_motivo_y_rol_de_quien_cancelo(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/",
            {"motivo": "Se empalmó con un examen."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["motivo_cancelacion"], "Se empalmó con un examen.")
        self.assertEqual(response.data["cancelado_por"], self.alumno_user.id)
        self.assertEqual(response.data["cancelado_por_rol"], "alumno")

    def test_el_asesor_ve_el_motivo_de_una_cancelacion_del_alumno(self):
        self.asesoria.cancelar(usuario=self.alumno_user, motivo="Ya no lo necesito.")

        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["motivo_cancelacion"], "Ya no lo necesito.")
        self.assertEqual(response.data["cancelado_por_rol"], "alumno")

    def test_cancelacion_del_asesor_reporta_rol_asesor(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.post(
            f"/api/asesorias/asesorias/{self.asesoria.id}/cancelar/",
            {"motivo": "Junta académica."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cancelado_por_rol"], "asesor")

    def test_sesion_no_cancelada_reporta_campos_vacios(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.data["motivo_cancelacion"], "")
        self.assertIsNone(response.data["cancelado_por"])
        self.assertIsNone(response.data["cancelado_por_rol"])
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `uv run manage.py test asesorias.tests.test_api_asesoria.CicloDeVidaAsesoriaApiTests -v 2`

Expected: FAIL — los 4 tests nuevos con `KeyError: 'motivo_cancelacion'` (o `'cancelado_por_rol'`); los tests preexistentes de esa clase siguen en PASS.

- [ ] **Step 3: Agregar los campos al serializer**

En `backend/asesorias/serializers.py`, reemplazar la clase `AsesoriaSerializer` (líneas 68-114) por:

```python
class AsesoriaSerializer(serializers.ModelSerializer):
    cancelado_por_rol = serializers.SerializerMethodField()

    class Meta:
        model = Asesoria
        fields = [
            "id", "alumno", "disponibilidad", "materia", "carrera", "fecha", "hora_inicio",
            "formato", "ubicacion", "liga_virtual", "estado", "asistio", "notas",
            "motivo_cancelacion", "cancelado_por", "cancelado_por_rol", "creado_en",
        ]
        read_only_fields = [
            "id", "alumno", "carrera", "hora_inicio", "formato", "ubicacion", "liga_virtual",
            "estado", "asistio", "notas", "motivo_cancelacion", "cancelado_por", "creado_en",
        ]
        # DRF genera un UniqueTogetherValidator automático a partir del
        # UniqueConstraint condicional de Asesoria, lo que rechazaría el
        # doble-booking con 400 antes de tocar la base de datos. Se
        # desactiva a propósito: ADR 0017 decisión 8 exige que la condición
        # de carrera se resuelva en la base de datos y se traduzca a 409,
        # no que se prevenga con un chequeo optimista en la vista.
        validators = []

    def get_cancelado_por_rol(self, obj):
        """Quién canceló, en términos de la sesión — no de la identidad.

        `cancelado_por` es un id de User, y ninguna de las dos partes conoce
        el id de User de la otra (el asesor solo ve PerfilAlumno.id), así que
        el id crudo no alcanza para renderizar el panel de cancelación.
        """
        if not obj.cancelado_por_id:
            return None
        if obj.cancelado_por_id == obj.alumno.user_id:
            return "alumno"
        if obj.cancelado_por_id == obj.disponibilidad.registro.asesor.user_id:
            return "asesor"
        return "otro"

    def validate(self, attrs):
        disponibilidad = attrs["disponibilidad"]
        alumno = self.context["request"].user.perfil_alumno
        instance = Asesoria(
            alumno=alumno,
            disponibilidad=disponibilidad,
            materia=attrs["materia"],
            carrera=alumno.carrera,
            fecha=attrs["fecha"],
            hora_inicio=disponibilidad.hora_inicio,
            formato=disponibilidad.formato,
            ubicacion=disponibilidad.ubicacion,
            liga_virtual=disponibilidad.liga_virtual,
        )
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        attrs["carrera"] = alumno.carrera
        attrs["hora_inicio"] = disponibilidad.hora_inicio
        attrs["formato"] = disponibilidad.formato
        attrs["ubicacion"] = disponibilidad.ubicacion
        attrs["liga_virtual"] = disponibilidad.liga_virtual
        return attrs

    def create(self, validated_data):
        validated_data["alumno"] = self.context["request"].user.perfil_alumno
        return Asesoria.objects.create(**validated_data)
```

`cancelado_por_rol` está declarado explícitamente, así que **no** va en `read_only_fields` (un `SerializerMethodField` ya es read-only y DRF falla si aparece en ambos lugares).

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test asesorias.tests.test_api_asesoria -v 2`

Expected: PASS — toda la clase, incluidos los 4 tests nuevos.

- [ ] **Step 5: Correr la suite completa**

Run: `uv run manage.py test`

Expected: PASS. Los campos agregados son de salida; ningún test existente afirma la lista exacta de claves de la respuesta.

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/tests/test_api_asesoria.py
git commit -s -m "[feat][backend] exponer motivo y autor de cancelacion en AsesoriaSerializer" \
  -m "- motivo_cancelacion y cancelado_por pasan a Meta.fields (existian en
    el modelo desde la Fase 1 y cancelar() los llena, pero el serializer
    no los exponia).
- cancelado_por_rol nuevo (alumno/asesor/otro/null): el id crudo de User
    no sirve para renderizar el panel de cancelacion porque ninguna de las
    dos partes conoce el id de User de la otra.
- Cierra el tercer punto de la deuda tecnica 0010."
```

---

### Task 5: El asesor ve el nombre del alumno (y el alumno el del asesor)

Resuelve el workaround 2 de la [deuda técnica 0010](../../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md): hoy la UI del asesor muestra `"Alumno #<id>"` porque `AsesoriaSerializer.alumno` es un id plano y no hay ruta para resolver el nombre asociado.

**Decisión de alcance tomada aquí — se incluye, no se difiere.** Dos razones concretas: (1) sin esto la deuda 0010 no puede cerrarse, y este plan es el que la spec del paso 3 designó para resolverla; (2) la señal de revisión de la propia deuda dice que el caso simétrico (el alumno viendo el nombre de su asesor) reabre el mismo hueco en Fase 2 — resolver una sola dirección garantiza una segunda pasada sobre el mismo serializer por el mismo motivo, que es exactamente lo que la deuda advierte ("dos parches iguales es la señal de que ya no es aceptable posponerlo"). Por eso se agregan las dos direcciones en el mismo cambio: es el mismo mecanismo (`User.nombre_completo`, ya construido en la Task 3) aplicado a los dos extremos de la relación.

**Decisión de forma:** `alumno` sigue siendo un id plano y se agrega un campo hermano `alumno_nombre`, en vez de expandir `alumno` a objeto anidado. Expandirlo cambiaría el tipo de una clave que el frontend ya lee, y la deuda 0010 registra justamente esa compatibilidad como la razón por la que el cambio se separó ("si expandir `alumno` a un objeto rompe compatibilidad con lo que ya consume el body de creación"). Un campo hermano no rompe a nadie.

No hay riesgo de fuga de datos: `AsesoriaViewSet.get_queryset` ya restringe cada sesión a su alumno o a su asesor, y `EsDuenoDeLaAsesoria` cubre las acciones de detalle.

**Files:**
- Modify: `backend/asesorias/serializers.py`
- Modify: `backend/asesorias/views.py:118-130`
- Test: `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**
- Consumes: `accounts.models.User.nombre_completo` (Task 3).
- Produces: `AsesoriaSerializer` con `alumno_nombre` (`str`) y `asesor_nombre` (`str`), ambos read-only.

- [ ] **Step 1: Escribir los tests — RED**

Agregar a `backend/asesorias/tests/test_api_asesoria.py` una clase nueva, al final del archivo:

```python
class NombresEnAsesoriaApiTests(AsesoriaApiTestsBase):
    def setUp(self):
        super().setUp()
        self.alumno_user.first_name = "Ana"
        self.alumno_user.apellido1 = "López"
        self.alumno_user.apellido2 = "Ruiz"
        self.alumno_user.save()
        self.asesor_user.first_name = "Beto"
        self.asesor_user.apellido1 = "Martínez"
        self.asesor_user.save()
        self.asesoria = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes,
            hora_inicio=self.disponibilidad.hora_inicio, formato=self.disponibilidad.formato,
            liga_virtual=self.disponibilidad.liga_virtual,
        )

    def test_el_asesor_ve_el_nombre_del_alumno(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["alumno_nombre"], "Ana López Ruiz")
        self.assertEqual(response.data["alumno"], self.alumno.id)

    def test_el_alumno_ve_el_nombre_del_asesor(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get(f"/api/asesorias/asesorias/{self.asesoria.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["asesor_nombre"], "Beto Martínez")

    def test_listar_no_dispara_consultas_por_sesion(self):
        """Regresión de N+1: los nombres se resuelven con select_related."""
        for delta in (7, 14):
            Asesoria.objects.create(
                alumno=self.otro_alumno, disponibilidad=self.disponibilidad,
                materia=self.materia, carrera=self.carrera,
                fecha=self.proximo_lunes + datetime.timedelta(days=delta),
                hora_inicio=self.disponibilidad.hora_inicio,
                formato=self.disponibilidad.formato,
                liga_virtual=self.disponibilidad.liga_virtual,
            )
        self.client.force_authenticate(user=self.asesor_user)

        with self.assertNumQueries(2):
            response = self.client.get("/api/asesorias/asesorias/")

        self.assertEqual(len(response.data), 3)
```

Sobre `assertNumQueries(2)`: una consulta para resolver el `User` autenticado y una para el listado con sus `select_related`. Si el número real difiere por algo ajeno a este cambio (p. ej. una consulta de sesión), ajusta el número al valor observado **después** del Step 3 y deja el comentario — lo que el test protege es que el número no crezca con la cantidad de sesiones, no el valor absoluto. Para comprobarlo, agrega una tercera `Asesoria` localmente y confirma que el conteo no sube.

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `uv run manage.py test asesorias.tests.test_api_asesoria.NombresEnAsesoriaApiTests -v 2`

Expected: FAIL — `test_el_asesor_ve_el_nombre_del_alumno` y `test_el_alumno_ve_el_nombre_del_asesor` con `KeyError: 'alumno_nombre'` / `'asesor_nombre'`; `test_listar_no_dispara_consultas_por_sesion` falla con un conteo mayor a 2 (una consulta extra por sesión para resolver cada `alumno__user`) o pasa por casualidad — en cualquier caso vuelve a evaluarse en el Step 5.

- [ ] **Step 3: Agregar los campos de nombre al serializer**

En `backend/asesorias/serializers.py`, dentro de `AsesoriaSerializer`, agregar estas dos líneas justo debajo de `cancelado_por_rol = serializers.SerializerMethodField()`:

```python
    alumno_nombre = serializers.CharField(source="alumno.user.nombre_completo", read_only=True)
    asesor_nombre = serializers.CharField(
        source="disponibilidad.registro.asesor.user.nombre_completo", read_only=True
    )
```

y agregar `"alumno_nombre"` y `"asesor_nombre"` a `Meta.fields`, inmediatamente después de `"alumno"`:

```python
        fields = [
            "id", "alumno", "alumno_nombre", "asesor_nombre", "disponibilidad", "materia",
            "carrera", "fecha", "hora_inicio", "formato", "ubicacion", "liga_virtual",
            "estado", "asistio", "notas", "motivo_cancelacion", "cancelado_por",
            "cancelado_por_rol", "creado_en",
        ]
```

`read_only_fields` **no** cambia: ambos campos están declarados explícitamente con `read_only=True`.

- [ ] **Step 4: Evitar el N+1 en el viewset**

En `backend/asesorias/views.py`, reemplazar `AsesoriaViewSet.get_queryset` (líneas 118-130) por:

```python
    def get_queryset(self):
        user = self.request.user
        # alumno_nombre/asesor_nombre del serializer recorren dos cadenas de
        # FK; sin esto cada sesión del listado dispara consultas extra.
        base = Asesoria.objects.select_related(
            "alumno__user", "disponibilidad__registro__asesor__user", "materia"
        )
        if self.action in ("cancelar", "marcar_asistencia", "notas"):
            # get_object() resuelve desde este queryset ANTES de aplicar
            # has_object_permission. Si se filtrara aquí por dueño, un
            # objeto ajeno daría 404 y nunca llegaría a EsDuenoDeLaAsesoria
            # -> el 403 explícito que exige el ADR 0017 se perdería.
            return base
        if hasattr(user, "perfil_alumno"):
            return base.filter(alumno=user.perfil_alumno)
        if hasattr(user, "perfil_asesor_academico"):
            return base.filter(disponibilidad__registro__asesor__user=user)
        return Asesoria.objects.none()
```

- [ ] **Step 5: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test asesorias.tests.test_api_asesoria -v 2`

Expected: PASS — toda la clase nueva y todas las preexistentes. Si `assertNumQueries` falla con un número distinto de 2, ajústalo al valor observado (ver la nota del Step 1) y vuelve a correr.

- [ ] **Step 6: Correr la suite completa**

Run: `uv run manage.py test`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py \
        backend/asesorias/tests/test_api_asesoria.py
git commit -s -m "[feat][backend] exponer nombre de alumno y asesor en AsesoriaSerializer" \
  -m "- alumno_nombre y asesor_nombre (solo lectura, via User.nombre_completo)
    como campos hermanos: 'alumno' sigue siendo un id plano, para no
    romper a los consumidores actuales del payload.
- Se agregan las dos direcciones a la vez porque son el mismo mecanismo y
    la senal de revision de la deuda 0010 nombra explicitamente el caso
    simetrico (el alumno viendo a su asesor) como el disparador de un
    segundo parche identico.
- AsesoriaViewSet.get_queryset agrega select_related para no introducir un
    N+1 al serializar los listados; cubierto con assertNumQueries.
- Cierra el workaround 2 de la deuda tecnica 0010."
```

---

### Task 6: Consultar las sesiones futuras de un bloque de disponibilidad

Primer endpoint nuevo de la [spec del paso 3](../specs/2026-08-04-revision-vistas-asesorias-design.md): antes de mostrar el modal de advertencia al desactivar un bloque, la UI necesita saber si hay `Asesoria` agendadas a futuro sobre él, para no dejar sesiones huérfanas.

**Decisiones de forma tomadas aquí:**
- Respuesta como sobre `{"total": n, "sesiones": [...]}` en vez de array plano: el consumidor principal es un condicional (`total > 0` → mostrar modal), y un sobre deja explícito que esto no es un endpoint de listado paginable. Los endpoints `list` del proyecto siguen devolviendo arrays planos, sin cambio.
- "Futura" significa que la sesión **aún no ha comenzado** (fecha y hora comparadas contra `timezone.localtime()`), no solo `fecha >= hoy`: una sesión de hoy a las 09:00 vista a las 15:00 ya ocurrió y no debe aparecer en un modal que promete "sesiones futuras".
- La definición vive en un método de modelo (`Disponibilidad.sesiones_futuras()`) para que la Task 7 use exactamente el mismo criterio — si divergieran, el modal podría anunciar 2 sesiones y la acción cancelar 3.

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/serializers.py`
- Modify: `backend/asesorias/views.py`
- Test: `backend/asesorias/tests/test_disponibilidad.py`
- Test: `backend/asesorias/tests/test_api_disponibilidad.py`

**Interfaces:**
- Consumes: `Disponibilidad.asesorias` (related_name existente), `User.nombre_completo` (Task 3).
- Produces:
  - `Disponibilidad.sesiones_futuras() -> QuerySet[Asesoria]` — sesiones `estado="agendada"` que aún no comienzan, ordenadas por `(fecha, hora_inicio)`, con `select_related("alumno__user", "materia")`. La Task 7 la consume.
  - `asesorias.serializers.SesionFuturaSerializer` — campos `id`, `fecha`, `hora_inicio`, `alumno_nombre`, `materia_nombre`.
  - `GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/` → `200 {"total": int, "sesiones": [...]}`; `403` si el bloque no es del asesor autenticado.

- [ ] **Step 1: Escribir el test del método de modelo — RED**

Agregar al final de `backend/asesorias/tests/test_disponibilidad.py` (revisa los imports que ya tenga el archivo y agrega solo los que falten; los usados aquí son `datetime`, `timezone` de `django.utils`, `TestCase`, y los modelos):

```python
class SesionesFuturasTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        self.alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )

    def _crear_asesoria(self, fecha, estado="agendada"):
        return Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=fecha, hora_inicio=self.disponibilidad.hora_inicio,
            formato="virtual", liga_virtual="https://meet.example.com/x", estado=estado,
        )

    def test_incluye_solo_las_agendadas_que_no_han_ocurrido(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        self._crear_asesoria(hoy - datetime.timedelta(days=7))
        self._crear_asesoria(hoy + datetime.timedelta(days=14), estado="cancelada")

        futuras = list(self.disponibilidad.sesiones_futuras())

        self.assertEqual(futuras, [futura])

    def test_una_sesion_de_hoy_que_ya_empezo_no_cuenta_como_futura(self):
        hoy = timezone.localdate()
        temprano = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=hoy.weekday(),
            hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )
        Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=temprano, materia=self.materia,
            carrera=self.carrera, fecha=hoy, hora_inicio=datetime.time(0, 0),
            formato="virtual", liga_virtual="https://meet.example.com/y",
        )

        self.assertEqual(list(temprano.sesiones_futuras()), [])

    def test_sin_sesiones_devuelve_vacio(self):
        self.assertEqual(list(self.disponibilidad.sesiones_futuras()), [])
```

Nota sobre `test_una_sesion_de_hoy_que_ya_empezo_no_cuenta_como_futura`: usa `hora_inicio=00:00` para que la sesión esté garantizadamente en el pasado sin importar a qué hora corran los tests (salvo que corran exactamente a la medianoche). `Asesoria.objects.create` no llama a `clean()`, así que la ventana agendable no interfiere.

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad.SesionesFuturasTests -v 2`

Expected: FAIL con `AttributeError: 'Disponibilidad' object has no attribute 'sesiones_futuras'`.

- [ ] **Step 3: Implementar el método de modelo**

En `backend/asesorias/models.py`, dentro de la clase `Disponibilidad`, agregar después de la propiedad `hora_fin`:

```python
    def sesiones_futuras(self):
        """Sesiones agendadas sobre este bloque que todavía no comienzan.

        Criterio único para toda la app: lo consumen tanto el endpoint de
        consulta (`sesiones-futuras/`) como `desactivar()`. Si divergieran,
        el modal de advertencia podría anunciar N sesiones y la acción
        cancelar otra cantidad.
        """
        ahora = timezone.localtime()
        return (
            self.asesorias.filter(estado="agendada")
            .filter(
                models.Q(fecha__gt=ahora.date())
                | models.Q(fecha=ahora.date(), hora_inicio__gt=ahora.time())
            )
            .select_related("alumno__user", "materia")
            .order_by("fecha", "hora_inicio")
        )
```

`models`, `timezone` y `transaction` ya están importados al inicio del archivo (líneas 2-3).

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad.SesionesFuturasTests -v 2`

Expected: PASS — los 3 tests.

- [ ] **Step 5: Escribir el test del endpoint — RED**

Agregar al final de `backend/asesorias/tests/test_api_disponibilidad.py`:

```python
class SesionesFuturasApiTests(APITestCase):
    def setUp(self):
        from accounts.models import PerfilAlumno
        from asesorias.models import Asesoria
        from carreras.models import Carrera
        from materias.models import Materia

        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        self.asesor_user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.asesor_user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.asesor_user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )

        self.otro_user = User.objects.create_user(email="otro@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.otro_user, numero_trabajador="54321")
        self.otro_asesor = PerfilAsesorAcademico.objects.create(user=self.otro_user, area=self.area)

        self.alumno_user = User.objects.create_user(
            email="alumno@ciencias.unam.mx", password="x", first_name="Ana",
        )
        self.alumno_user.apellido1 = "López"
        self.alumno_user.save()
        self.alumno = PerfilAlumno.objects.create(
            user=self.alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        self.Asesoria = Asesoria

    def _crear_asesoria_futura(self, dias):
        from django.utils import timezone
        return self.Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=timezone.localdate() + datetime.timedelta(days=dias),
            hora_inicio=self.disponibilidad.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/x",
        )

    def test_devuelve_total_y_lista_minima(self):
        self._crear_asesoria_futura(7)
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        sesion = response.data["sesiones"][0]
        self.assertEqual(sesion["alumno_nombre"], "Ana López")
        self.assertEqual(sesion["materia_nombre"], "Álgebra")
        self.assertIn("fecha", sesion)
        self.assertIn("hora_inicio", sesion)

    def test_bloque_sin_sesiones_devuelve_total_cero(self):
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"total": 0, "sesiones": []})

    def test_bloque_ajeno_devuelve_403(self):
        self.client.force_authenticate(user=self.otro_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 403)

    def test_alumno_no_puede_consultar(self):
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.get(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/sesiones-futuras/"
        )

        self.assertEqual(response.status_code, 403)
```

Agregar al inicio del archivo el import que falta: `from accounts.models import PerfilAcademico, User` ya está; agrega también `from asesorias.models import PerfilAsesorAcademico, RegistroAsesor, Disponibilidad` (ya está) — verifica y no dupliques.

- [ ] **Step 6: Correr el test y confirmar que falla**

Run: `uv run manage.py test asesorias.tests.test_api_disponibilidad.SesionesFuturasApiTests -v 2`

Expected: FAIL con `404` en todos los tests (la ruta `sesiones-futuras/` no existe todavía).

- [ ] **Step 7: Implementar el serializer y la acción**

En `backend/asesorias/serializers.py`, agregar después de `ResultadoBusquedaSerializer`:

```python
class SesionFuturaSerializer(serializers.Serializer):
    """Vista mínima de una Asesoria para el modal de advertencia al
    desactivar un bloque: lo justo para que el asesor reconozca qué está
    por cancelar."""

    id = serializers.IntegerField()
    fecha = serializers.DateField()
    hora_inicio = serializers.TimeField()
    alumno_nombre = serializers.CharField(source="alumno.user.nombre_completo")
    materia_nombre = serializers.CharField(source="materia.nombre")
```

En `backend/asesorias/views.py`, agregar la acción dentro de `DisponibilidadViewSet` (después de `get_queryset`):

```python
    @action(detail=True, methods=["get"], url_path="sesiones-futuras")
    def sesiones_futuras(self, request, pk=None):
        disponibilidad = self.get_object()
        sesiones = list(disponibilidad.sesiones_futuras())
        return Response({
            "total": len(sesiones),
            "sesiones": SesionFuturaSerializer(sesiones, many=True).data,
        })
```

y agregar `SesionFuturaSerializer` a la lista de imports de serializers al inicio del archivo (líneas 16-19), respetando el orden alfabético ya usado.

Nota: la acción hereda `permission_classes = [EsAsesorAcademico, EsDuenoDelRegistro]` del viewset, y `self.get_object()` dispara `has_object_permission`; `EsDuenoDelRegistro` ya sabe resolver `obj.registro` (`asesorias/permissions.py:29`). El `get_queryset` de este viewset devuelve `Disponibilidad.objects.all()` para acciones que no son `list`, así que un bloque ajeno llega al chequeo de permiso y da `403`, no `404` — el comportamiento explícito que exige ADR 0017.

- [ ] **Step 8: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test asesorias.tests.test_api_disponibilidad asesorias.tests.test_disponibilidad -v 2`

Expected: PASS — todo, incluidos los tests preexistentes de ambos archivos.

- [ ] **Step 9: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/serializers.py backend/asesorias/views.py \
        backend/asesorias/tests/test_disponibilidad.py backend/asesorias/tests/test_api_disponibilidad.py
git commit -s -m "[feat][backend] consultar sesiones futuras de un bloque de disponibilidad" \
  -m "- Disponibilidad.sesiones_futuras(): sesiones agendadas que aun no
    comienzan (fecha+hora contra localtime, no solo fecha >= hoy). Vive en
    el modelo para que la accion de desactivar use el mismo criterio.
- GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/ responde
    {total, sesiones} con la vista minima que necesita el modal de
    advertencia; 403 si el bloque es de otro asesor.
- Requisito de entrada del rediseno de vistas de asesorias (paso 3)."
```

---

### Task 7: Desactivar un bloque, con o sin cancelar sus sesiones futuras

Segundo endpoint nuevo de la spec del paso 3. El modal de 3 acciones ofrece: (1) "Solo dejar de recibir nuevas", (2) "Cancelar esas sesiones y desactivar", (3) "Volver".

**Decisiones de forma tomadas aquí:**
- **Un solo endpoint para las opciones 1 y 2**, distinguidas por un flag del body: `POST /api/asesorias/disponibilidades/{id}/desactivar/ {"cancelar_sesiones": bool, "motivo": str}`. Ambas son la misma intención ("desactivar este bloque") y difieren solo en qué pasa con lo ya agendado; servirlas con un `PATCH {activa:false}` y un `POST` distintos obligaría al frontend a usar dos verbos y dos formas de respuesta para dos botones del mismo modal. El `PATCH activa` existente **no** se retira: sigue siendo el toggle simple del resto de la UI.
- **La cancelación en masa es transaccional** (`transaction.atomic`), así que o se cancelan todas las sesiones y el bloque queda inactivo, o no cambia nada. Es lo que la spec pide explícitamente ("no un loop de N requests desde el frontend").
- **Motivo por defecto** `"El asesor dio de baja este horario."` cuando se cancelan sesiones sin motivo: `Asesoria.motivo_cancelacion` es lo único que el alumno verá en su panel de cancelación, y un motivo vacío ahí no comunica nada.
- La lógica vive en `Disponibilidad.desactivar()` (modelo), como exige ADR 0016; la vista solo valida el body y traduce.

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/serializers.py`
- Modify: `backend/asesorias/views.py`
- Test: `backend/asesorias/tests/test_disponibilidad.py`
- Test: `backend/asesorias/tests/test_api_disponibilidad.py`

**Interfaces:**
- Consumes: `Disponibilidad.sesiones_futuras()` (Task 6), `Asesoria.cancelar(usuario, motivo="")` (existente).
- Produces:
  - `Disponibilidad.desactivar(*, usuario, cancelar_sesiones=False, motivo="") -> int` — devuelve cuántas sesiones canceló.
  - `asesorias.serializers.DesactivarDisponibilidadSerializer` — body `{cancelar_sesiones: bool (default False), motivo: str (opcional)}`.
  - `POST /api/asesorias/disponibilidades/{id}/desactivar/` → `200 {"disponibilidad": {...}, "sesiones_canceladas": int}`.

- [ ] **Step 1: Escribir el test del método de modelo — RED**

Agregar al final de `backend/asesorias/tests/test_disponibilidad.py` una clase nueva que reusa el mismo `setUp` que `SesionesFuturasTests` (la Task 6 ya lo escribió; hereda de ella para no duplicarlo):

```python
class DesactivarDisponibilidadTests(SesionesFuturasTests):
    def test_desactivar_sin_cancelar_conserva_las_sesiones(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        canceladas = self.disponibilidad.desactivar(usuario=self.asesor_user)

        self.assertEqual(canceladas, 0)
        self.disponibilidad.refresh_from_db()
        self.assertFalse(self.disponibilidad.activa)
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "agendada")

    def test_desactivar_cancelando_cancela_solo_las_futuras(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))
        pasada = self._crear_asesoria(hoy - datetime.timedelta(days=7))

        canceladas = self.disponibilidad.desactivar(
            usuario=self.asesor_user, cancelar_sesiones=True, motivo="Cambio de horario.",
        )

        self.assertEqual(canceladas, 1)
        self.disponibilidad.refresh_from_db()
        self.assertFalse(self.disponibilidad.activa)
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "cancelada")
        self.assertEqual(futura.motivo_cancelacion, "Cambio de horario.")
        self.assertEqual(futura.cancelado_por, self.asesor_user)
        pasada.refresh_from_db()
        self.assertEqual(pasada.estado, "agendada")

    def test_motivo_vacio_usa_el_texto_por_defecto(self):
        hoy = timezone.localdate()
        futura = self._crear_asesoria(hoy + datetime.timedelta(days=7))

        self.disponibilidad.desactivar(usuario=self.asesor_user, cancelar_sesiones=True)

        futura.refresh_from_db()
        self.assertEqual(futura.motivo_cancelacion, "El asesor dio de baja este horario.")
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad.DesactivarDisponibilidadTests -v 2`

Expected: FAIL con `AttributeError: 'Disponibilidad' object has no attribute 'desactivar'` en los 3 tests.

- [ ] **Step 3: Implementar el método de modelo**

En `backend/asesorias/models.py`, dentro de la clase `Disponibilidad`, agregar después de `sesiones_futuras`:

```python
    MOTIVO_BAJA_DE_HORARIO = "El asesor dio de baja este horario."

    def desactivar(self, *, usuario, cancelar_sesiones=False, motivo=""):
        """Deja de ofrecer este bloque. Devuelve cuántas sesiones canceló.

        Con `cancelar_sesiones=False` las sesiones ya agendadas se
        conservan (el bloque solo deja de aparecer en búsquedas); con
        `True` se cancelan todas las futuras en la misma transacción, para
        que no quede un estado intermedio con la mitad canceladas.
        """
        with transaction.atomic():
            canceladas = 0
            if cancelar_sesiones:
                for asesoria in list(self.sesiones_futuras()):
                    asesoria.cancelar(
                        usuario=usuario, motivo=motivo or self.MOTIVO_BAJA_DE_HORARIO
                    )
                    canceladas += 1
            self.activa = False
            self.save()
        return canceladas
```

`transaction` ya está importado (línea 2). Las notificaciones de cancelación que dispara `Asesoria.cancelar()` usan `transaction.on_commit`, así que se encolan una sola vez al confirmar la transacción — nunca a medias.

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `uv run manage.py test asesorias.tests.test_disponibilidad -v 2`

Expected: PASS — todo el archivo.

- [ ] **Step 5: Escribir el test del endpoint — RED**

Agregar al final de `backend/asesorias/tests/test_api_disponibilidad.py` una clase que hereda el `setUp` de la Task 6:

```python
class DesactivarDisponibilidadApiTests(SesionesFuturasApiTests):
    def test_desactivar_sin_cancelar(self):
        futura = self._crear_asesoria_futura(7)
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/desactivar/",
            {"cancelar_sesiones": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sesiones_canceladas"], 0)
        self.assertFalse(response.data["disponibilidad"]["activa"])
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "agendada")

    def test_desactivar_cancelando_sesiones(self):
        futura = self._crear_asesoria_futura(7)
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/desactivar/",
            {"cancelar_sesiones": True, "motivo": "Cambio de horario."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sesiones_canceladas"], 1)
        self.assertFalse(response.data["disponibilidad"]["activa"])
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "cancelada")
        self.assertEqual(futura.motivo_cancelacion, "Cambio de horario.")

    def test_body_vacio_equivale_a_no_cancelar(self):
        futura = self._crear_asesoria_futura(7)
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/desactivar/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sesiones_canceladas"], 0)
        futura.refresh_from_db()
        self.assertEqual(futura.estado, "agendada")

    def test_desactivar_bloque_ajeno_devuelve_403(self):
        self.client.force_authenticate(user=self.otro_user)

        response = self.client.post(
            f"/api/asesorias/disponibilidades/{self.disponibilidad.id}/desactivar/",
            {"cancelar_sesiones": True},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 6: Correr el test y confirmar que falla**

Run: `uv run manage.py test asesorias.tests.test_api_disponibilidad.DesactivarDisponibilidadApiTests -v 2`

Expected: FAIL con `404` en los 4 tests (la ruta no existe).

- [ ] **Step 7: Implementar el serializer de body y la acción**

En `backend/asesorias/serializers.py`, agregar después de `SesionFuturaSerializer`:

```python
class DesactivarDisponibilidadSerializer(serializers.Serializer):
    cancelar_sesiones = serializers.BooleanField(required=False, default=False)
    motivo = serializers.CharField(required=False, allow_blank=True, default="")
```

En `backend/asesorias/views.py`, agregar dentro de `DisponibilidadViewSet`, después de la acción `sesiones_futuras`:

```python
    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        disponibilidad = self.get_object()
        serializer = DesactivarDisponibilidadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        canceladas = disponibilidad.desactivar(
            usuario=request.user,
            cancelar_sesiones=serializer.validated_data["cancelar_sesiones"],
            motivo=serializer.validated_data["motivo"],
        )
        return Response({
            "disponibilidad": DisponibilidadSerializer(disponibilidad).data,
            "sesiones_canceladas": canceladas,
        })
```

y agregar `DesactivarDisponibilidadSerializer` al bloque de imports de serializers al inicio del archivo.

- [ ] **Step 8: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test asesorias.tests.test_api_disponibilidad asesorias.tests.test_disponibilidad -v 2`

Expected: PASS — todo.

- [ ] **Step 9: Correr la suite completa**

Run: `uv run manage.py test`

Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/serializers.py backend/asesorias/views.py \
        backend/asesorias/tests/test_disponibilidad.py backend/asesorias/tests/test_api_disponibilidad.py
git commit -s -m "[feat][backend] desactivar un bloque cancelando sus sesiones futuras en una transaccion" \
  -m "- Disponibilidad.desactivar(usuario, cancelar_sesiones, motivo): pone
    activa=False y, si se pide, cancela todas las sesiones futuras dentro
    de la misma transaccion (nunca a medias). Devuelve cuantas cancelo.
- POST /api/asesorias/disponibilidades/{id}/desactivar/ sirve las dos
    opciones del modal de 3 acciones con un solo endpoint; el PATCH de
    'activa' sigue existiendo para el toggle simple.
- Motivo por defecto 'El asesor dio de baja este horario.' cuando se
    cancelan sesiones sin motivo: es lo unico que el alumno vera.
- Requisito de entrada del rediseno de vistas de asesorias (paso 3)."
```

---

### Task 8: Quitar una materia del registro del asesor

Tercer endpoint nuevo de la spec del paso 3: la pantalla "Mis materias" tiene un botón de quitar por fila, pero hoy `RegistroAsesorSerializer.materias` es `read_only` y solo existe el `agregar_materia()` simétrico.

**Decisiones de forma tomadas aquí:**
- **`POST .../materias/quitar/` y no `DELETE .../materias/{id}/`.** `RegistroAsesorViewSet.http_method_names` excluye `delete` a propósito (`backend/asesorias/views.py:26`), porque ADR 0017 y `docs/development/api-frontend.md` fijan que `RegistroAsesor` no acepta `DELETE` en ningún caso. Habilitar el verbo para una subruta también habilitaría `DELETE /registros/{id}/` (la acción `destroy` del `ModelViewSet`), obligando a re-prohibirla con un override. `POST .../materias/quitar/` es simétrico con el `POST .../materias/` ya existente y no toca `http_method_names`.
- **Quitar una materia no cancela nada.** Es literalmente la promesa del copy que la spec fija para el diálogo de confirmación: "Ya no aparecerás como asesor de esta materia en búsquedas de alumnos. Las asesorías ya agendadas no se cancelan."
- **Quitar una materia que no está en el registro es un `400`, no un no-op silencioso**, para que un doble tap del usuario no se confunda con éxito real.

**Files:**
- Modify: `backend/asesorias/models.py`
- Modify: `backend/asesorias/serializers.py`
- Modify: `backend/asesorias/views.py`
- Test: `backend/asesorias/tests/test_registro_asesor.py`
- Test: `backend/asesorias/tests/test_api_registro.py`

**Interfaces:**
- Consumes: `RegistroAsesor.materias` (M2M existente), `RegistroAsesor.agregar_materia()` (existente, sin cambios).
- Produces:
  - `RegistroAsesor.quitar_materia(materia) -> None` — levanta `django.core.exceptions.ValidationError` si la materia no está en el registro.
  - `asesorias.serializers.MateriaDelRegistroSerializer` — **renombre** de `AgregarMateriaSerializer`; mismo campo `materia_id`, ahora usado por las dos acciones.
  - `POST /api/asesorias/registros/{id}/materias/quitar/ {"materia_id": int}` → `200` con el `RegistroAsesorSerializer` actualizado.

- [ ] **Step 1: Renombrar `AgregarMateriaSerializer` a `MateriaDelRegistroSerializer` (refactor puro)**

El serializer solo valida que la materia exista; lo van a usar tanto agregar como quitar, así que el nombre con "Agregar" deja de describirlo. Es un refactor sin cambio de comportamiento, y por la regla de atomicidad de `docs/development/commit-conventions.md` va en su propio commit, antes de la funcionalidad.

En `backend/asesorias/serializers.py`, renombrar la clase (líneas 16-23):

```python
class MateriaDelRegistroSerializer(serializers.Serializer):
    """Valida el `materia_id` del body de las acciones de agregar y quitar
    materia de un RegistroAsesor."""

    materia_id = serializers.IntegerField()

    def validate_materia_id(self, value):
        try:
            return Materia.objects.get(pk=value)
        except Materia.DoesNotExist:
            raise serializers.ValidationError("La materia no existe.")
```

En `backend/asesorias/views.py`, actualizar el import (línea 16-19) y el único uso, dentro de `RegistroAsesorViewSet.materias`:

```python
        serializer = MateriaDelRegistroSerializer(data=request.data)
```

Verificar que no quede ninguna referencia:

Run: `grep -rn "AgregarMateriaSerializer" backend/`
Expected: sin resultados.

Run: `uv run manage.py test asesorias -v 2`
Expected: PASS — nada cambió de comportamiento.

```bash
git add backend/asesorias/serializers.py backend/asesorias/views.py
git commit -s -m "[refactor][backend] renombrar AgregarMateriaSerializer a MateriaDelRegistroSerializer" \
  -m "- El serializer solo valida que exista la materia; lo van a usar tanto
    la accion de agregar como la de quitar, asi que el nombre con
    'Agregar' deja de describirlo. Sin cambio de comportamiento."
```

- [ ] **Step 2: Escribir el test del método de modelo — RED**

Agregar al final de `backend/asesorias/tests/test_registro_asesor.py` (revisa los imports existentes del archivo y agrega solo los que falten):

```python
class QuitarMateriaTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(nombre="Area test")
        self.carrera = Carrera.objects.create(clave=801, nombre="Carrera Test", area=self.area)
        self.materia = Materia.objects.create(
            clave="1801", nombre="Álgebra", carrera=self.carrera, nivel=1, plan=2006,
            habilitada_asesorias=True,
        )
        OfertaMateria.objects.create(materia=self.materia, semestre="20271", se_imparte=True)
        self.user = User.objects.create_user(email="asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=self.user, numero_trabajador="12345")
        self.asesor = PerfilAsesorAcademico.objects.create(user=self.user, area=self.area)
        self.registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")

    def test_quitar_una_materia_del_registro(self):
        self.registro.agregar_materia(self.materia)

        self.registro.quitar_materia(self.materia)

        self.assertNotIn(self.materia, self.registro.materias.all())

    def test_quitar_una_materia_que_no_esta_levanta_validation_error(self):
        with self.assertRaises(ValidationError):
            self.registro.quitar_materia(self.materia)

    def test_quitar_una_materia_no_cancela_las_asesorias_agendadas(self):
        """La promesa explícita del diálogo de confirmación: 'Las asesorías
        ya agendadas no se cancelan.'"""
        self.registro.agregar_materia(self.materia)
        disponibilidad = Disponibilidad.objects.create(
            registro=self.registro, dia_semana=0, hora_inicio=datetime.time(10, 0),
            formato="virtual", liga_virtual="https://meet.example.com/x",
        )
        alumno_user = User.objects.create_user(email="alumno@ciencias.unam.mx", password="x")
        alumno = PerfilAlumno.objects.create(
            user=alumno_user, numero_cuenta="312345678", carrera=self.carrera, generacion=2023,
        )
        asesoria = Asesoria.objects.create(
            alumno=alumno, disponibilidad=disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=timezone.localdate() + datetime.timedelta(days=7),
            hora_inicio=datetime.time(10, 0), formato="virtual",
            liga_virtual="https://meet.example.com/x",
        )

        self.registro.quitar_materia(self.materia)

        asesoria.refresh_from_db()
        self.assertEqual(asesoria.estado, "agendada")
```

Imports que este bloque necesita (agrega solo los que el archivo no tenga ya): `datetime`, `from django.core.exceptions import ValidationError`, `from django.test import TestCase`, `from django.utils import timezone`, `from accounts.models import PerfilAcademico, PerfilAlumno, User`, `from asesorias.models import Asesoria, Disponibilidad, PerfilAsesorAcademico, RegistroAsesor`, `from carreras.models import Area, Carrera`, `from materias.models import Materia, OfertaMateria`.

- [ ] **Step 3: Correr el test y confirmar que falla**

Run: `uv run manage.py test asesorias.tests.test_registro_asesor.QuitarMateriaTests -v 2`

Expected: FAIL con `AttributeError: 'RegistroAsesor' object has no attribute 'quitar_materia'` en los 3 tests.

- [ ] **Step 4: Implementar el método de modelo**

En `backend/asesorias/models.py`, dentro de `RegistroAsesor`, agregar justo después de `agregar_materia`:

```python
    def quitar_materia(self, materia):
        """Deja de ofrecer asesorías de esta materia.

        No toca las asesorías ya agendadas — solo deja de aparecer en las
        búsquedas de los alumnos de aquí en adelante.
        """
        if not self.materias.filter(pk=materia.pk).exists():
            raise ValidationError("La materia no está en este registro.")
        self.materias.remove(materia)
```

`ValidationError` (de `django.core.exceptions`) ya está importado en la línea 1.

- [ ] **Step 5: Correr el test y confirmar que pasa**

Run: `uv run manage.py test asesorias.tests.test_registro_asesor -v 2`

Expected: PASS — todo el archivo.

- [ ] **Step 6: Escribir el test del endpoint — RED**

Agregar al final de la clase `RegistroAsesorApiTests` en `backend/asesorias/tests/test_api_registro.py`:

```python
    def test_quitar_materia_exitoso(self):
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        registro.agregar_materia(self.materia)
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/quitar/",
            {"materia_id": self.materia.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["materias"], [])
        registro.refresh_from_db()
        self.assertNotIn(self.materia, registro.materias.all())
        registro.delete()

    def test_quitar_materia_que_no_esta_devuelve_400(self):
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/quitar/",
            {"materia_id": self.materia.id},
        )

        self.assertEqual(response.status_code, 400)
        registro.delete()

    def test_quitar_materia_de_registro_ajeno_devuelve_403(self):
        self.client.force_authenticate(user=self.asesor_user)

        response = self.client.post(
            f"/api/asesorias/registros/{self.registro_ajeno.id}/materias/quitar/",
            {"materia_id": self.materia.id},
        )

        self.assertEqual(response.status_code, 403)

    def test_alumno_no_puede_quitar_materia(self):
        registro = RegistroAsesor.objects.create(asesor=self.asesor, semestre="20271")
        registro.agregar_materia(self.materia)
        self.client.force_authenticate(user=self.alumno_user)

        response = self.client.post(
            f"/api/asesorias/registros/{registro.id}/materias/quitar/",
            {"materia_id": self.materia.id},
        )

        self.assertEqual(response.status_code, 403)
        registro.delete()
```

- [ ] **Step 7: Correr el test y confirmar que falla**

Run: `uv run manage.py test asesorias.tests.test_api_registro -v 2`

Expected: FAIL — los 4 tests nuevos con `404` (la ruta no existe); los preexistentes en PASS.

- [ ] **Step 8: Implementar la acción**

En `backend/asesorias/views.py`, agregar dentro de `RegistroAsesorViewSet`, después de la acción `materias`:

```python
    @action(detail=True, methods=["post"], url_path="materias/quitar")
    def quitar_materia(self, request, pk=None):
        registro = self.get_object()
        serializer = MateriaDelRegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        materia = serializer.validated_data["materia_id"]
        try:
            registro.quitar_materia(materia)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RegistroAsesorSerializer(registro).data, status=status.HTTP_200_OK)
```

Es `POST` y no `DELETE` a propósito: `http_method_names` de este viewset excluye `delete` para que `DELETE /registros/{id}/` no exista (ADR 0017), y habilitarlo para una subruta también lo habilitaría para el recurso.

- [ ] **Step 9: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test asesorias -v 2`

Expected: PASS — toda la app.

- [ ] **Step 10: Commit**

```bash
git add backend/asesorias/models.py backend/asesorias/views.py \
        backend/asesorias/tests/test_registro_asesor.py backend/asesorias/tests/test_api_registro.py
git commit -s -m "[feat][backend] permitir quitar una materia del registro del asesor" \
  -m "- RegistroAsesor.quitar_materia(): simetrico de agregar_materia; no
    toca las asesorias ya agendadas (la promesa literal del dialogo de
    confirmacion del rediseno) y falla con 400 si la materia no esta.
- POST /api/asesorias/registros/{id}/materias/quitar/ {materia_id}. Se
    usa POST y no DELETE porque http_method_names de este viewset excluye
    'delete' a proposito (ADR 0017: RegistroAsesor no acepta DELETE), y
    habilitarlo para la subruta lo habilitaria para el recurso.
- Requisito de entrada del rediseno de vistas de asesorias (paso 3)."
```

---

### Task 9: Filtrar el historial de asesorías por semestre

Cuarto y último endpoint nuevo de la spec del paso 3: el historial pasa a tener subtabs de semestre en vez de cargar todo de una vez.

**Decisiones de forma tomadas aquí:**
- **Filtro por query param en el listado existente** (`GET /api/asesorias/asesorias/?semestre=20262`), filtrando por `disponibilidad__registro__semestre`, tal como la spec propone. Se implementa con comparación manual en `get_queryset`, sin `django-filter` — es la convención que ya usa `materias` (`docs/development/api-frontend.md`: "comparación manual en `get_queryset`, no `django-filter`").
- **Permisivo, no validador:** un `semestre` desconocido devuelve `[]`, no `400`. No hay modelo de calendario académico que defina qué claves son válidas (deuda técnica 0001), así que validar el formato aquí inventaría una regla que nadie decidió.
- **Endpoint auxiliar `GET /api/asesorias/asesorias/semestres/`** (array plano de claves, orden descendente). Sin él, el frontend no puede construir los subtabs sin cargar el historial completo — exactamente lo que el filtro busca evitar. Devuelve solo los semestres del usuario autenticado, reusando el mismo `get_queryset` con su ramificación por rol. El primer elemento es el semestre más reciente con sesiones, que es lo que el tab por default debe cargar: no hace falta un modelo de calendario para eso.
- El filtro **no** resuelve la [deuda técnica 0006](../../technical-debt/0006-sin-paginacion-listados.md): cubre el caso de uso más común (ver el historial de un semestre), no establece una convención de paginación de proyecto. Se anota en la propia 0006 en la Task 10.

**Files:**
- Modify: `backend/asesorias/views.py`
- Test: `backend/asesorias/tests/test_api_asesoria.py`

**Interfaces:**
- Consumes: `RegistroAsesor.semestre` (`CharField(max_length=5)`, formato `"20262"`), alcanzable desde `Asesoria` vía `disponibilidad__registro__semestre`.
- Produces:
  - `GET /api/asesorias/asesorias/?semestre=<clave>` → mismo shape de listado, filtrado.
  - `GET /api/asesorias/asesorias/semestres/` → `200 ["20262", "20261"]`.

- [ ] **Step 1: Escribir los tests — RED**

Agregar al final de `backend/asesorias/tests/test_api_asesoria.py`:

```python
class FiltroSemestreApiTests(AsesoriaApiTestsBase):
    def setUp(self):
        super().setUp()
        # Un segundo registro/disponibilidad del mismo asesor, en otro semestre.
        self.registro_viejo = RegistroAsesor.objects.create(
            asesor=self.asesor, semestre="20262",
        )
        self.disponibilidad_vieja = Disponibilidad.objects.create(
            registro=self.registro_viejo, dia_semana=0, hora_inicio=datetime.time(12, 0),
            formato="virtual", liga_virtual="https://meet.example.com/z",
        )
        self.sesion_actual = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes,
            hora_inicio=self.disponibilidad.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/x",
        )
        self.sesion_vieja = Asesoria.objects.create(
            alumno=self.alumno, disponibilidad=self.disponibilidad_vieja, materia=self.materia,
            carrera=self.carrera, fecha=self.proximo_lunes - datetime.timedelta(days=7 * 20),
            hora_inicio=self.disponibilidad_vieja.hora_inicio, formato="virtual",
            liga_virtual="https://meet.example.com/z", estado="realizada", asistio=True,
        )

    def test_sin_filtro_devuelve_todas(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filtra_por_semestre(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/?semestre=20262")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.sesion_vieja.id)

    def test_semestre_desconocido_devuelve_lista_vacia(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/?semestre=19991")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_el_alumno_tambien_puede_filtrar(self):
        self.client.force_authenticate(user=self.alumno_user)
        response = self.client.get("/api/asesorias/asesorias/?semestre=20271")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.sesion_actual.id)

    def test_listar_semestres_del_asesor_en_orden_descendente(self):
        self.client.force_authenticate(user=self.asesor_user)
        response = self.client.get("/api/asesorias/asesorias/semestres/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ["20271", "20262"])

    def test_listar_semestres_solo_incluye_los_del_usuario(self):
        otro_user = User.objects.create_user(email="otro_asesor@ciencias.unam.mx", password="x")
        PerfilAcademico.objects.create(user=otro_user, numero_trabajador="99999")
        PerfilAsesorAcademico.objects.create(user=otro_user, area=self.area)
        self.client.force_authenticate(user=otro_user)

        response = self.client.get("/api/asesorias/asesorias/semestres/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
```

`RegistroAsesor`, `Disponibilidad`, `PerfilAsesorAcademico`, `PerfilAcademico`, `User` y `Asesoria` ya están importados al inicio de ese archivo (líneas 3-8).

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `uv run manage.py test asesorias.tests.test_api_asesoria.FiltroSemestreApiTests -v 2`

Expected: FAIL en 4 de los 6.
- `test_sin_filtro_devuelve_todas` → PASS ya (línea base).
- `test_filtra_por_semestre` → FAIL con `2 != 1`: el query param se ignora.
- `test_semestre_desconocido_devuelve_lista_vacia` → FAIL: devuelve las 2 sesiones.
- `test_el_alumno_tambien_puede_filtrar` → FAIL con `2 != 1`.
- Los dos de `semestres/` → FAIL con `404`.

- [ ] **Step 3: Implementar el filtro y la acción**

En `backend/asesorias/views.py`, reemplazar `AsesoriaViewSet.get_queryset` (la versión que dejó la Task 5) por:

```python
    def get_queryset(self):
        user = self.request.user
        # alumno_nombre/asesor_nombre del serializer recorren dos cadenas de
        # FK; sin esto cada sesión del listado dispara consultas extra.
        base = Asesoria.objects.select_related(
            "alumno__user", "disponibilidad__registro__asesor__user", "materia"
        )
        if self.action in ("cancelar", "marcar_asistencia", "notas"):
            # get_object() resuelve desde este queryset ANTES de aplicar
            # has_object_permission. Si se filtrara aquí por dueño, un
            # objeto ajeno daría 404 y nunca llegaría a EsDuenoDeLaAsesoria
            # -> el 403 explícito que exige el ADR 0017 se perdería.
            return base

        if hasattr(user, "perfil_alumno"):
            queryset = base.filter(alumno=user.perfil_alumno)
        elif hasattr(user, "perfil_asesor_academico"):
            queryset = base.filter(disponibilidad__registro__asesor__user=user)
        else:
            return Asesoria.objects.none()

        # Filtro de historial por semestre. Comparación manual, igual que
        # materias/views.py — el proyecto no usa django-filter. Permisivo a
        # propósito: un semestre desconocido devuelve [], no 400, porque no
        # existe un modelo de calendario académico que defina qué claves son
        # válidas (deuda técnica 0001).
        if self.action == "list":
            semestre = self.request.query_params.get("semestre")
            if semestre:
                queryset = queryset.filter(disponibilidad__registro__semestre=semestre)
        return queryset

    @action(detail=False, methods=["get"])
    def semestres(self, request):
        """Claves de semestre en las que el usuario tiene sesiones, de la más
        reciente a la más antigua.

        Sostiene los subtabs del historial: sin esto el frontend tendría que
        cargar el historial completo para saber qué pestañas dibujar, que es
        justo lo que el filtro `?semestre=` busca evitar.
        """
        claves = self.get_queryset().values_list(
            "disponibilidad__registro__semestre", flat=True
        )
        return Response(sorted(set(claves), reverse=True))
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `uv run manage.py test asesorias.tests.test_api_asesoria -v 2`

Expected: PASS — todo el archivo, incluidas las clases anteriores.

- [ ] **Step 5: Correr la suite completa**

Run: `uv run manage.py test`

Expected: PASS — toda la suite del backend.

- [ ] **Step 6: Commit**

```bash
git add backend/asesorias/views.py backend/asesorias/tests/test_api_asesoria.py
git commit -s -m "[feat][backend] filtrar asesorias por semestre y listar los semestres con sesiones" \
  -m "- GET /api/asesorias/asesorias/?semestre=20262 filtra por
    disponibilidad__registro__semestre, con comparacion manual en
    get_queryset (misma convencion que materias, sin django-filter).
    Permisivo: un semestre desconocido devuelve [], no 400.
- GET /api/asesorias/asesorias/semestres/ devuelve las claves del usuario
    en orden descendente, para que los subtabs del historial no obliguen a
    cargar el historial completo.
- Cubre parcialmente la deuda tecnica 0006 (sin paginacion) para el caso
    de uso mas comun; no establece la convencion de paginacion del
    proyecto ni la reemplaza.
- Requisito de entrada del rediseno de vistas de asesorias (paso 3)."
```

---

### Task 10: Documentar los cambios (ADRs, deuda técnica y guía de API)

Todo cambio de contrato de API en este repo se refleja en `docs/development/api-frontend.md` y en el `## Changelog` del ADR correspondiente, sin reescribir la decisión original (es el patrón del commit `d6ade66`). Además, la deuda técnica 0010 queda resuelta y la 0006 gana una nota.

**Files:**
- Modify: `docs/development/api-frontend.md`
- Modify: `docs/decisions/0016-asesorias-academicas.md`
- Modify: `docs/decisions/0017-asesorias-academicas-api.md`
- Modify: `docs/decisions/0019-transporte-login-google-id-token.md`
- Modify: `docs/technical-debt/0006-sin-paginacion-listados.md`
- Modify: `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md`
- Modify: `docs/technical-debt/README.md`

**Interfaces:**
- Consumes: los contratos verificados por los tests de las Tasks 1-9.
- Produces: nada consumido por código.

- [ ] **Step 1: Actualizar la sección de login con Google en la guía de API**

En `docs/development/api-frontend.md`, reemplazar los puntos 1 y 2 de la subsección "### Login con Google (único flujo social soportado)" por:

```markdown
1. El SPA usa Google Identity Services — **Sign In With Google** (`google.accounts.id`, no `google.accounts.oauth2`) para obtener un **ID token** (JWT OIDC) directamente en el navegador. **No existe flujo de redirect/Authorization Code** — se eliminó del backend el 2026-08-01 (commit `cdefb7e`); no hay ruta de callback que implementar.
2. `POST /api/auth/google/` con `{"id_token": "<jwt>"}`. **Mandar `access_token` ya no funciona**: desde ADR 0019 el backend lo rechaza con `400`, porque el flujo de `access_token` no verificaba que el token se hubiera emitido para el `client_id` de Atenea (`audience`). Errores posibles: `400 {"detail": ["El id_token de Google no es válido."]}` (firma, issuer, expiración o `audience` inválidos) y `400 {"non_field_errors": ["Incorrect input. id_token is required."]}` (falta el campo).
```

- [ ] **Step 2: Actualizar el payload de usuario en la guía de API**

En `docs/development/api-frontend.md`, reemplazar el bloque JSON de la subsección "### Login con email/password" y el párrafo "**Ojo:** este payload de `user` **no incluye** ..." que le sigue, por:

```markdown
`POST /api/auth/login/` — `{"email": "...", "password": "..."}` → `200` con:

```json
{
  "access": "<jwt>",
  "refresh": "<jwt o \"\" si JWT_AUTH_HTTPONLY>",
  "user": {
    "pk": 1,
    "email": "alguien@ciencias.unam.mx",
    "first_name": "Ana",
    "apellido1": "López",
    "apellido2": "Ruiz",
    "nombre_completo": "Ana López Ruiz",
    "roles": ["alumno"],
    "perfil_alumno": {"id": 3, "numero_cuenta": "312345678", "carrera": 5, "carrera_nombre": "Actuaría", "generacion": 2023},
    "perfil_academico": null,
    "perfil_asesor_academico": null
  }
}
```

`400` si las credenciales son inválidas (`{"non_field_errors": [...]}`).

El mismo objeto `user` es lo que devuelve `GET /api/auth/user/` (mismo serializer, `accounts.serializers.UserDetailsSerializer`), así que **el SPA conoce el rol desde el login mismo, sin una segunda llamada** — resuelve la [deuda técnica 0010](../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md), que el frontend suplía sondeando `GET /api/asesorias/registros/` y leyendo 200 vs 403.

- `roles` es una lista de claves estables: `"alumno"`, `"academico"`, `"asesor_academico"`. Vacía si el usuario no tiene ningún perfil de negocio.
- Cada `perfil_*` es un objeto o `null`. `perfil_asesor_academico.activo` puede ser `false`: el rol aparece en `roles` en cuanto el perfil existe, igual que hace la permission class `EsAsesorAcademico`.
- Solo `first_name` es escribible vía `PUT`/`PATCH /api/auth/user/`. Todo lo demás (incluidos `apellido1`/`apellido2`) es de solo lectura — la identidad la aprovisiona la SAE.
```

- [ ] **Step 3: Documentar las rutas nuevas de `asesorias` en la guía de API**

En `docs/development/api-frontend.md`, en la tabla de "### Rutas — vista de asesor (`registros`, `disponibilidades`)", agregar estas tres filas al final de la tabla:

```markdown
| `POST` | `/api/asesorias/registros/{id}/materias/quitar/` | quita una materia del registro — `{materia_id}`. `400` si la materia no está en el registro. **No cancela las asesorías ya agendadas.** Es `POST` y no `DELETE` porque este viewset no habilita el verbo `DELETE` (ver abajo) |
| `GET` | `/api/asesorias/disponibilidades/{id}/sesiones-futuras/` | `{"total": n, "sesiones": [{id, fecha, hora_inicio, alumno_nombre, materia_nombre}]}` — sesiones agendadas que aún no comienzan sobre ese bloque |
| `POST` | `/api/asesorias/disponibilidades/{id}/desactivar/` | `{cancelar_sesiones?: bool = false, motivo?: string}` → `{"disponibilidad": {...}, "sesiones_canceladas": n}`. Con `cancelar_sesiones=true` cancela todas las sesiones futuras y desactiva el bloque en una sola transacción; el motivo por defecto es `"El asesor dio de baja este horario."` |
```

En la tabla de "### Rutas — vista de alumno (búsqueda y booking)", agregar al final:

```markdown
| `GET` | `/api/asesorias/asesorias/?semestre=20262` | requerida | filtra el listado por `disponibilidad__registro__semestre`. Permisivo: un semestre desconocido devuelve `[]`, no `400` |
| `GET` | `/api/asesorias/asesorias/semestres/` | requerida | `["20262", "20261"]` — claves de semestre en las que el usuario tiene sesiones, de la más reciente a la más antigua. Sostiene los subtabs del historial |
```

Y en el párrafo que empieza con "`Asesoria.estado`: `agendada` (default) → ...", agregar al final:

```markdown

El payload de `Asesoria` incluye además `motivo_cancelacion` (string, vacío si no está cancelada), `cancelado_por` (id de `User` o `null`), `cancelado_por_rol` (`"alumno"` | `"asesor"` | `"otro"` | `null`), `alumno_nombre` y `asesor_nombre` — todos de solo lectura. `alumno` sigue siendo un id plano de `PerfilAlumno`; `alumno_nombre` es un campo hermano, no un reemplazo.
```

- [ ] **Step 4: Agregar la entrada de Changelog a la ADR 0019**

Al final de `docs/decisions/0019-transporte-login-google-id-token.md`, en la sección `## Changelog`, agregar:

```markdown
- **2026-08-04** — Implementada en el backend. `accounts.adapters.GoogleIdTokenAdapter` (subclase de `GoogleOAuth2Adapter`) sobreescribe `parse_token` para construir el `SocialToken` desde `data["id_token"]`; `GoogleLoginSerializer` exige `id_token`, rechaza `access_token` con `400`, y captura el `OAuth2Error` que levanta la verificación de allauth (`_verify_and_decode`) para traducirlo a `400 {"detail": ["El id_token de Google no es válido."]}` en vez de dejarlo propagar. Cobertura nueva en `accounts/tests/test_auth.py`: además de los tests con `complete_login` mockeado, `GoogleIdTokenVerificacionTests` ejercita la verificación criptográfica real (firma, issuer, expiración y `audience`) firmando su propio JWT y parcheando únicamente `jwtkit.fetch_key`, la única llamada de red. El frontend todavía manda `access_token` — su migración es el paso 9 del ledger (`docs/superpowers/plans/2026-08-04-login-y-componentes-PROGRESO.md`), y hasta que ocurra el login con Google no funciona end-to-end.
```

- [ ] **Step 5: Agregar la entrada de Changelog a la ADR 0016 (modelo)**

Al final de `docs/decisions/0016-asesorias-academicas.md`, en la sección `## Changelog`, agregar:

```markdown
- **2026-08-04** — Tres métodos de negocio nuevos en el modelo, sin cambios de esquema (ninguna migración): `RegistroAsesor.quitar_materia(materia)` (simétrico de `agregar_materia`; **no** cancela las asesorías ya agendadas, y falla con `ValidationError` si la materia no está en el registro), `Disponibilidad.sesiones_futuras()` (sesiones `agendada` que aún no comienzan — comparación de fecha **y** hora contra `timezone.localtime()`, no solo `fecha >= hoy`) y `Disponibilidad.desactivar(usuario, cancelar_sesiones, motivo)` (pone `activa=False` y opcionalmente cancela todas las sesiones futuras dentro de una sola transacción, devolviendo cuántas canceló). Motivados por el rediseño de las vistas de asesorías ([spec del paso 3](../superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md)); la superficie HTTP correspondiente está en el [Changelog de la ADR 0017](0017-asesorias-academicas-api.md#changelog).
```

- [ ] **Step 6: Agregar la entrada de Changelog a la ADR 0017 (API)**

Al final de `docs/decisions/0017-asesorias-academicas-api.md`, en la sección `## Changelog`, agregar:

```markdown
- **2026-08-04:** Superficie nueva pedida por el rediseño de vistas ([spec del paso 3](../superpowers/specs/2026-08-04-revision-vistas-asesorias-design.md)), toda siguiendo el patrón ya establecido de "vista delgada que invoca un método de modelo y traduce `ValidationError` a HTTP":
  - `GET /api/asesorias/disponibilidades/{id}/sesiones-futuras/` → `{total, sesiones}`. Se devuelve un sobre y no un array plano porque el consumidor principal es un condicional (`total > 0` → mostrar el modal de advertencia), y para dejar explícito que no es un endpoint de listado.
  - `POST /api/asesorias/disponibilidades/{id}/desactivar/` `{cancelar_sesiones, motivo}` → `{disponibilidad, sesiones_canceladas}`. Un solo endpoint sirve las dos opciones del modal de 3 acciones; el `PATCH` de `activa` sigue existiendo sin cambios para el toggle simple.
  - `POST /api/asesorias/registros/{id}/materias/quitar/` `{materia_id}`. Se eligió `POST` sobre `DELETE .../materias/{id}/` porque `http_method_names` de `RegistroAsesorViewSet` excluye `delete` deliberadamente (esta ADR fija que `RegistroAsesor` no acepta `DELETE`), y habilitar el verbo para la subruta también habilitaría `destroy` sobre el recurso.
  - `GET /api/asesorias/asesorias/?semestre=<clave>` (filtro permisivo: un semestre desconocido devuelve `[]`, no `400` — no hay modelo de calendario que defina qué claves son válidas, ver [deuda 0001](../technical-debt/0001-sin-modelo-calendario-academico.md)) y `GET /api/asesorias/asesorias/semestres/` (claves del usuario, orden descendente). El segundo existe para que los subtabs del historial no obliguen a cargar el historial completo, que es justo lo que el filtro evita. Cubre parcialmente la [deuda 0006](../technical-debt/0006-sin-paginacion-listados.md), no la reemplaza.
  - `AsesoriaSerializer` gana `motivo_cancelacion`, `cancelado_por`, `cancelado_por_rol`, `alumno_nombre` y `asesor_nombre` (todos de solo lectura), cerrando la [deuda técnica 0010](../technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md) del lado de Asesorías. `alumno` sigue siendo un id plano: los nombres son campos hermanos, no un reemplazo, para no romper a los consumidores actuales del payload.
```

- [ ] **Step 7: Cerrar la deuda técnica 0010**

En `docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md`, reemplazar la línea `**Estado:** Activa` por:

```markdown
**Estado:** Resuelta — 2026-08-04 ([plan de backend](../superpowers/plans/2026-08-04-login-oauth-backend.md), ver Changelog de [ADR 0017](../decisions/0017-asesorias-academicas-api.md))
```

y agregar al final del archivo:

```markdown
## Cómo se resolvió

Los tres puntos se cerraron en la misma pasada de backend:

1. **Detección de rol:** `GET /api/auth/user/` (y la clave `user` del body de login, mismo serializer) expone `roles` — lista de claves estables (`"alumno"`, `"academico"`, `"asesor_academico"`) — más un objeto por perfil o `null`, derivados de los `OneToOneField` inversos ya existentes. El sondeo de `GET /api/asesorias/registros/` (200 vs 403) deja de ser necesario. `roles` sigue el mismo criterio que la permission class `EsAsesorAcademico` (el perfil existe), no `activo`, para que la UI no oculte una pantalla a la que el backend sí da acceso.
2. **Nombre de la contraparte:** `AsesoriaSerializer` gana `alumno_nombre` y `asesor_nombre` (de solo lectura, vía `User.nombre_completo`), como campos **hermanos** de `alumno` — que sigue siendo un id plano, así que no se rompe ningún consumidor del payload, que era la preocupación registrada arriba en "Por qué era razonable". Se agregaron las dos direcciones a la vez y no solo la del asesor, precisamente porque la señal de revisión de este ítem nombraba el caso simétrico (Fase 2, el alumno viendo a su asesor) como el disparador de un segundo parche idéntico.
3. **Campos de cancelación:** `motivo_cancelacion` y `cancelado_por` entraron a `AsesoriaSerializer.Meta.fields`, más un `cancelado_por_rol` derivado (`"alumno"`/`"asesor"`/`"otro"`/`null`) — el id crudo de `User` no basta para renderizar el panel de cancelación, porque ninguna de las dos partes conoce el id de `User` de la otra.

Lo que **no** cubre: sigue sin existir un endpoint donde un usuario resuelva el nombre de otro a partir de un id de perfil arbitrario, fuera del contexto de una `Asesoria` que comparten. La señal de revisión de la Fase 3 (panel de administración, que necesita listar todos los roles de todos los usuarios) sigue vigente y no se resolvió aquí.
```

- [ ] **Step 8: Anotar la deuda técnica 0006**

En `docs/technical-debt/0006-sin-paginacion-listados.md`, agregar al final del archivo:

```markdown
## Cobertura parcial (2026-08-04)

`GET /api/asesorias/asesorias/?semestre=<clave>` filtra el historial por semestre (`disponibilidad__registro__semestre`), acompañado de `GET /api/asesorias/asesorias/semestres/` para construir los subtabs. Eso acota el listado que más riesgo tenía de crecer sin límite natural (el historial de un asesor con años de antigüedad — el ejemplo exacto que menciona la señal de revisión de arriba) al caso de uso más común: ver un semestre a la vez.

**Esto no resuelve este ítem.** Sigue sin haber convención de paginación de proyecto (`REST_FRAMEWORK` en `config/settings/base.py` no la define), el resto de los listados sigue devolviendo la colección completa, y un solo semestre con volumen suficiente vuelve a exhibir el problema. La señal de revisión sigue vigente tal cual.
```

- [ ] **Step 9: Mover la 0010 al índice de resueltas**

En `docs/technical-debt/README.md`, quitar la línea de la 0010 de la lista bajo `### Activa`, y reemplazar el contenido de la sección `### Resuelta` (hoy `_(vacío por ahora)_`) por:

```markdown
- [0010 — API no expone perfil ni rol del usuario autenticado](0010-api-no-expone-perfil-usuario-autenticado.md) — resuelta 2026-08-04
```

- [ ] **Step 10: Verificar que todos los archivos tocados existen y que no quedó referencia rota**

Run:
```bash
cd /home/hyfi/Development/atenea-fc
for f in docs/development/api-frontend.md \
         docs/decisions/0016-asesorias-academicas.md \
         docs/decisions/0017-asesorias-academicas-api.md \
         docs/decisions/0019-transporte-login-google-id-token.md \
         docs/technical-debt/0006-sin-paginacion-listados.md \
         docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md \
         docs/technical-debt/README.md \
         docs/superpowers/plans/2026-08-04-login-oauth-backend.md; do
  [ -f "$f" ] && echo "OK $f" || echo "MISSING $f"
done
grep -rn "access_token" docs/development/api-frontend.md
```
Expected: las 8 líneas dicen `OK`. El `grep` no debe reportar ninguna línea que siga describiendo `access_token` como el transporte vigente del login con Google (puede aparecer en texto histórico si lo hubiera; si aparece en la sección de "Login con Google", corrígelo).

- [ ] **Step 11: Correr la suite completa una última vez**

Run: `cd backend && uv run manage.py test`

Expected: PASS — toda la suite. Este task no toca código, pero cierra el plan: si algo está en rojo aquí, no se comitea la documentación.

- [ ] **Step 12: Commit**

```bash
git add docs/development/api-frontend.md \
        docs/decisions/0016-asesorias-academicas.md \
        docs/decisions/0017-asesorias-academicas-api.md \
        docs/decisions/0019-transporte-login-google-id-token.md \
        docs/technical-debt/0006-sin-paginacion-listados.md \
        docs/technical-debt/0010-api-no-expone-perfil-usuario-autenticado.md \
        docs/technical-debt/README.md
git commit -s -m "[docs] documentar transporte id_token, perfil/rol en la API y superficie nueva de asesorias" \
  -m "- api-frontend.md: login con Google pasa a id_token (access_token da
    400), payload de usuario con roles/perfiles, y las cinco rutas nuevas
    de asesorias con sus contratos exactos.
- Changelog en ADR 0019 (implementacion del transporte), ADR 0016
    (metodos de modelo nuevos) y ADR 0017 (superficie HTTP nueva, con la
    razon de cada decision de forma).
- Deuda tecnica 0010 pasa a Resuelta con la seccion 'Como se resolvio' y
    lo que deliberadamente no cubre; 0006 gana una nota de cobertura
    parcial y sigue Activa; README de deuda tecnica reindexado."
```

---

## Self-Review

**1. Cobertura de los requisitos**

| Requisito | Fuente | Task |
|---|---|---|
| Backend recibe y valida `id_token` con `audience=client_id`, sin dependencias nuevas | ADR 0019 / spec de login, "Cambios de backend" | 1, 2 |
| `GoogleLoginSerializer.validate` deja de exigir `access_token` | spec de login | 1 |
| Adapter propio que sobreescribe `parse_token` | spec de login, ADR 0019 | 1 |
| Sin cambios en `complete_login` ni en `_decode_id_token`/`_verify_and_decode` | spec de login | 1 (solo se hereda) |
| Los 3 tests existentes de `GoogleLoginTests` pasan a `{"id_token": ...}` | spec de login, "Testing" | 1 (Step 1) |
| Test de que `access_token`-solo se rechaza | spec de login, "Testing" | 1 (`test_rechaza_access_token_sin_id_token`) |
| Test de `audience` incorrecto sin mockear `complete_login` | spec de login, "Testing" | 2 (`test_id_token_con_audience_ajeno_devuelve_400`) |
| Tabla de error handling: `id_token` ausente / firma inválida / expirado / `audience` distinto / correo no provisionado | spec de login, "Error handling" | 1 (ausente, no provisionado), 2 (firma, expirado, audience) |
| Perfil/rol del usuario autenticado en una sola llamada | deuda 0010 punto 1; spec de vistas §2 | 3 |
| `motivo_cancelacion` + `cancelado_por` en `AsesoriaSerializer` | deuda 0010, tercer campo | 4 |
| Decisión explícita sobre el workaround del nombre de alumno | instrucción del paso 4 | 5 (se resuelve, con razón documentada; no se difiere) |
| Confirmar sesiones futuras antes de desactivar un bloque | spec de vistas §3, tabla de backend | 6, 7 |
| Acción transaccional "cancelar todas y desactivar" | spec de vistas §3, tabla de backend | 7 |
| Quitar una materia del `RegistroAsesor` + `quitar_materia()` | spec de vistas §3, tabla de backend | 8 |
| Filtro de historial por semestre (`?semestre=20262`, `disponibilidad__registro__semestre`) | spec de vistas §4 | 9 |
| Anotar en la deuda 0006 que el filtro la cubre parcialmente | spec de vistas §4 | 10 (Step 8) |
| ADRs/docs actualizados como parte del trabajo (patrón `d6ade66`) | instrucción del paso 4 | 10 |

Fuera de alcance a propósito, sin omisión silenciosa: el transporte/storage del JWT propio de Atenea (decisión 2 de ADR 0018, sin cambios), la invalidación de refresh token en logout (deuda 0007), el CSRF en cookie JWT (deuda 0009, decisión 6 de la spec de login), la paginación de proyecto (deuda 0006, solo cobertura parcial), el modelo de calendario académico (deuda 0001), y todo el frontend (`Landing.tsx`, `google.ts`, `AuthContext.tsx`, íconos, diálogos, tabs) — pasos 8 y 9 del ledger.

**2. Placeholders**

Sin `TBD`, sin "implementar después", sin "manejar los casos borde". Cada step de código trae el bloque completo listo para pegar; cada step de verificación trae el comando exacto y el resultado esperado, incluida la razón por la que falla en RED. Las dos únicas instrucciones condicionales son deliberadas y acotadas: el valor de `assertNumQueries` en la Task 5 (con el criterio explícito de qué protege el test) y "agrega solo los imports que falten" en archivos de test que el ejecutor tiene abiertos delante.

**3. Consistencia de tipos y nombres**

- `GoogleIdTokenAdapter` se define en la Task 1 y se importa con ese nombre exacto en `views.py` (Task 1) y en los tests de la Task 2.
- `User.nombre_completo` se define en la Task 3 y se consume en las Tasks 5 (`source="alumno.user.nombre_completo"`) y 6 (`SesionFuturaSerializer`).
- `Disponibilidad.sesiones_futuras()` se define en la Task 6 y se consume en la Task 7 (`desactivar`).
- `MateriaDelRegistroSerializer` se renombra en el Step 1 de la Task 8 y se usa con ese nombre en las dos acciones del mismo task.
- `AsesoriaViewSet.get_queryset` se reescribe en la Task 5 y se vuelve a reescribir completo en la Task 9 — el Task 9 muestra la versión final íntegra, incluidos los `select_related` que introdujo la Task 5, para que no se pierdan al reemplazar.
- Los tres campos nuevos de `AsesoriaSerializer` de la Task 4 y los dos de la Task 5 aparecen juntos en la lista final de `Meta.fields` que muestra la Task 5, sin duplicados.
- La restricción de DRF sobre campos declarados vs. `read_only_fields` se aplica de forma consistente en las Tasks 3, 4 y 5 y está enunciada una sola vez en Global Constraints.

**4. Validación empírica previa a este plan**

Contra el código real de este repo, antes de escribir: (a) `OAuth2Adapter.parse_token` de allauth hace `data["access_token"]` sin fallback, confirmando que hace falta el adapter propio; (b) `GoogleOAuth2Adapter._decode_id_token` verifica `audience=app.client_id` sin cambios en la librería instalada, y `did_fetch_access_token` es `False` en este flujo, así que la firma **sí** se verifica; (c) `jwtkit.verify_and_decode` levanta `OAuth2Error("Invalid id_token")` con `aud` incorrecto y decodifica correctamente con `aud` correcto, con `fetch_key` parcheado a `("HS256", <clave>)` — que es exactamente el arnés de test de la Task 2; (d) `GoogleIdTokenAdapter(RequestFactory().get("/")).get_provider().app.client_id` resuelve desde `SOCIALACCOUNT_PROVIDERS` en settings sin tocar la base de datos, por eso los tests lo leen dinámicamente en vez de hardcodear el valor de `.env`. Ninguna de estas cuatro es una inferencia sobre el comportamiento de la librería.

### Critical Files for Implementation
- /home/hyfi/Development/atenea-fc/backend/accounts/serializers.py
- /home/hyfi/Development/atenea-fc/backend/accounts/adapters.py
- /home/hyfi/Development/atenea-fc/backend/asesorias/models.py
- /home/hyfi/Development/atenea-fc/backend/asesorias/views.py
- /home/hyfi/Development/atenea-fc/backend/asesorias/serializers.py
</content>
