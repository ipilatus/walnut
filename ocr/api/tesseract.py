try:
    from PIL import Image
except ImportError:
    import Image

import shlex
import subprocess
import sys
import os
from ocr.config import tesseract_cmd
from ocr.api.exceptions import TesseractNotFoundError, TesseractError


def get_errors(error_string):
    return u' '.join(
        line for line in error_string.decode('utf-8').splitlines()
    ).strip()


def subprocess_args(include_stdout=True):
    kwargs = {
        'stdin': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'startupinfo': None,
        'env': None
    }

    if hasattr(subprocess, 'STARTUPINFO'):
        kwargs['startupinfo'] = subprocess.STARTUPINFO()
        kwargs['startupinfo'].dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['env'] = os.environ

    if include_stdout:
        kwargs['stdout'] = subprocess.PIPE

    return kwargs


def run_tesseract(input_filename, output_filename_base, extension, lang, config='', nice=0):
    cmd_args = []

    if not sys.platform.startswith('win32') and nice != 0:
        cmd_args += ('nice', '-n', str(nice))

    cmd_args += (tesseract_cmd, input_filename, output_filename_base)

    if lang is not None:
        cmd_args += ('-l', lang)

    cmd_args += shlex.split(config)

    if len(extension) > 1:
        for i in range(0, len(extension)):
            cmd_args.append(extension[i])
    else:
        cmd_args.append(extension[0])

    try:
        proc = subprocess.Popen(cmd_args, **subprocess_args())
    except OSError:
        raise TesseractNotFoundError()

    status_code, error_string = proc.wait(), proc.stderr.read()
    proc.stdin.close()
    proc.stdout.close()
    proc.stderr.close()

    if status_code:
        raise TesseractError(status_code, get_errors(error_string))

    return True