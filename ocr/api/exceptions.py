from http import HTTPStatus
from bottle import response

JSONAPI_ERROR_CODE = 9000
BACKEND_STATUS_CODE_ERROR_CODE = 9001
AUTHENTICATION_ERROR_CODE = 9002
PARAMETER_ERROR_CODE = 9003
SMB_CONNECTION_ERROR_CODE = 9004
UNIVERSAL_CHARACTER_RECOGNITIO_ERROR_CODE = 9005
PDF_TO_JPG_ERROR_CODE = 9006
MERGE_PDF_ERROR_CODE = 9007
TIFF_TO_JPG_ERROR_CODE = 9008
MERGE_TIFF_ERROR_CODE = 9009
MERGE_TXT_ERROR_CODE = 90010
MAKE_DIR_ERROR_CODE = 90011


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


class BackendStatusCodeError(JsonApiError):
    """
    调用后端状态码错误
    """
    _error = 'Backend Status Code Error'
    _error_code = BACKEND_STATUS_CODE_ERROR_CODE
    _msg_fmt = 'backend status code error, except status code %(except_code)d, actual status code %(actual_code)d'

    def __init__(self, msg_fmt=None, **kwargs):
        if msg_fmt:
            self._msg_fmt = msg_fmt
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            self._status_code = response.status_code
        super(BackendStatusCodeError, self).__init__(self._msg_fmt, **kwargs)


class AuthenticationError(JsonApiError):
    """
    身份验证失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'authentication error'
    _error_code = AUTHENTICATION_ERROR_CODE
    _msg_fmt = 'Api Authentication Error, username: %(parameter)s'

    def __init__(self, *args, **kwargs):
        super(AuthenticationError, self).__init__(self._msg_fmt, **kwargs)


class ParameterError(JsonApiError):
    """
    传入参数为空或错误
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'parameter error'
    _error_code = PARAMETER_ERROR_CODE
    _msg_fmt = 'Api Parameter Error, %(parameter)s: %(parameter_value)s'

    def __init__(self, *args, **kwargs):
        super(ParameterError, self).__init__(self._msg_fmt, **kwargs)


class SMBConnectionError(JsonApiError):
    """
    连接SMB失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'SMB ConnectionError error'
    _error_code = SMB_CONNECTION_ERROR_CODE
    _msg_fmt = 'Api SMB ConnectionError Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(SMBConnectionError, self).__init__(self._msg_fmt, **kwargs)


class UniversalCharacterRecognitioError(JsonApiError):
    """
    通用文字识别失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'universal character recognitio error'
    _error_code = UNIVERSAL_CHARACTER_RECOGNITIO_ERROR_CODE
    _msg_fmt = 'Api Universal Character Recognitio Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(UniversalCharacterRecognitioError, self).__init__(self._msg_fmt, **kwargs)


class PDFToJPGError(JsonApiError):
    """
    PDF转JPG失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'PDF to JPG error'
    _error_code = PDF_TO_JPG_ERROR_CODE
    _msg_fmt = 'Api PDF to JPG Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(PDFToJPGError, self).__init__(self._msg_fmt, **kwargs)


class MergePDFError(JsonApiError):
    """
    合并PDF失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'merge PDF error'
    _error_code = MERGE_PDF_ERROR_CODE
    _msg_fmt = 'Api Merge PDF Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(MergePDFError, self).__init__(self._msg_fmt, **kwargs)


class TIFFToJPGError(JsonApiError):
    """
    TIFF转JPG失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'TIFF to JPG error'
    _error_code = TIFF_TO_JPG_ERROR_CODE
    _msg_fmt = 'Api TIFF to JPG Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(TIFFToJPGError, self).__init__(self._msg_fmt, **kwargs)


class MergeTIFFError(JsonApiError):
    """
    合并TIFF失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'merge TIFF error'
    _error_code = MERGE_TIFF_ERROR_CODE
    _msg_fmt = 'Api Merge TIFF Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(MergeTIFFError, self).__init__(self._msg_fmt, **kwargs)


class MergeTxtError(JsonApiError):
    """
    合并TXT失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'merge txt error'
    _error_code = MERGE_TXT_ERROR_CODE
    _msg_fmt = 'Api Merge TXT Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(MergeTxtError, self).__init__(self._msg_fmt, **kwargs)


class MakeDirError(JsonApiError):
    """
    创建文件夹失败
    """
    _status_code = HTTPStatus.BAD_REQUEST.value
    _error = 'make dir error'
    _error_code = MAKE_DIR_ERROR_CODE
    _msg_fmt = 'Api make dir Error, %(data)s'

    def __init__(self, *args, **kwargs):
        super(MakeDirError, self).__init__(self._msg_fmt, **kwargs)



