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

        access_token = attrs.get("access_token")
        code = attrs.get("code")

        if access_token:
            tokens_to_parse = {"access_token": access_token}
            token = access_token
            id_token = attrs.get("id_token")
            if id_token:
                tokens_to_parse["id_token"] = id_token
        elif code:
            self.set_callback_url(view=view, adapter_class=adapter_class)
            self.client_class = getattr(view, "client_class", None)

            if not self.client_class:
                raise serializers.ValidationError(_("Define client_class in view"))

            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope_delimiter=adapter.scope_delimiter,
                headers=adapter.headers,
                basic_auth=adapter.basic_auth,
            )
            try:
                token = client.get_access_token(code)
            except Exception as ex:
                raise serializers.ValidationError(_("Failed to exchange code for access token")) from ex
            access_token = token["access_token"]
            tokens_to_parse = {"access_token": access_token}

            for key in ["refresh_token", "id_token", adapter.expires_in_key]:
                if key in token:
                    tokens_to_parse[key] = token[key]
        else:
            raise serializers.ValidationError(_("Incorrect input. access_token or code is required."))

        social_token = adapter.parse_token(tokens_to_parse)
        social_token.app = app

        try:
            if adapter.provider_id == "google" and not code:
                login = self.get_social_login(adapter, app, social_token, response={"id_token": id_token})
            else:
                login = self.get_social_login(adapter, app, social_token, token)
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
