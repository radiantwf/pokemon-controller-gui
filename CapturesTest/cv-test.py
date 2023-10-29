import cv2

# 初始化视频捕获
cap = cv2.VideoCapture(0)

# 初始化背景和前景模型import cv2

# Initialize video capture
cap = cv2.VideoCapture(0)

# Initialize previous frame
prev_frame = None

# Loop through video frames
while True:
    # Read frame
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    # Initialize previous frame if necessary
    if prev_frame is None:
        prev_frame = gray
        continue
    
    # Compute absolute difference between current and previous frame
    frame_diff = cv2.absdiff(prev_frame, gray)
    
    # Apply thresholding to highlight motion regions
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    
    # Apply morphological operations to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Find contours in thresholded image
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw bounding boxes around contours
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # Update previous frame
    prev_frame = gray
    
    # Display result
    cv2.imshow('Result', frame)
    if cv2.waitKey(1) == ord('q'):
        break

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()
bg_model = cv2.createBackgroundSubtractorMOG2()
fg_model = cv2.createBackgroundSubtractorMOG2()

# 循环遍历视频帧
while True:
    # 读取帧
    ret, frame = cap.read()
    if not ret:
        break
    
    # 应用背景减除
    fg_mask = fg_model.apply(frame)
    bg_mask = bg_model.apply(frame)
    
    # 对前景掩模应用阈值处理
    thresh = cv2.threshold(fg_mask, 128, 255, cv2.THRESH_BINARY)[1]
    
    # 应用形态学操作以去除噪声
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # 在阈值图像中查找轮廓
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 在轮廓周围绘制边界框
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # 显示结果
    cv2.imshow('Result', frame)
    if cv2.waitKey(1) == ord('q'):
        break

# 释放视频捕获并关闭窗口
cap.release()
cv2.destroyAllWindows()