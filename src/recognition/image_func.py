import cv2
import numpy as np


def find_matches(gray, template_gray, threshold=0.95, min_distance=10):
    # 在目标图片中查找匹配
    result = cv2.matchTemplate(gray, template_gray, cv2.TM_CCOEFF_NORMED)

    # 查找所有匹配的位置
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))

    # 去除距离太近的匹配
    filtered_locations = []
    for loc in locations:
        too_close = False
        for other_loc in filtered_locations:
            distance = np.sqrt((loc[0] - other_loc[0])
                               ** 2 + (loc[1] - other_loc[1])**2)
            if distance < min_distance:
                too_close = True
                if result[loc[::-1]] > result[other_loc[::-1]]:
                    filtered_locations.remove(other_loc)
                    filtered_locations.append(loc)
                break
        if not too_close:
            filtered_locations.append(loc)

    # 返回所有匹配的位置
    return filtered_locations
