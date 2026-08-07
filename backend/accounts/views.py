from dj_rest_auth.registration.views import SocialLoginView

from .adapters import GoogleIdTokenAdapter
from .serializers import GoogleLoginSerializer


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleIdTokenAdapter
    serializer_class = GoogleLoginSerializer
