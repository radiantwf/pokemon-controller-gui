import cv2
import numpy as np

# 读取视频帧
cap = cv2.VideoCapture('./yolo_training/data/2023-10-29 01-28-46.mp4')
# bgsegm = cv2.bgsegm.createBackgroundSubtractorMOG()
bgsegm = cv2.createBackgroundSubtractorMOG2(history=1, detectShadows=False)
# bgsegm = cv2.bgsegm.createBackgroundSubtractorGMG()

while True:
    ret, frame = cap.read()
    if ret == False:
        exit(1)
    fgmask = bgsegm.apply(frame)
    cv2.imshow('v', fgmask)
    k = cv2.waitKey(10) & 0xff
    if k == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
