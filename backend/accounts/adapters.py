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
