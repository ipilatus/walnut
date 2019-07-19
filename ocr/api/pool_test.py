from smb.SMBConnection import SMBConnection
import tempfile
from nmb.NetBIOS import NetBIOS
import sys

import  urllib.request
from smb.SMBHandler import SMBHandler

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
import base64


def getBIOSName(timeout=30):
    try:
        bios = NetBIOS()
        srv_name = bios.queryIPForName('172.25.73.100', timeout=timeout)
    except:
        print("Looking up timeout, check remote_smb_ip again!!", sys.stderr)
    finally:
        bios.close()
        return srv_name


def smb_manger():
    try:
        conn = SMBConnection('wuqian', 'woshi123', 'RITS066100', 'RITS066300', use_ntlm_v2=True)
        res = conn.connect('172.25.73.100', 139)

        # with open('F:\\tmp\\0000.txt', 'rb') as f:
        #     conn.storeFile('Users', '\\test1\\hello.txt', f)

        with open('F:\\tmp\\0001.txt', 'wb') as f:
            conn.retrieveFile('Users', '\\test1\\hello.txt', f)

    except Exception as e:
        print('SMB file upload error. %s' % str(e))


def req():
    director = urllib.request.build_opener(SMBHandler)
    fh = director.open('smb://wuqian:woshi123@172.25.73.100/Users/test1/hello.txt')
    print(fh.read())
    fh.close()


""" AES """


# padding算法
BS = AES.block_size  # aes数据分组长度为128 bit
pad = lambda s: s + (BS - len(s) % BS) * chr(0)


def encrypt():
    """
    AES 加密
    :return:
    """
    txt = b'hello word'
    data = pad(txt)
    key = get_random_bytes(16)
    iv = Random.new().read(AES.block_size)
    print(key)
    print(iv)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext, tag = cipher.encrypt(data)

    with open(r'F:\tmp\encrypted.txt', 'wb') as file_out:
        [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]

    return key


def decrypt(key):
    """
    AES 解密
    :param key:
    :param mode:
    :return:
    """
    with open(r'F:\tmp\encrypted.txt', 'rb') as file_in:
        nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]

        for x in (16, 16, -1):
            file_in.read(x)

    # let's assume that the key is somehow available again
    cipher = AES.new(key, AES.MODE_CBC)
    data = cipher.decrypt(ciphertext, tag)
    print(data)


# def encrypt(plaintext, key, mode):
#     # 生成随机初始向量IV
#     iv = Random.new().read(AES.block_size)
#
#     cryptor = AES.new(key.encode('utf-8'), mode, iv)
#     ciphertext = cryptor.encrypt(pad(plaintext))
#
#     with open(r'F:\tmp\encrypted.txt', 'wb') as f:
#         f.write(ciphertext)
#
#     return base64.b64encode(iv + ciphertext)
#
#
# def decrypt(ciphertext, key, mode):
#     ciphertext = base64.decodebytes(ciphertext)
#     iv = ciphertext[0:AES.block_size]
#     ciphertext = ciphertext[AES.block_size:len(ciphertext)]
#
#     cryptor = AES.new(key, mode, iv)
#     plaintext = cryptor.decrypt(ciphertext)
#
#     return plaintext.rstrip(chr(0))


def aes_encrypt(key, data):
    iv = '0102030405060708'
    # pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
    data = pad(data)
    # 字符串补位
    cipher = AES.new(key.encode('utf8'), AES.MODE_CBC, iv.encode('utf8'))
    encryptedbytes = cipher.encrypt(data.encode('utf8'))  # 加密后得到的是bytes类型的数据
    encodestrs = base64.b64encode(encryptedbytes)  # 使用Base64进行编码,返回byte字符串

    enctext = encodestrs.decode('utf8')  # 对byte字符串按utf-8进行解码

    with open(r'F:\tmp\encrypted.txt', 'w') as f:
        f.write(enctext)

    return enctext


def aes_decrypt(key, data):
    vi = '0102030405060708'
    data = data.encode('utf8')
    encodebytes = base64.decodebytes(data)

    cipher = AES.new(key.encode('utf8'), AES.MODE_CBC, vi.encode('utf8'))   # 将加密数据转换位bytes类型数据
    text_decrypted = cipher.decrypt(encodebytes)
    unpad = lambda s: s[0:-s[-1]]
    text_decrypted = unpad(text_decrypted)
    # 去补位
    text_decrypted = text_decrypted.decode('utf8')
    return text_decrypted


if __name__ == '__main__':
    # smb_manger()
    # getBIOSName()
    # req()

    key = encrypt()
    decrypt(key)

    # key = '1234567890123456'
    # data = 'hello word'
    # mode = AES.MODE_CBC
    # encrypt(data, key, mode)
    # decrypt(data, key, mode)

    # aes_encrypt(key, data)
    # with open(r'F:\tmp\encrypted.txt', 'r') as f:
    #     data1 = f.read()
    # aes_decrypt(key, data1)