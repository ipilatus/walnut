import base64
import datetime
import io
import logging
import os
import time
from http import HTTPStatus

import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from nmb.NetBIOS import NetBIOS
from smb.SMBConnection import SMBConnection
from wand.image import Image

from ocr.api.exceptions import BackendStatusCodeError
from ocr.api.exceptions import SMBConnectionError, PDFToJPGError, MergePDFError, TIFFToJPGError, MergeTIFFError, \
    MergeTxtError, MakeDirError
from ocr.api.type import FileType
from ocr.config import base_folder, input_folder_name, process_folder_name, output_folder_name

logger = logging.getLogger(__name__)
http = urllib3.PoolManager()


class RecognitionMixin:

    def ocr_finished(self, url):
        resp = http.request('GET', url, fields={'timestamp': time.time()})

        if resp.status == HTTPStatus.OK:
            logger.debug('request success. url: %s' % url)
        else:
            raise BackendStatusCodeError(except_code=HTTPStatus.OK, actual_code=resp.status)

    def aes_decrypt(self, input_file_path, key, iv, mode, encoded):
        """
        AES 解密
        :param input_file_path:
        :param key:
        :param iv:
        :param mode:
        :param encoded:
        :return:
        """
        with open(input_file_path, 'rb') as f:
            text = f.read()

        data = base64.decodebytes(text) if encoded == 'base64' else text

        cryptor = AES.new(key.encode('utf-8'), mode, iv.encode('utf-8'))
        res = cryptor.decrypt(data)

        with open(input_file_path, 'wb') as f:
            f.write(res)

    def aes_encrypt(self, text, result_file_path, key, iv, mode, encoded, style='pkcs7'):
        """
        AES 加密
        :param text:
        :param result_file_path:
        :param key:
        :param iv:
        :param mode:
        :param encoded:
        :param style:
        :return:
        """
        data = pad(text, AES.block_size, style)

        cryptor = AES.new(key.encode('utf-8'), mode, iv)
        cipher_text = cryptor.encrypt(data)

        res = base64.b64encode(cipher_text) if encoded == 'base64' else cipher_text

        with open(result_file_path, 'wb') as f:
            f.write(res)

    def get_BIOSName(self, host, timeout=30):
        try:
            bios = NetBIOS()
            srv_name = bios.queryIPForName(host, timeout=timeout)

        except Exception as e:
            logger.error("Looking up timeout, check remote_smb_ip again. %s" % str(e))

        finally:
            bios.close()
            return srv_name

    def download_file_by_smb(self, host, host_name, username, password, domain, shared_folder_name, remote_file_path, local_file_path):
        """
        download file by SMB
        :param host: IP
        :param host_name: 域名
        :param username: 用户名
        :param password: 密码
        :param domain: 域名
        :param shared_folder_name: 共享文件夹名称
        :param remote_file_path: 存放路径是相对共享文件夹的路径
        :param local_file_path: 本地文件路径
        :return:
        """
        try:
            remote_name = host_name or self.get_BIOSName(host)
            domain = domain or ''
            conn = SMBConnection(username, password, '', remote_name, domain, use_ntlm_v2=True)
            assert conn.connect(host)

            with open(local_file_path, 'wb') as f:
                conn.retrieveFile(shared_folder_name, remote_file_path, f)

        except Exception as e:
            raise SMBConnectionError(data=str(e))

        finally:
            conn.close()

    def upload_file_by_smb(self, host, host_name, username, password, shared_folder_name, remote_file_path, local_file_path):
        """ upload file by SMB """
        try:
            remote_name = host_name or self.get_BIOSName(host)
            conn = SMBConnection(username, password, '', remote_name, use_ntlm_v2=True)
            assert conn.connect(host)

            with open(local_file_path, 'rb') as f:
                conn.storeFile(shared_folder_name, remote_file_path, f)

        except Exception as e:
            logger.error('SMB file download error. %s' % str(e))

        finally:
            conn.close()

    def pdf_to_image(self, input_file_path, process_folder):
        """
        将 PDF 拆分为JPF
        :param input_file_path: 传入文件路径
        :param process_folder: 图片存储文件夹
        :return:
        """
        try:
            # Read PDF format file
            reader = PdfFileReader(stream=open(input_file_path, 'rb'), strict=False)

            for i in range(reader.numPages):
                page = reader.getPage(i)
                x1, y1, x2, y2 = page.mediaBox

                pdf_writer = PdfFileWriter()
                pdf_writer.addPage(page)

                pdf_bytes = io.BytesIO()
                pdf_writer.write(pdf_bytes)
                pdf_bytes.seek(0)

                # Save as JPG format
                image_file_path = os.path.join(process_folder, '%04d.jpg' % i)
                with Image(file=pdf_bytes, resolution=300) as f:
                    f.save(filename=image_file_path)

        except Exception as e:
            raise PDFToJPGError(data=str(e))

    def merge_pdf(self, process_folder, output_folder, output_filename):
        """
        将 JPG 合并为 PDF
        :param process_folder: 图片所在文件夹
        :param output_folder: 输出结果存储文件夹
        :param output_filename: 输出文件名称
        :return:
        """
        try:
            pdf_merger = PdfFileMerger()
            process_folder_dir = os.listdir(process_folder)
            for i in process_folder_dir:
                if i.split('.')[1] != FileType.PDF: continue
                pdf_file_path = os.path.join(process_folder, i)
                pdf_merger.append(open(pdf_file_path, 'rb'))

            filename = output_filename + os.extsep + FileType.PDF
            result_file_path = os.path.join(output_folder, filename)
            logger.debug('output file path: %s', result_file_path)

            with open(result_file_path, 'wb') as f1:
                pdf_merger.write(f1)

        except Exception as e:
            raise MergePDFError(data=str(e))

    def merge_txt(self, process_folder, output_folder, output_filename):
        """
        合并 TXT 文件
        :param process_folder: TXT 所在文件夹
        :param output_folder: 输出结果存储文件夹
        :param output_filename: 输出文件名称
        :return:
        """
        try:
            process_folder_dir = os.listdir(process_folder)
            filename = output_filename + os.extsep + FileType.TXT
            result_file_path = os.path.join(output_folder, filename)
            logger.debug('output file path: %s', result_file_path)

            with open(result_file_path, 'w', encoding='utf-8') as f:
                for i in process_folder_dir:
                    if i.split('.')[1] != FileType.TXT: continue
                    txt_file_path = os.path.join(process_folder, i)

                    with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
                        f.write(txt_file.read())
                        f.write('\n')

        except Exception as e:
            raise MergeTxtError(data=str(e))

    def tiff_to_image(self, input_file_path, process_folder):
        """
        将 TIFF 拆分为 JPG
        :param input_file_path:
        :param process_folder:
        :return:
        """
        try:
            pass

        except Exception as e:
            raise TIFFToJPGError(data=str(e))

    def merge_tiff(self, input_file_path, process_folder):
        """
        将 JPG 合并为 TIFF
        :param input_file_path:
        :param process_folder:
        :return:
        """
        try:
            pass

        except Exception as e:
            raise MergeTIFFError(data=str(e))

    def make_dir(self, filename=None):
        try:
            date = datetime.datetime.now().strftime('%Y%m%d')
            now_timestamp = str(round(time.time() * 1000))
            logger.debug('current date: %s, timestamp: %s' % (date, now_timestamp))

            folder_name = now_timestamp + '_' + filename if filename else now_timestamp

            input_folder = os.path.join(base_folder, date, folder_name, input_folder_name)
            process_folder = os.path.join(base_folder, date, folder_name, process_folder_name)
            output_folder = os.path.join(base_folder, date, folder_name, output_folder_name)
            logger.debug('input folder path: %s' % str(input_folder))
            logger.debug('process folder path: %s' % str(process_folder))
            logger.debug('output folder path: %s' % str(output_folder))

            if not os.path.exists(input_folder):
                os.makedirs(input_folder)

            if not os.path.exists(process_folder):
                os.makedirs(process_folder)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            return input_folder, process_folder, output_folder, now_timestamp

        except Exception as e:
            raise MakeDirError(data=str(e))