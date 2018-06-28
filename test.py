from code_model.predict import *
import time

from detect import detect

from cfgs.config import cfg

predict_func = initialize(cfg.model_path)

import cv2

img = cv2.imread('resize_img.jpg')

for idx in range(200):
    if idx % 10 == 0:
        print(time.time())
    peaks, img = detect(img, predict_func, scale=1, draw_result=False)

cv2.imwrite('result_1.jpg', img)
