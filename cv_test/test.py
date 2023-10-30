import cv2
import numpy as np

# 读取图像
img = cv2.imread('cv_test/0984-Great Tusk-0001.jpg')

# 将图像转换为灰度图像
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 自适应阈值二值化
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, -30)

# 定义结构元素
kernel = np.ones((5,5),np.uint8)

# 进行开运算
opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

# 进行闭运算
closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

# 显示结果
cv2.imshow('Original Image', img)
cv2.imshow('Thresholded Image', thresh)
cv2.imshow('Opening', opening)
cv2.imshow('Closing', closing)
cv2.waitKey(0)
cv2.destroyAllWindows()