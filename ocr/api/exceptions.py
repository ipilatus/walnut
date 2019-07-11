from ocr.config import tesseract_cmd


class ParameterError(Exception):
    def __init__(self, data):
        super().__init__(self)
        self.data = data
        self.args = ('Incorrect parameters : %s' % data)

    def __str__(self):
        return self.data


class TesseractNotFoundError(EnvironmentError):
    def __init__(self):
        super(TesseractNotFoundError, self).__init__(
            tesseract_cmd + " is not installed or it's not in your path"
        )


class TesseractError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        self.args = (status, message)

