from django.urls import include, path, re_path

from .views import AteneaLoginView, GoogleLoginView

urlpatterns = [
    # Override del login de dj_rest_auth.urls: Django usa el primer match, así
    # que este path gana. El include de abajo no se toca (sigue sirviendo
    # logout, password/reset, user, token/refresh). Mantener name="rest_login",
    # el mismo que usa dj_rest_auth.urls, por si algo hace reverse().
    re_path(r"^login/?$", AteneaLoginView.as_view(), name="rest_login"),
    path("", include("dj_rest_auth.urls")),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
]
