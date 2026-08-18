from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import LoginView

from .adapters import GoogleIdTokenAdapter
from .serializers import GoogleLoginSerializer


class LoginResponseSinAccessEnBodyMixin:
    """dj-rest-auth 7.2.0 (LoginView.get_response) vacía `refresh` del body
    cuando JWT_AUTH_HTTPONLY=True pero deja `access` en texto plano — el JWT
    queda expuesto a cualquier JS que lea la respuesta del login, justo lo
    que ADR 0018 dice que la cookie httpOnly debe evitar. Copia
    get_response() de dj_rest_auth.views.LoginView (v7.2.0) con una sola
    línea distinta: `access` se vacía igual que `refresh`."""

    def get_response(self):
        from dj_rest_auth.app_settings import api_settings
        from django.utils import timezone
        from rest_framework import status
        from rest_framework.response import Response

        serializer_class = self.get_response_serializer()

        if api_settings.USE_JWT:
            from rest_framework_simplejwt.settings import api_settings as jwt_settings

            access_token_expiration = timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME
            refresh_token_expiration = timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME
            return_expiration_times = api_settings.JWT_AUTH_RETURN_EXPIRATION
            auth_httponly = api_settings.JWT_AUTH_HTTPONLY

            data = {"user": self.user, "access": self.access_token}

            if not auth_httponly:
                data["refresh"] = self.refresh_token
            else:
                # Ninguno de los dos tokens debe viajar en el body cuando el
                # transporte es la cookie httpOnly (ADR 0018).
                data["refresh"] = ""
                data["access"] = ""

            if return_expiration_times:
                data["access_expiration"] = access_token_expiration
                data["refresh_expiration"] = refresh_token_expiration

            serializer = serializer_class(instance=data, context=self.get_serializer_context())
        elif self.token:
            serializer = serializer_class(instance=self.token, context=self.get_serializer_context())
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

        response = Response(serializer.data, status=status.HTTP_200_OK)
        if api_settings.USE_JWT:
            from dj_rest_auth.jwt_auth import set_jwt_cookies

            set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response


class AteneaLoginView(LoginResponseSinAccessEnBodyMixin, LoginView):
    pass


class GoogleLoginView(LoginResponseSinAccessEnBodyMixin, SocialLoginView):
    adapter_class = GoogleIdTokenAdapter
    serializer_class = GoogleLoginSerializer
