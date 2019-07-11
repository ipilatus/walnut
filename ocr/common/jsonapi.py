import logging
from json import dumps as json_dumps
from json import loads as json_loads

from bottle import Bottle
from bottle import ERROR_PAGE_TEMPLATE
from bottle import HTTPResponse
from bottle import request
from bottle import response
from bottle import template
from bottle import tob
# from sqlalchemy.exc import SQLAlchemyError

from .exceptions import JsonApiError, SQLALCHEMY_ERROR_CODE

logger = logging.getLogger(__name__)


class JsonFormatting(object):
    """
    Bottle plugin which encapsulates results and error in a json object. 
    Intended for instances where you want to use Bottle as an api server.
    """

    name = 'json_formatting'
    api = 2

    # pylint: disable=C0103,W0102
    ALL_TYPES = '*/*'

    statuses = {
        0: ('success', 200),
        1: ('error', 500),
        2: ('internal failure', 500),
    }

    def __init__(self, supported_types=['*/*'],
                 debug=False):
        self.debug = debug
        self.app = None
        self.function_type = None
        self.function_original = None
        self.supported_types = supported_types
        self.ALL_TYPES = JsonFormatting.ALL_TYPES

    def setup(self, app):
        """
        Handle plugin install
        :param app: 
        :return: 
        """
        self.app = app
        self.function_type = type(app.default_error_handler)
        self.function_original = app.default_error_handler
        self.app.default_error_handler = self.function_type(
            self.custom_error_handler, app)

    # pylint: disable=W0613
    def apply(self, callback, route):
        """
        Handle route callbacks
        :param callback: 
        :param route: 
        :return: 
        """
        if not json_dumps:
            return callback

        def validate_json_string(myjson):
            """判断是否是json string"""
            try:
                json_object = json_loads(myjson)
            except ValueError as e:
                return False, None
            return True, json_object

        def wrapper(*a, **ka):
            """Encapsulate the result in json"""

            try:
                output = callback(*a, **ka)
                if self.in_supported_types(request.headers.get('Accept', '')) and not isinstance(output, HTTPResponse):
                    json_data = output
                    if isinstance(output, str):  # 说明是 string
                        result = validate_json_string(output)  # 判断是否是 json string
                        if result[0] is True:  # 是 json string
                            if logger.isEnabledFor(logging.DEBUG):
                                logger.debug('json, %s', output)
                            json_data = result[1]

                    response_object = self.get_response_object(0)
                    response_object['data'] = json_data
                    json_response = json_dumps(response_object)
                    response.content_type = 'application/json'
                    return json_response

                return output

            except JsonApiError as e:
                logger.exception('JsonApiError, %s', e)
                response_object = self.get_response_object(1)
                response_object['error'] = {
                    'error_code': e.error_code,
                    'error': e.error,
                    'message': str(e)
                }
                response_object['status_code'] =  e.status_code
                json_response = json_dumps(response_object)
                response.content_type = 'application/json'
                response.status = e.status_code
                return json_response

            # except SQLAlchemyError as e:
            #     logger.exception('SQLAlchemyError, %s', e)
            #     response_object = self.get_response_object(1)
            #     response_object['error'] = {
            #         'error_code': SQLALCHEMY_ERROR_CODE,
            #         'error': 'SQLAlchemy Error',
            #         'message': str(e)
            #     }
            #     json_response = json_dumps(response_object)
            #     response.content_type = 'application/json'
            #     return json_response

        return wrapper

    def in_supported_types(self, accept_request_header):
        """
        Test accept request header in supprted types
        :param accept_request_header: 
        :return: 
        """
        if self.ALL_TYPES in self.supported_types:
            return True
        accepts = []
        for item in accept_request_header.split(','):
            accepts.append(item.strip().split(';')[0])
        if self.ALL_TYPES in accepts:
            return True
        for this_type in self.supported_types:
            if this_type in accepts:
                return True
        return False

    def close(self):
        """
        Put the original function back on uninstall
        :return: 
        """
        self.app.default_error_handler = self.function_type(
            self.function_original, self.app, Bottle)

    def get_response_object(self, status):
        """
        Helper for building the json object 
        :param status: 
        :return: 
        """
        # global statuses
        if status in self.statuses:
            if response.status_code == 200:  # 如果状态码为200，需要根据 status 进行判断
                response.status = self.statuses.get(status)[1]
            status_code = response.status_code
            if status_code >= 400:  # 4xx, 5xx 错误
                status_message = 'error'
            else:
                status_message = 'success'
            json_response = {
                'status': status_message,
                'status_code': status_code,
                'data': None,
            }
            return json_response
        else:
            return self.get_response_object(2)

    def custom_error_handler(self, res, error):
        """
        Monkey patch method for json formatting error responses
        :param res: 
        :param error: 
        :return: 
        """
        # when the accept type matches the jsonFormatting configuration
        if self.in_supported_types(request.headers.get('Accept', '')):
            response_object = self.get_response_object(1)
            response_object['error'] = {
                'error_code': error.status_code,
                'error': error.status_line,
                'message': error.body,
            }
            if self.debug:
                response_object['debug'] = {
                    'exception': repr(error.exception),
                    'traceback': error.traceback,
                }
            json_response = json_dumps(response_object)
            response.content_type = 'application/json'
            return json_response
        else:
            return tob(template(ERROR_PAGE_TEMPLATE, e=error))
