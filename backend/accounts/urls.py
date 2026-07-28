from django.urls import include, path

from .views import GoogleLoginView

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("google/", GoogleLoginView.as_view(), name="google_login"),
]
