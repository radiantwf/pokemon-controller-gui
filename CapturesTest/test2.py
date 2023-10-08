import cv2
import numpy as np

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

# 测试代码
result = get_main_colors('CapturesTest/test.png', k=5)
for color, count in result:
    print('color:', color, 'count:', count)
