import json
import logging
import os

import pytesseract as ts
from bottle import request

from ocr.api import FileType
from ocr.api import LangType
from ocr.api import ProtocolType
from ocr.api import RecognitionMixin
from ocr.api import optImageForOCR
from ocr.api import run_tesseract
from ocr.common.base import Base
from ocr.api.exceptions import ParameterError, UniversalCharacterRecognitioError

logger = logging.getLogger(__name__)


DEFAULT_INPUT_TYPE = [FileType.PNG, FileType.JPEG, FileType.JPG, FileType.TIF, FileType.TIFF, FileType.PDF]  # 支持的上传文件格式
DEFAULT_OUTPUT_TYPE = [FileType.PDF, FileType.TXT]  # 支持的输出文件类型
DEFAULT_LANG = [LangType.CHI_SIM, LangType.CHI_TRA, LangType.ENG, LangType.JPN]  # 支持的语言类型
PREFIX = 'tess_'  # 传入文件保存时名称前缀
SUFFIX = '_out'  # 识别结果保存时名称后缀


def image_to_pdf_or_hocr_wrapper(image_file_path, result_file_path, lang, config):
    data = ts.image_to_pdf_or_hocr(image_file_path, lang, config)
    with open(result_file_path, 'wb') as f:
        f.write(data)


class Recognition(Base, RecognitionMixin):

    def __init__(self, *args, **kwargs):
        super(Recognition, self).__init__(*args, **kwargs)
        self.dispatch()

    """
    origin_folder
    process_folder
    result_folder
    """

    def recognition(self):
        """
        通用文字识别
        :return:
        """
        try:
            lang = request.forms.get('language').split(',')
            output_type = request.forms.get('outputType').split(',')
            dpi = request.forms.get('dpi')
            correct = request.forms.get('correct')
            enhance = request.forms.get('enhance')
            callback_url = request.forms.get('callbackUrl')
            file = request.files.get('file')
            input = json.loads(request.forms.get('inputInfo')) if request.forms.get('inputInfo') else None
            output = json.loads(request.forms.get('outputInfo')) if request.forms.get('outputInfo') else None
            encrypt_decrypt = json.loads(request.forms.get('encryptDecrypt')) if request.forms.get('encryptDecrypt') else None
            logger.debug('param: %s', json.dumps(request.forms.dict))
            encrypt_flag = decrypt_flag = True if encrypt_decrypt else False

            input_folder, process_folder, output_folder, now_timestamp = self.make_dir()

            file_type = ''
            no_extension_filename = ''
            input_file_path = ''

            if file:
                filename = file.filename
                no_extension_filename, file_type = os.path.splitext(filename)
                input_file_path = os.path.join(input_folder, file.filename)
                file.save(input_file_path)
                logger.debug('input file path: %s, file save successful.', input_file_path)

            elif input:
                protocol = input['protocol']
                host = input['host']
                host_name = input['hostName']
                username = input['userName']
                password = input['password']
                domain = input['domain'] or ''
                remote_file_path = input['filePath']

                shared_folder_name = remote_file_path.split('\\')[0]
                _, filename = os.path.split(remote_file_path)
                no_extension_filename, file_type = os.path.splitext(filename)

                input_file_path = os.path.join(input_folder, filename)

                if protocol == ProtocolType.SMB:
                    self.download_file_by_smb(host, host_name, username, password, domain, shared_folder_name, remote_file_path,
                                              input_file_path)
                else:
                    raise ParameterError(parameter='protocol', parameter_value=protocol)

            else:
                raise ParameterError(parameter='file', parameter_value='None')

            if decrypt_flag:
                aes_mode = encrypt_decrypt['mode']
                aes_key = encrypt_decrypt['key']
                aes_offset = encrypt_decrypt['offset']
                aes_encoded = encrypt_decrypt.get('encoded')
                # aes_complement = encrypt_decrypt.get('complement')

                self.aes_decrypt(input_file_path, aes_key, aes_offset, aes_mode, aes_encoded)

            if self.allowed_lang(lang) and self.allowed_input_file_type(file_type) \
                    and self.allowed_output_type(output_type):
                config = '--oem 1 --dpi ' + dpi if dpi else '--oem 1'
                lang = lang[0] if len(lang) == 1 else '+'.join(lang)
                logger.debug('lang: %s', lang)
                logger.debug('config: %s', config)
                logger.debug('upload file type: %s', file_type)

                kwargs = {
                    'lang': lang,
                    'output_type': output_type,
                    'config': config,
                    'correct': correct,
                    'enhance': enhance,
                    'input_file_path': input_file_path,
                    'process_folder': process_folder,
                    'output_folder': output_folder,
                    'output_filename': no_extension_filename + SUFFIX
                }

                if file_type == FileType.PDF:
                    self.handle_pdf(**kwargs)

                if file_type in [FileType.TIFF, FileType.TIF]:
                    self.handle_tiff_or_tif(**kwargs)

                if file_type in [FileType.JPG, FileType.JPEG, FileType.PNG]:
                    self.handle_jpg_or_png(**kwargs)

            else:
                raise ParameterError(parameter='parameter', parameter_value=str(lang + 'or' + file_type + 'or' + output_type))

            if output:
                protocol = output['protocol']
                share_folder_name = output['sharedFolderName']
                url = output['filePath']
                host = output['host']
                port = output['hostName']
                username = output['userName']
                password = output['password']
                overwrite = output.get('overwrite', False)
                output_file_name = no_extension_filename if overwrite else no_extension_filename + SUFFIX

                # search output_folder
                output_folder_dir = os.listdir(output_folder)

                for i in output_folder_dir:

                    result_file_path = os.path.join(output_folder, i)
                    logger.debug('AED or SMB file path', result_file_path)

                    if decrypt_flag:
                        aes_mode = encrypt_decrypt['mode']
                        aes_key = encrypt_decrypt['key']
                        aes_offset = encrypt_decrypt['offset']
                        aes_encoded = encrypt_decrypt.get('encoded')
                        # aes_complement = encrypt_decrypt.get('complement')

                        self.aes_decrypt(result_file_path, aes_key, aes_offset, aes_mode, aes_encoded)

                    if protocol == 'smb':
                        self.upload_file_by_smb(host, port, username, password, share_folder_name, url, result_file_path)

            if callback_url:
                self.ocr_finished()

        except Exception as e:
            raise UniversalCharacterRecognitioError(data=str(e))

    def allowed_lang(self, lang):
        return lang and len(lang) <= 2 and set(lang).issubset(DEFAULT_LANG)

    def allowed_output_type(self, output_type):
        return output_type and set(output_type).issubset(DEFAULT_OUTPUT_TYPE)

    def allowed_input_file_type(self, input_file_type):
        return input_file_type in DEFAULT_INPUT_TYPE

    def handle_pdf(self, lang, output_type, config, correct, enhance, input_file_path, process_folder, output_folder, output_filename):
        """
        传入文件格式为PDF
        :param lang: 识别语言类型
        :param output_type: 输出文件类型
        :param config: 引擎参数
        :param correct: 是否倾斜补正
        :param enhance: 是否图像增强
        :param input_file_path: 传入文件路径
        :param process_folder: 处理中文件存放文件夹
        :param output_folder: 输出文件存放文件夹
        :param output_filename: 输出文件名称
        :return:
        """
        # Read PDF format file
        self.pdf_to_image(input_file_path, process_folder)
        image_dir = os.listdir(process_folder)

        # if correct or enhance:
        #     # image processing
        #     pass

        if len(output_type) == 1:
            extension = output_type[0]

            if extension == FileType.PDF:

                # pool = Pool(processes=4)

                for i in image_dir:
                    if i.split('.')[1] != FileType.JPG: continue

                    image_file_path = os.path.join(process_folder, i)
                    result_file_path = os.path.join(process_folder, str(i.split('.')[0]) + '.pdf')
                    logger.debug('image file path: %s' % image_file_path)
                    logger.debug('result file path: %s' % result_file_path)

                    # pool.apply_async(func=image_to_pdf_or_hocr_wrapper, args=(image_file_path, result_file_path, lang, config))

                    data = ts.image_to_pdf_or_hocr(image_file_path, lang, config)
                    with open(result_file_path, 'wb') as f:
                        f.write(data)

                # pool.close()
                # pool.join()

                self.merge_pdf(process_folder, output_folder, output_filename)

            elif extension == FileType.TXT:
                for i in image_dir:
                    if i.split('.')[1] != FileType.JPG: continue

                    # pool.apply_async(self.image_to_pdf_or_hocr_wrapper, (i, process_folder, lang, config))
                    image_file_path = os.path.join(process_folder, i)
                    result_file_path = os.path.join(process_folder, str(i.split('.')[0]) + '.txt')
                    data = ts.image_to_string(image_file_path, lang, config)
                    with open(result_file_path, 'wb') as f:
                        f.write(data)

                # pool.close()
                # pool.join()

                self.merge_txt(process_folder, output_folder, output_filename)

        else:
            for i in image_dir:
                if i.split('.')[1] != FileType.JPG: continue
                process_filename_base = os.path.join(process_folder, i.split('.')[0])
                image_file_path = os.path.join(process_folder, i)
                run_tesseract(image_file_path, process_filename_base, output_type, lang, config)

            # merge pdf
            self.merge_pdf(process_folder, output_folder, output_filename)

            # merge txt
            self.merge_txt(process_folder, output_folder, output_filename)

    def handle_tiff_or_tif(self, lang, output_type, config, correct, enhance, input_file_path, process_folder, output_folder, output_filename):
        """
        传入文件格式为TIFF/TIF
        :param lang: 识别语言类型
        :param output_type: 输出文件类型
        :param config: 引擎参数
        :param correct: 是否倾斜补正
        :param enhance: 是否图像增强
        :param input_file_path: 传入文件路径
        :param process_folder: 处理中文件存放文件夹
        :param output_folder: 输出文件存放文件夹
        :param output_filename: 输出文件名称
        :return:
        """
        # if enhance or enhance:
        #     is_image = True
        #     # 拆分TIFF/TIF为JPG
        #     self.split_pdf(input_file_path, process_folder)
        #
        #     # image processing
        #     optImageForOCR(srcFolder=process_folder, dstFolder=output_folder, needEnhance=enhance, needRotate=correct)

        if len(output_type) == 1:
            extension = output_type[0]
            result_file_path = os.path.join(output_folder, output_filename + os.extsep + extension)
            logger.debug('output file path: %s', result_file_path)

            # ocr
            if extension == FileType.PDF:
                data = ts.image_to_pdf_or_hocr(input_file_path, lang, config, extension=extension)
                with open(result_file_path, 'wb') as f:
                    f.write(data)

            elif extension == FileType.TXT:
                data = ts.image_to_string(input_file_path, lang, config)
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    f.write(data)

        else:
            # 多输出格式
            output_filename_base = os.path.join(output_folder, output_filename)
            run_tesseract(input_file_path, output_filename_base, output_type, lang, config)

    def handle_jpg_or_png(self, lang, output_type, config, correct, enhance, input_file_path, process_folder, output_folder, output_filename, encrypt_decrypt):
        """
        传入文件格式为JPG/JPEG/PNG
        :param lang: 识别语言类型
        :param output_type: 输出文件类型
        :param config: 引擎参数
        :param correct: 是否倾斜补正
        :param enhance: 是否图像增强
        :param input_file_path: 传入文件路径
        :param process_folder: 处理中文件存放文件夹
        :param output_folder: 输出文件存放文件夹
        :param output_filename: 输出文件名称
        :return:
        """
        current_file_path = input_file_path
        if enhance or enhance:
            # image processing
            current_file_path = process_folder
            optImageForOCR(srcFolder=input_file_path, dstFolder=process_folder, needEnhance=enhance, needRotate=correct)

        if len(output_type) == 1:
            extension = output_type[0]
            result_file_path = os.path.join(output_folder, output_filename + os.extsep + extension)
            logger.debug('output file path: %s', result_file_path)

            # ocr
            if extension == FileType.PDF:
                data = ts.image_to_pdf_or_hocr(current_file_path, lang, config, extension=extension)
                with open(result_file_path, 'wb') as f:
                    f.write(data)

            elif extension == FileType.TXT:
                data = ts.image_to_string(current_file_path, lang, config)
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    f.write(data)

        else:
            # 多输出格式
            output_filename_base = os.path.join(output_folder, output_filename)
            run_tesseract(input_file_path, output_filename_base, output_type, lang, config)

    def dispatch(self):
        self.app.route('/general', method='POST')(self.recognition)
