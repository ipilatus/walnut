# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from json import loads as json_loads

import pytz
from bottle import request
from redis import Redis

from evm.common.utils.redis_util import get_redis_pool_connection

logger = logging.getLogger(__name__)
utc_tz = pytz.timezone('UTC')  # UTC 时区
local_tz = pytz.timezone('Asia/Shanghai')  # 本地时区


class TokenPlugin(object):
    """
    刷新 token 过期时间的插件
    """

    name = 'token'
    api = 2
    token_utc_datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ %Z %z'
    token_local_datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self, token_header, token_param, token_prefix_key, token_expired_sec, redis_url):
        self.token_header = token_header
        self.token_param = token_param
        self.token_prefix_key = token_prefix_key
        self.token_expired_sec = token_expired_sec
        self.redis_url = redis_url

    def setup(self, app):
        for other in app.plugins:
            if not isinstance(other, TokenPlugin):
                continue

    def apply(self, callback, route):

        def renew_token():
            auth_token = None
            if self.token_header in request.headers:
                auth_token = request.headers[self.token_header]
                if logger.isEnabledFor(logging.DEBUG) and auth_token:
                    logger.debug('find token in headers, %s', auth_token)

            if not auth_token and self.token_param in request.forms:
                auth_token = request.forms[self.token_param]
                if logger.isEnabledFor(logging.DEBUG) and auth_token:
                    logger.debug('find token in forms, %s', auth_token)

            if not auth_token and self.token_param in request.query:
                auth_token = request.query[self.token_param]
                if logger.isEnabledFor(logging.DEBUG) and auth_token:
                    logger.debug('find token in url, %s', auth_token)

            if auth_token:
                request.token = auth_token
                redis_key = self.token_prefix_key + auth_token
                connection_pool = get_redis_pool_connection(self.redis_url)
                redis = Redis(connection_pool=connection_pool)
                row = redis.get(redis_key)
                if row:
                    json_data = json_loads(row.decode())
                    request.token_data = json_data
                    expires_at = datetime.strptime(json_data['token']['expires_at'] + ' UTC +0000',
                                                   self.token_utc_datetime_format)
                    utcnow = datetime.now(tz=utc_tz)
                    expired_sec = int((expires_at - utcnow).total_seconds())
                    if expired_sec > 0:
                        ttl_sec = self.token_expired_sec if self.token_expired_sec < expired_sec else expired_sec
                        redis.expire(redis_key, ttl_sec)

        def wrapper(*args, **kwargs):
            renew_token()
            rv = callback(*args, **kwargs)
            return rv

        return wrapper


Plugin = TokenPlugin
