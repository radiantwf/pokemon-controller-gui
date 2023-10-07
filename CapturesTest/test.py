import cv2
import numpy as np




def find_matches(template_gray, gray, threshold=0.3, min_distance=10):
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
                break
        if not too_close:
            filtered_locations.append(loc)

    # 返回所有匹配的位置
    return filtered_locations


def main():
    egg_template = cv2.imread(
        "resources/img/recognition/pokemon/sv/eggs/box/box-arrow.png")
    template_gray = cv2.cvtColor(
        egg_template, cv2.COLOR_BGR2GRAY)

    mat = cv2.imread(
        "CapturesTest/41.jpg")
    gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)

    # 查找所有匹配的位置
    locations = find_matches(template_gray, gray)

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
