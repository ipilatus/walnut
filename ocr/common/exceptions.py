from http import HTTPStatus
# from .i18n import _

JSONAPI_ERROR_CODE = 9000
AUTH_TOKEN_NOT_FOUND_ERROR_CODE = 9001
HEADER_NOT_FOUND_ERROR_CODE = 9002


class JsonApiError(Exception):
    _status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    _error = 'json api error'
    _error_code = JSONAPI_ERROR_CODE

    def __init__(self, err, status_code=None, error=None, error_code=None, **kwargs):
        self.message = err % kwargs
        super(JsonApiError, self).__init__(self.message)
        if error:
            self._error = error
        if status_code:
            self._status_code = status_code
        if error_code:
            self._error_code = error_code

    # http response status code
    status_code = property(fget=lambda self: self._status_code, fset=lambda self, x: setattr(self, '_status_code', x))

    # jsonapi error attribute value in error object
    error = property(fget=lambda self: self._error, fset=lambda self, x: setattr(self, '_error', x))

    # jsonapi error code attribute value in error object
    error_code = property(fget=lambda self: self._error_code, fset=lambda self, x: setattr(self, '_error_code', x))


class HeaderNotFoundError(JsonApiError):
    """
    消息头 没有找到
    """
    _error = 'header not found'
    _error_code = HEADER_NOT_FOUND_ERROR_CODE
    _msg_fmt = 'header %(header)s not found'

    def __init__(self, *args, **kwargs):
        super(HeaderNotFoundError, self).__init__(self._msg_fmt, **kwargs)


class AuthTokenNotFoundError(JsonApiError):
    """
    Token 没有找到
    """
    _status_code = HTTPStatus.FORBIDDEN.value
    _error = 'auth token not found'
    _error_code = AUTH_TOKEN_NOT_FOUND_ERROR_CODE
    _msg_fmt = 'token %(token)s not found'

    def __init__(self, *args, **kwargs):
        super(AuthTokenNotFoundError, self).__init__(self._msg_fmt, **kwargs)
