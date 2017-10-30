
import requests
import requests.adapters
import ssl


class TLSLowerAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = ssl.SSLContext(self.ssl_version)
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = ssl.SSLContext(self.ssl_version)
        return super().proxy_manager_for(*args, **kwargs)


class TLSv1Adapter(TLSLowerAdapter):
    ssl_version = ssl.PROTOCOL_TLSv1


class TLSv1_1Adapter(TLSLowerAdapter):
    ssl_version = ssl.PROTOCOL_TLSv1_1


class TLSv1_2Adapter(TLSLowerAdapter):
    ssl_version = ssl.PROTOCOL_TLSv1_2


def method_tls_fallback(url, method, *args, **kwargs):
    """
    Try to perform a method on an url using requests.
    If the get request fails due to an SSLError, we try to lower
    the TLS version until it finally succeeds.
    """
    # Try to get as-is
    try:
        session = requests.Session()
        return getattr(session, method)(url, *args, **kwargs)
    except requests.exceptions.SSLError:
        pass

    err = None
    for adapter in [TLSv1_2Adapter, TLSv1_1Adapter, TLSv1Adapter]:
        try:
            session = requests.Session()
            session.mount("https://", adapter())
            return getattr(session, method)(url, *args, **kwargs)
        except requests.exceptions.SSLError as e:
            err = e
    raise err


def get_tls_fallback(url, *args, **kwargs):
    return method_tls_fallback(url, "get", *args, **kwargs)


def post_tls_fallback(url, *args, **kwargs):
    return method_tls_fallback(url, "post", *args, **kwargs)
