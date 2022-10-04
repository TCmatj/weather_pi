import aspose.words as aw
import os
import cv2
import numpy as np 

doc = aw.Document()
builder = aw.DocumentBuilder(doc)

path = 'D:\QQdata\\2216685752\FileRecv\MobileFile'
pathl = path + '\Image'
pathp = path + '\\bmp'
filelist = os.listdir(pathl)
i = 1
for file in filelist:
    image = cv2.imread(os.path.join(pathl, file))
    length = image.shape[0]
    weight = image.shape[1]
    if length>weight:
        scale = 200/weight
    else:
        scale = 200/length
    image = cv2.resize(image, None, fx= scale, fy= scale, interpolation= cv2.INTER_LINEAR)
    img_encode = cv2.imencode('.bmp',image)[1]
    with open(pathp + '\\' + str(i) + '.bmp', 'wb') as f: #写入
        f.write(img_encode)

    i = i + 1