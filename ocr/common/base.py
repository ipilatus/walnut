import logging

from bottle import Bottle
from .jsonapi import JsonFormatting


logger = logging.getLogger(__name__)


class Base(object):
    def __init__(self, *args, **kwargs):
        self.app = Bottle()
        self.app.install(JsonFormatting())
        # self.app.install(
        #     TokenPlugin(token_header=evm_config.auth_token_header, token_param=evm_config.auth_token_param,
        #                 token_prefix_key=evm_config.token_prefix_key,
        #                 token_expired_sec=evm_config.token_expired_sec, redis_url=evm_config.redis_url))