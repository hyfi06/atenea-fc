from django.urls import include, path, re_path

from .views import (
    AteneaLoginView,
    AteneaPasswordResetConfirmView,
    AteneaPasswordResetView,
    AteneaUserDetailsView,
    GoogleLoginView,
)

urlpatterns = [
    # Overrides de dj_rest_auth.urls: Django usa el primer match, así que estos
    # paths ganan. El include de abajo no se toca (sigue sirviendo logout, user,
    # token/refresh, password/change). Mantener los mismos `name` que usa
    # dj_rest_auth.urls, por si algo hace reverse().
    re_path(r"^login/?$", AteneaLoginView.as_view(), name="rest_login"),
    path(
        "password/reset/",
        AteneaPasswordResetView.as_view(),
        name="rest_password_reset",
    ),
    path(
        "password/reset/confirm/",
        AteneaPasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    path("user/", AteneaUserDetailsView.as_view(), name="rest_user_details"),
    path("", include("dj_rest_auth.urls")),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
]
