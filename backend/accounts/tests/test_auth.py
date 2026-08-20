import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import get_adapter as get_social_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User

BASE_DIR = Path(__file__).resolve().parents[2]


def _complete_login_as(email):
    def _complete_login(request, app, token, **kwargs):
        provider = get_social_adapter().get_provider(request, provider="google")
        user = User(email=email)
        account = SocialAccount(provider="google", uid=email)
        sociallogin = SocialLogin(user=user, account=account, provider=provider)
        sociallogin.email_addresses = [
            EmailAddress(email=email, verified=True, primary=True)
        ]
        return sociallogin

    return _complete_login


class GoogleLoginTests(APITestCase):
    def setUp(self):
        cache.clear()

    def _post_google_login(self):
        return self.client.post(
            "/api/auth/google/", {"id_token": "fake-token"}, format="json"
        )

    def _post_google_login_con_access_token(self):
        return self.client.post(
            "/api/auth/google/", {"access_token": "fake-token"}, format="json"
        )

    @patch.object(GoogleOAuth2Adapter, "complete_login")
    def test_rejects_unprovisioned_email(self, mock_complete_login):
        mock_complete_login.side_effect = _complete_login_as("nadie@ciencias.unam.mx")

        response = self._post_google_login()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    @patch.object(GoogleOAuth2Adapter, "complete_login")
    def test_connects_provisioned_email(self, mock_complete_login):
        user = User.objects.create_user("alguien@ciencias.unam.mx")
        mock_complete_login.side_effect = _complete_login_as(user.email)

        response = self._post_google_login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(
            SocialAccount.objects.filter(user=user, provider="google").exists()
        )

    @patch.object(GoogleOAuth2Adapter, "complete_login")
    def test_sets_cookies_when_httponly_configured(self, mock_complete_login):
        user = User.objects.create_user("google-cookies@ciencias.unam.mx")
        mock_complete_login.side_effect = _complete_login_as(user.email)

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            response = self._post_google_login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("atenea-access-token", response.cookies)
        self.assertIn("atenea-refresh-token", response.cookies)

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

    @patch.object(GoogleOAuth2Adapter, "complete_login")
    def test_google_no_devuelve_access_en_el_body_con_httponly(self, mock_complete_login):
        """SocialLoginView hereda get_response() de LoginView, así que arrastra
        el mismo hallazgo H1 que el login por password."""
        user = User.objects.create_user("google-sin-access@ciencias.unam.mx")
        mock_complete_login.side_effect = _complete_login_as(user.email)

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            response = self._post_google_login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["access"], "")
        self.assertEqual(response.data["refresh"], "")
        self.assertNotEqual(response.cookies["atenea-access-token"].value, "")


class PasswordResetLoginFlowTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_reset_then_login_then_refresh(self):
        user = User.objects.create_user("staff@ciencias.unam.mx", password="throwaway")

        response = self.client.post(
            "/api/auth/password/reset/", {"email": user.email}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r"/reset-password/([^/]+)/([^/]+)/", mail.outbox[0].body)
        self.assertIsNotNone(match)
        uid, token = match.group(1), match.group(2)

        response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password1": "NuevaClave123!",
                "new_password2": "NuevaClave123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "NuevaClave123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access = response.data["access"]
        refresh = response.data["refresh"]

        response = self.client.get(
            "/api/auth/user/", HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)

        response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


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
            "        for k in ('JWT_AUTH_HTTPONLY', 'JWT_AUTH_COOKIE', 'JWT_AUTH_REFRESH_COOKIE', 'JWT_AUTH_SECURE', 'JWT_AUTH_SAMESITE')\n"
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
        self.assertEqual(output["REST_AUTH"]["JWT_AUTH_SAMESITE"], "Lax")
        self.assertEqual(
            output["AUTH_CLASSES"], ["dj_rest_auth.jwt_auth.JWTCookieAuthentication"]
        )


from dj_rest_auth.app_settings import api_settings as dra_settings

PROD_COOKIE_SETTINGS = dict(
    JWT_AUTH_COOKIE="atenea-access-token",
    JWT_AUTH_REFRESH_COOKIE="atenea-refresh-token",
    JWT_AUTH_SECURE=True,
    JWT_AUTH_HTTPONLY=True,
    JWT_AUTH_SAMESITE="Lax",
)


class CookieBasedLoginTests(APITestCase):
    def setUp(self):
        cache.clear()

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
        self.assertEqual(access_cookie["samesite"], "Lax")
        self.assertEqual(refresh_cookie["samesite"], "Lax")
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
            # Con token_blacklist activo, LogoutView necesita el refresh token:
            # en modo httpOnly lo lee de esta cookie o responde 401.
            self.client.cookies["atenea-refresh-token"] = login_response.cookies["atenea-refresh-token"].value

            logout_response = self.client.post(
                "/api/auth/logout/",
                {},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {login_response.cookies['atenea-access-token'].value}",
            )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.cookies["atenea-access-token"].value, "")
        self.assertEqual(logout_response.cookies["atenea-access-token"]["max-age"], 0)
        self.assertEqual(logout_response.cookies["atenea-refresh-token"].value, "")
        self.assertEqual(logout_response.cookies["atenea-refresh-token"]["max-age"], 0)

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

    def test_login_no_devuelve_access_en_el_body_con_httponly(self):
        """ADR 0018: con la cookie httpOnly activa, ni access ni refresh viajan
        en el body — dj-rest-auth 7.2.0 solo vacía refresh."""
        user = User.objects.create_user("sin-access-body@ciencias.unam.mx", password="ClaveSegura123!")

        with patch.multiple(dra_settings, **PROD_COOKIE_SETTINGS):
            response = self.client.post(
                "/api/auth/login/",
                {"email": user.email, "password": "ClaveSegura123!"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["access"], "")
        self.assertEqual(response.data["refresh"], "")
        self.assertNotEqual(response.cookies["atenea-access-token"].value, "")


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

    def setUp(self):
        cache.clear()

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


class LoginThrottleTests(APITestCase):
    """Hallazgo H3: sin DEFAULT_THROTTLE_CLASSES, /api/auth/login/ acepta
    intentos ilimitados. ScopedRateThrottle + el scope dj_rest_auth que la
    librería ya declara lo acota a 5/min."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_sexto_intento_de_login_devuelve_429(self):
        User.objects.create_user("throttle@ciencias.unam.mx", password="ClaveSegura123!")

        for _ in range(5):
            response = self.client.post(
                "/api/auth/login/",
                {"email": "throttle@ciencias.unam.mx", "password": "clave-incorrecta"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            "/api/auth/login/",
            {"email": "throttle@ciencias.unam.mx", "password": "clave-incorrecta"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_throttle_usa_cf_connecting_ip_no_x_forwarded_for(self):
        """CF-Connecting-IP no es falseable por el cliente (Cloudflare lo
        sobrescribe en su borde); X-Forwarded-For sí, porque el nginx interno
        solo lo agrega sin descartar lo que traiga la peticion entrante."""
        User.objects.create_user("throttle-cf@ciencias.unam.mx", password="ClaveSegura123!")

        for i in range(5):
            response = self.client.post(
                "/api/auth/login/",
                {"email": "throttle-cf@ciencias.unam.mx", "password": "clave-incorrecta"},
                format="json",
                HTTP_X_FORWARDED_FOR=f"1.2.3.{i}",  # distinto en cada intento
                HTTP_CF_CONNECTING_IP="9.9.9.9",  # mismo cliente real
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            "/api/auth/login/",
            {"email": "throttle-cf@ciencias.unam.mx", "password": "clave-incorrecta"},
            format="json",
            HTTP_X_FORWARDED_FOR="1.2.3.99",
            HTTP_CF_CONNECTING_IP="9.9.9.9",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


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
