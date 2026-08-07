from allauth.account.utils import user_pk_to_url_str
from allauth.socialaccount.helpers import complete_social_login
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as BasePasswordResetSerializer
from requests.exceptions import HTTPError
from rest_framework import serializers


class GoogleLoginSerializer(SocialLoginSerializer):
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


def atenea_password_reset_url_generator(request, user, temp_key):
    uid = user_pk_to_url_str(user)
    return f"{settings.FRONTEND_URL}/reset-password/{uid}/{temp_key}/"


class PasswordResetSerializer(BasePasswordResetSerializer):
    def get_email_options(self):
        return {"url_generator": atenea_password_reset_url_generator}
