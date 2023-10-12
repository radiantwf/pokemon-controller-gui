import cv2
import numpy as np
import tkinter as tk

def get_main_colors(image_path, k=5):
    # Load the image
    image = cv2.imread(image_path)

    # 将图片转换为一维数组
    img_data = image.reshape((-1, 3))

    # 将数据类型转换为 CV_32F
    img_data = np.float32(img_data)

    # 使用 k-means 聚类算法，将像素点分为 k 类
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_RANDOM_CENTERS
    _, labels, centers = cv2.kmeans(img_data, k, None, criteria, 10, flags)

    # 获取聚类中心，即每个类别的主颜色
    colors = centers.astype(int)

    # 统计每个聚类的像素点个数
    counts = np.bincount(labels.reshape(-1))

    # 将主颜色和像素点个数组合成一个列表
    result = list(zip(colors.tolist(), counts.tolist()))

    return result

def show_colors(result):
    # 创建一个新窗口
    window = tk.Tk()

    # 创建一个标签，用于显示每个颜色和计数
    for color, count in result:
        color_hex = '#{:02x}{:02x}{:02x}'.format(*color)
        label = tk.Label(window, text='Count: {}  Color: {}'.format(count, color_hex), bg=color_hex, fg='white')
        label.pack()

    # 运行窗口
    window.mainloop()

# 测试代码
# result = get_main_colors('CapturesTest/background-14.jpg', k=5)
result = get_main_colors('CapturesTest/20231006134925-recognize.jpg', k=1)
show_colors(result)
