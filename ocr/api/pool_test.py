from smb.SMBConnection import SMBConnection
import tempfile
from nmb.NetBIOS import NetBIOS
import sys

import  urllib.request
from smb.SMBHandler import SMBHandler


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


if __name__ == '__main__':
    smb_manger()
    # getBIOSName()
    # req()