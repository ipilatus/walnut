import functools
import logging
# from logging import basicConfig
from logging.config import fileConfig
from urllib.parse import unquote as urlunquote

import bottle

from ocr.api.recognition import Recognition
from ocr.config import logging_conf_path

logger = logging.getLogger(__name__)

# fmt = '%Y-%m-%d %H:%M:%S'
# format = '%(asctime)s:%(levelname)s [%(thread)d:%(process)d] (%(module)s:%(lineno)d) - %(message)s'
# if not os.path.exists(logging_file_path):
#     os.makedirs(logging_conf_path)
# basicConfig(filename=logging_file_path, format=format, datefmt=fmt, level=logging.DEBUG)
fileConfig(logging_conf_path, disable_existing_loggers=False)


default_app = bottle.default_app()

default_app.mount('ocr', Recognition().app)


app = default_app

# bottle patch
bottle.urlunquote = functools.partial(urlunquote, encoding='utf-8')


if __name__ == '__main__':
    bottle.run(app=app, host='127.0.0.1', port=8000)