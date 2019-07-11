## openCV-Python(4.1.0) Docs: https://docs.opencv.org/4.1.0/
## Pillow (Python Image Library) Docs: https://pillow.readthedocs.io/en/stable/index.html
## -*- coding: utf-8 -*-
## v1.0.0 @2019-05-16

import os, math, cv2
import numpy as np
from PIL import Image, ImageEnhance


def __pil2cv(pil_im):
    '''
    将PIL的Image对象转为适用于OpenCV的numpy.ndarray, 
    并且由于两者的对于RGB，RGBA图像的存放格式不同，需要翻转R,B通道, 
    详见 https://docs.opencv.org/4.1.0/ 中对cvtColor()的说明
    '''
    mode = pil_im.mode
    if('RGB' == mode):
        return cv2.cvtColor(np.asarray(pil_im), cv2.COLOR_RGB2BGR)
    elif('RGBA' == mode):
        return cv2.cvtColor(np.asarray(pil_im), cv2.COLOR_RGBA2BGRA)
    elif('1' == mode):
        array = np.asarray(pil_im, dtype=np.uint8)
        if (np.max(array) == 1):
            return array * 255
        return array
    else:
        return np.asarray(pil_im)


def __cv2pil(cv_img):
    """
    将OpenCV的numpy.ndarray转为适用于PIL的Image对象
    """
    if len(cv_img.shape) < 3: return Image.fromarray(cv_img)   # 灰度图像

    channel = cv_img.shape[2]
    if(channel == 3):           # 三通道图像
        return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    elif(channel == 4):         # 三通道+alpha通道图像
        return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA))
    else:
        return Image.fromarray(cv_img)


def __pilResize2Dpi(pil_im, dpi=300):
    """
    缩小图片至指定dpi，返回缩小后的图和缩小倍率
    """
    w1, h1 = pil_im.size                        # 原图宽高
    srcDpi = pil_im.info.get('dpi')[0]          # 原图分辨率
    X = dpi/srcDpi                              # 缩小倍率

    # 如果原图已经小于期望尺寸，则直接返回
    if(X >= 1): return pil_im, 1.0

    # 使用Image.ANTIALIAS参数的话质量较高，但速度稍慢
    return pil_im.resize((int(w1 * X), int(h1 * X)), resample=Image.ANTIALIAS), X


def __cv2GaryScale(src):
    """
    转为灰度图像
    """
    img = src
    if len(img.shape) < 3: return img   # 灰度图像
    channel = img.shape[2]
    if(channel == 3):       # 三通道图像
        return cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)
    elif(channel == 4):     # 三通道+alpha通道图像
        return cv2.cvtColor(src=img, code=cv2.COLOR_BGRA2GRAY)
    else:                   
        return img


def __cv2Resize(src, size=1024):
    """
    缩小图片, 返回缩小后的图和缩小倍率
    """
    img = src
    h, w = img.shape[:2]
    X = size/max(h, w)  # 缩小倍率
    if(X >= 1): return img, 1.0 # 如果原图已经小于期望尺寸，则直接返回
    return cv2.resize(src=img, dsize=(int(w*X), int(h*X)), interpolation=cv2.INTER_LINEAR), X


def __cv2EnhanceImg(src):
    """
    图像增强
    """
    # img = src
    if(len(src.shape) > 2):
        img = cv2.split(src)
        for i in range(src.shape[2]):
            img[i] = cv2.equalizeHist(img[i])
        return cv2.merge(img)
    else:
        img = src
        return cv2.equalizeHist(img)

    # return cv2.Laplacian(src=img, ddepth=-1, ksize=5)


def __cv2eraseEdge(src, size=5, color=255):
    """
    消除边缘, 将图像外缘填充为白色
    """
    img = src
    h, w = img.shape[:2]

    color = color if len(img.shape) == 2 else (color, color, color)
    if size <= 0: size = 1

    img[:size] = color       # 去边，上
    img[h-size:] = color     # 去边，下
    img[:, :size] = color    # 去边，左
    img[:, w-size:] = color    # 去边，右
    return img


def __calcRotateAngle(houghlines, threshold=90):
    """
    计算旋转角度
    threshold为正负倾角的最大范围，取值范围0~90，threshold=10 表示只处理-10°~10°之间的倾角(不包含-10°和10°)
    """
    if (houghlines is None): return 0.0     # 如没有找到直线，直接返回0°（不旋转）
    if (threshold > 90): threshold = 90     # 阈值取值范围 0 ~ 90
    if (threshold < 0): threshold = 0

    # angles列表记录直线参数，方便之后计算平均值和去除干扰项
    # angles[0]: 固定为180个元素，负角度(-1°~-89°)记录在0~89，正角度(1°~89°)记录在90~179
    # angles[0][]中: [0]为此角度线条的数量，[1]为精确的角度的集合
    # angles = [[0,[]] for _ in range(180)]
    # offset = 90
    angles = [[0,[]] for _ in range(threshold*2)]
    offset = threshold
    for line in houghlines:
        x0, y0 = line[0][0], line[0][1]
        x1, y1 = line[0][2], line[0][3]
        if ((x1-x0)==0): continue  # 两点的x坐标差为0，说明为垂直线，无法计算反正切，跳过

        tan = (y1-y0)/(x1-x0)
        angle = math.degrees(math.atan(tan))  # 反正切角度
        
        if abs(angle) >= threshold: continue   # 过滤掉大于阈值的角度

        # 将角度加入angles列表中
        # 取角度值的整数绝对值作为索引
        if(angle < 0):
            index = abs(int(angle))
        else:
            index = abs(int(angle)) + offset
        angles[index][0] += 1           # 每插入一条记录，数量+1
        angles[index][1].append(angle)
    
    # 将angles列表按各个角度线条的数量排序
    def elemCount(elem): return elem[0]
    angles.sort(key=elemCount, reverse=True)

    # 取线条数量最多的角度的平均值作为旋转角度
    angle_count, values = angles[0]
    if(angle_count>0):
        mean_angle = np.mean(values)
    else:
        mean_angle = 0.0

    # print('total lines:', len(houghlines))
    # print('1st:', angle_count, 'valus:', angles[0][1])
    # if(angle_count < len(houghlines)):
    #     print('2nd:', angles[1][0], 'valus:', angles[1][1])
    # if(angle_count + angles[1][0] < len(houghlines)):
    #     print('3rd:', angles[2][0], 'valus:', angles[2][1])
    # print('rotate_angle = ', mean_angle)

    return mean_angle


def __cvPerTreat(src, dpi, needEnhance=True):
    """
    图像预处理，返回处理后的图像和缩小倍率
    """
    img = src
    ## 1.缩图
    img, X = __cv2Resize(src=img, size=1024)
    t_dpi = int(dpi*X)

    ## 2.转灰度
    img = __cv2GaryScale(src=img)

    ## 3.消除边缘
    img = __cv2eraseEdge(src=img, size=int(t_dpi/5), color=255)    # 消除图像外缘1/5英寸范围内的黑边

    ## 4.图像增强
    if needEnhance:
        img = __cv2EnhanceImg(src=img)
        # img = __cv2EnhanceGrayImg(src=img, contrast=2.0, brightness=1.5)
    return img, X


def __cvFindLines_doc(cv_img, dpi):
    """
    使用Hough直线算法寻找直线
    * cv_img：  灰度图, OpenCV格式格式图像(ndarray)
    * dpi：     相当于一英寸的像素值，作为阈值的算子使用
    * 返回：    图中找到的所有线条(cv2.HoughLinesP()的返回值)
    """
    ## 模糊滤波, 用双边滤波可以尽量保留表格线条
    img = cv2.bilateralFilter(src=cv_img, d=0, sigmaColor=dpi*2, sigmaSpace=dpi/10)

    ## 灰度图像较适合自适应阈值二值化，OTSU二值化适合双峰图像
    size = int(dpi/2) if int(dpi/2)%2 == 1 else int(dpi/2)+1
    img = cv2.adaptiveThreshold(src=img, maxValue=255, adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C, thresholdType=cv2.THRESH_BINARY, blockSize=size, C=dpi/10)

    ## 查找边缘
    img = cv2.Canny(image=img, threshold1=dpi, threshold2=dpi*2)

    ## 用霍夫变换搜索直线
    lines = cv2.HoughLinesP(image=img, rho=1, theta=np.pi/180, threshold=dpi, minLineLength=dpi*2, maxLineGap=dpi)

    # # 调试用图像
    # if lines is not None:
    #     line_img = np.zeros(img.shape, np.uint8)
    #     for line in lines:
    #         x0, y0 = line[0][0], line[0][1]
    #         x1, y1 = line[0][2], line[0][3]
    #         cv2.line(line_img, (x0,y0), (x1,y1), 127, 1)
    #     cv2.imshow('', line_img)
    #     cv2.waitKey()
    return lines


def __cvRotateImg(cv_img, angle, trim=True):
    """
    使用OpenCV的warpAffine旋转图片(性能好)
    """
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = cv_img.shape[:2]
    cX, cY = (w/2, h/2)

    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    # 计算旋转矩阵
    rotate_matrix = cv2.getRotationMatrix2D(center=(cX, cY), angle=angle, scale=1.0)
    cos = np.abs(rotate_matrix[0,0])
    sin = np.abs(rotate_matrix[0,1])

    # compute the new bounding dimensions of the image
    nW = int((h*sin) + (w*cos))
    nH = int((h*cos) + (w*sin))

    # adjust the rotation matrix to take into account translation
    rotate_matrix[0,2] += (nW/2) - cX
    rotate_matrix[1,2] += (nH/2) - cY
    
    # 旋转图片, 根据图像通道数确定填充的值
    if(len(cv_img.shape) == 3 and cv_img.shape[2] == 3):
        border = (255,255,255)
    else:
        border = 255
    img = cv2.warpAffine(src=cv_img, M=rotate_matrix, dsize=(nW, nH), flags=cv2.INTER_LINEAR, borderValue=border)

    # 根据参数确定是否将其裁剪到与原图一致的尺寸
    if(trim == True):
        if(abs(angle) < 45):
            x = int((nH - h)/2)
            y = int((nW - w)/2)
            return img[x:x+h, y:y+w]
        else:
            x = int((nH - w)/2)
            y = int((nW - h)/2)
            return img[y:y+w, x:x+h]
    else:
        return img


def optImageForOCR(srcFolder, dstFolder, needTrim=True, needEnhance=False, needRotate=False, trim2Dpi=300, enhanceLevel=3.0, rotateThreshold=10):
    """
    ocr引擎图像优化，可处理jpg，单页tif，png文件
    * srcFolder:    源文件夹路径
    * dstFolder:    结果文件夹路径
    * needTrim:     是否缩小图像，默认True
    * needEnhance:  是否进行图像增强，默认False
    * needRotate:   是否进行偏斜矫正，默认False
    * trim2Dpi:     将图像缩小至此dpi，默认300，取值范围100-600整数，步进100
    * enhanceLevel: 图像强化等级，默认3.0，取值范围2.0-10.0
    * rotateThreshold: 最大纠偏角度，默认10，取值范围1-90整数，步进1
    """
    if os.path.isdir(srcFolder) == False: raise Exception('Wrong source folder')
    if os.path.isdir(dstFolder) == False: raise Exception('Wrong destination folder')

    list_ = os.listdir(srcFolder) #列出文件夹下所有的目录与文件
    for i in range(len(list_)):

        fileAbsPath = os.path.join(srcFolder, list_[i])
        if os.path.isfile(fileAbsPath):

            fileSortName, fileSuffix = os.path.splitext(list_[i])
            if fileSuffix.lower() not in ['.jpg','.jpeg','.tif','.tiff','.png']: continue   # 过滤掉不支持的图片格式

            im = Image.open(fileAbsPath)
            if im.mode == '1': im = im.convert('L')
            dpi = im.info.get('dpi', (300, 300))[0]     # 获取图像dpi信息
            if dpi == 0: raise Exception('Wrong source dpi')

            if needTrim and (dpi > trim2Dpi):
                im, _ = __pilResize2Dpi(im, trim2Dpi)
                dpi = trim2Dpi

            if needEnhance and (im.mode not in ['1',]):
                im = ImageEnhance.Contrast(im).enhance(enhanceLevel)

            if needRotate:
                ## 转cv格式
                src_img = __pil2cv(im)

                ## 1. 预处理
                img, X = __cvPerTreat(src=src_img, dpi=dpi, needEnhance=(not needEnhance))

                ## 2. 寻找直线
                lines = __cvFindLines_doc(cv_img=img, dpi=int(dpi*X))     # 传入相当于一英寸(2.5厘米)的像素值作为算子

                ## 3. 根据最佳旋转角度计算旋转矩阵, 旋转原图, 并裁剪到与原图尺寸一致
                rotate_angle = __calcRotateAngle(houghlines=lines, threshold=rotateThreshold)
                if(rotate_angle != 0.0):
                    img = __cvRotateImg(cv_img=src_img, angle=rotate_angle, trim=True)

                    ## 转pil格式
                    im = __cv2pil(img)

            im.save(os.path.join(dstFolder, fileSortName + ".jpg"), quality=95, dpi=(dpi, dpi))
            print(os.path.join(dstFolder, fileSortName + ".jpg"), ' --- saved.')


if __name__ == "__main__":
    ROOT_DIR = "D:\\My Documents\\workspace_python\\openCV"
    srcPath = ROOT_DIR + "\\original\\New folder - Copy"
    resultPath = srcPath + "\\result"
    
    optImageForOCR(srcPath, resultPath, True, True, True)