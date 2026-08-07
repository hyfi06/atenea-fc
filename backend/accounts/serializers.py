from allauth.account.utils import user_pk_to_url_str
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as BasePasswordResetSerializer
from dj_rest_auth.serializers import UserDetailsSerializer as BaseUserDetailsSerializer
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
        except OAuth2Error:
            # allauth levanta OAuth2Error cuando el id_token no pasa la
            # verificación de firma, issuer, expiración o audience
            # (_verify_and_decode -> jwtkit.verify_and_decode). Sin este
            # except, un token inválido revienta como error no manejado en
            # vez de dar el 400 que fija la spec de login.
            raise serializers.ValidationError(_("El id_token de Google no es válido."))

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
