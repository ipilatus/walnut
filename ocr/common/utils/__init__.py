from bottle import BaseResponse


class RequestWrapper(object):
    _method = None
    _headers = None
    _path = None
    _query_string = None
    _body = None

    def __init__(self, request=None, method=None, headers=None, path=None, query_string=None, body=None):
        if request:
            self._method = request.method
            self._headers = request.headers
            self._path = request.path
            self._query_string = request.query_string
            self._body = request.body
        if method:
            self._method = method
        if headers:
            self._headers = headers
        if path:
            self._path = path
        if query_string:
            self._query_string = query_string
        if body:
            self._body = body

    def get_header(self, header):
        if self._headers and header in self._headers:
            return self._headers[header]
        else:
            return None

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, method):
        self._method = method

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._headers = headers

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def query_string(self):
        return self._query_string

    @query_string.setter
    def query_string(self, query_string):
        self._query_string = query_string

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body


class ResponseWrapper(BaseResponse):
    pass
