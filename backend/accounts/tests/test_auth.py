import re
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import get_adapter as get_social_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


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
