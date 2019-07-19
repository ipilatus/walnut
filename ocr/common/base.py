import logging

from bottle import Bottle
from .jsonapi import JsonFormatting


logger = logging.getLogger(__name__)


class Base(object):
    def __init__(self, *args, **kwargs):
        self.app = Bottle()
        self.app.install(JsonFormatting())