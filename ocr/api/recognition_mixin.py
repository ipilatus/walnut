
import datetime
import io
import logging
import os
import time
from http import HTTPStatus

import urllib3
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from smb.SMBConnection import SMBConnection
from wand.image import Image

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
            logger.error('request fail. url: %s, code: %d' % (url, resp.status))

    def smb_manger(self, host, host_name, username, password, shared_folder_name, remote_file_path, local_file_path, operation):
        """
        SMB Connection
        :param host: IP
        :param host_name: 域名
        :param username: 用户名
        :param password: 密码
        :param shared_folder_name: 共享文件夹名称
        :param remote_file_path: 存放路径是相对共享文件夹的路径
        :param local_file_path: 本地文件路径
        :param operation:  download:下载文件； upload:上传文件
        :return:
        """
        try:
            conn = SMBConnection(username, password, '', host_name, use_ntlm_v2=True)
            assert conn.connect(host)

            if operation == 'download':
                # download file
                with open(local_file_path, 'wb') as f:
                    conn.retrieveFile(shared_folder_name, remote_file_path, f)

            elif operation == 'upload':
                # upload file
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
            logger.error('pdf to jpg error!', e)
            # TODO(): pdf to image error

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
            logger.error('merge pdf error!', e)
            # TODO(): merge pdf file error

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
            logger.debug('merge txt error. %s', str(e))

    def tiff_to_image(self, input_file_path, process_folder):
        """
        将 TIFF 拆分为 JPG
        :param input_file_path:
        :param process_folder:
        :return:
        """
        pass

    def merge_tiff(self, input_file_path, process_folder):
        """
        将 JPG 合并为 TIFF
        :param input_file_path:
        :param process_folder:
        :return:
        """
        pass

    def make_folder(self, filename):
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
            logger.error('create folder error', e)
            # TODO(): create folder error
            raise e