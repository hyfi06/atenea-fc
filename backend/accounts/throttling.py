from rest_framework.throttling import ScopedRateThrottle


class CloudflareScopedRateThrottle(ScopedRateThrottle):
    """ScopedRateThrottle que identifica al cliente por CF-Connecting-IP en vez de
    X-Forwarded-For. La topología de prod es Cloudflare -> cloudflared -> nginx
    central -> este servicio (ver docs/development/despliegue-produccion.md).
    Cloudflare fija CF-Connecting-IP con la IP real del cliente en su borde y ese
    header no es falseable por el cliente (Cloudflare lo sobrescribe siempre),
    a diferencia de X-Forwarded-For: el nginx interno solo *agrega* con
    proxy_add_x_forwarded_for, sin descartar lo que traiga la petición entrante,
    así que confiar en XFF sin NUM_PROXIES deja que un atacante controle su propio
    bucket de throttle mandando un valor distinto en cada intento (hallazgo del
    review final del branch de fixes de seguridad, 2026-08-19).

    Fuera de Cloudflare (dev, tests) no hay CF-Connecting-IP: cae al
    comportamiento original de ScopedRateThrottle.
    """

    def get_ident(self, request):
        cf_connecting_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_connecting_ip:
            return cf_connecting_ip
        return super().get_ident(request)
