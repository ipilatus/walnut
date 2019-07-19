import base64

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# padding算法
BS = AES.block_size  # aes数据分组长度为128 bit
# pad = lambda s: s + ((BS - len(s) % BS) * ' ').encode()

mode = AES.MODE_CBC
key = '751f621ea5c8f930751f621e'
iv = '2624750004598718'.encode()


def encrypt():
    """加密"""
    with open(r'F:\tmp\first.pdf', 'rb') as f:
        text = f.read()

    a = 16 - len(text) % 16
    data = pad(text, AES.block_size, style='pkcs7')

    cryptor = AES.new(key.encode('utf-8'), mode, iv)
    ciphertext = cryptor.encrypt(data)

    # res = base64.b64encode(ciphertext)

    with open(r'F:\tmp\first_encrypt_7.pdf', 'wb') as f:
        f.write(ciphertext)


def decrypt():
    """解密"""
    with open(r'F:\tmp\first_encrypt_7.pdf', 'rb') as f:
        data = f.read()

    # data = base64.decodebytes(data)
    cryptor = AES.new(key.encode('utf-8'), mode, iv)
    text = cryptor.decrypt(data)

    # res = text.rstrip(chr(0))

    with open(r'F:\tmp\first_decrypt.pdf', 'wb') as f:
        f.write(text)


if __name__ == '__main__':
    encrypt()
    decrypt()