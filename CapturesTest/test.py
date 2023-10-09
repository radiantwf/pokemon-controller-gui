import sys
import cv2
import numpy as np
import colorsys
sys.path.append('./src')
from recognition.scripts.sv.common.image_match.box_match import BoxMatch


def find_matches(template_gray, gray, threshold=0.95, min_distance=10):
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


def get_main_color(image, region=None):
    if region is not None:
        x, y, w, h = region
        img = image[y:y + h, x:x + w]
    else:
        img = image

    # 计算直方图
    hist = cv2.calcHist([img], [0, 1, 2], None, [
                        8, 8, 8], [0, 256, 0, 256, 0, 256])

    # 找到直方图中出现次数最多的颜色
    hsv = np.unravel_index(np.argmax(hist), hist.shape)

    hsv = colorsys.rgb_to_hsv(*[c for c in hsv])
    main_color = hsv[0] * 360
    return main_color


def main():
    egg_template = cv2.imread(
        "resources/img/recognition/pokemon/sv/eggs/box/box-space-selected.png")
    template_gray = cv2.cvtColor(
        egg_template, cv2.COLOR_BGR2GRAY)

    mat = cv2.imread(
        "CapturesTest/1.jpg")
    box = BoxMatch().match(mat)
    print(box)
    gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)

    main_color = get_main_color(mat, (226, 290, 6, 6))
    print(main_color)
    
    # 查找所有匹配的位置
    locations = find_matches(template_gray, gray,0.6)

    # 在目标图片中标记所有匹配的位置
    for loc in locations:
        cv2.rectangle(mat, loc, (loc[0] + egg_template.shape[1],
                      loc[1] + egg_template.shape[0]), (0, 0, 255), 2)
        print(loc)

    # 显示结果
    cv2.imshow("Matches", mat)
    cv2.waitKey(0)


if __name__ == "__main__":
    main()
