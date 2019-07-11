import logging
from urllib.parse import urlparse

from urllib3 import HTTPConnectionPool

CONN_POOL_MAX_SIZE = 500  # 连接池中的最大连接数
http_connection_pool_container = {}

logger = logging.getLogger(__name__)


class HTTPConnectionPoolWrapper(object):
    def __init__(self, pool):
        self.pool = pool

    def request(self, method, url, fields=None, headers=None, **urlopen_kw):
        r = urlparse(url)  # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        url = url[len(r.scheme) + len(r.netloc) + 3:]
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('fixed url: %s', url)

        return self.pool.request(method, url, fields, headers, **urlopen_kw)


def get_http_connection_pool(host=None, port=80, url=None, *args, **kwargs):
    if host:
        key = (host, port)

    elif url:
        o = urlparse(url)
        key = (o.hostname, o.port)

    else:
        raise Exception('host and url is empty')

    return _get_http_connection_pool(key)


def _get_http_connection_pool(key):
    if key not in http_connection_pool_container:
        pool = HTTPConnectionPool(host=key[0], port=key[1], maxsize=CONN_POOL_MAX_SIZE)
        http_connection_pool_container[key] = pool

    return HTTPConnectionPoolWrapper(http_connection_pool_container[key])
