from subprocess import call
import sys


def ocr():
    print('begin')
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    lang = sys.argv[3]

    cmd = 'tesseract {0} {1} --oem 1 -l {2}'.format(input_file, output_file, lang)
    print(cmd)

    res = call(cmd, shell=True)

    res = 'success' if res == 0 else 'fail'
    print('finished. %s' % (res))


if __name__ == '__main__':
    ocr()