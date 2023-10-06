import cv2
import numpy as np


def find_matches(template_gray, gray, threshold=0.9):
    # 在目标图片中查找匹配
    result = cv2.matchTemplate(gray, template_gray, cv2.TM_CCOEFF_NORMED)

    # 查找所有匹配的位置
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))

    # 返回所有匹配的位置
    return locations

def main():
    egg_template = cv2.imread(
        "resources/img/recognition/pokemon/sv/eggs/box/egg.png")
    template_gray = cv2.cvtColor(
        egg_template, cv2.COLOR_BGR2GRAY)
    
    mat = cv2.imread(
        "CapturesTest/background-11.jpg")
    gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)

    # 查找所有匹配的位置
    locations = find_matches(template_gray, gray)

    # 在目标图片中标记所有匹配的位置
    for loc in locations:
        cv2.rectangle(mat, loc, (loc[0] + egg_template.shape[1], loc[1] + egg_template.shape[0]), (0, 0, 255), 2)
        print(loc)

    # 显示结果
    cv2.imshow("Matches", mat)
    cv2.waitKey(0)

if __name__ == "__main__":
    main()
