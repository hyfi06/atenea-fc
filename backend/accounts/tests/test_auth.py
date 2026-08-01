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
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

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
    def _post_google_login(self):
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


class PasswordResetLoginFlowTests(APITestCase):
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
