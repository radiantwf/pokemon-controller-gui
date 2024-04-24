import sys
import cv2
import numpy as np
import colorsys
import pytesseract

sys.path.append('./src')
from recognition.scripts.games.pokemon.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.games.pokemon.sv.common.image_match.combat_match import CombatMatch


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
    _template = cv2.imread(
        "resources/img/recognition/pokemon/swsh/dynamax_adventures/battle/dynamax_icon.png")
    template_gray = cv2.cvtColor(
        _template, cv2.COLOR_BGR2GRAY)
# Captures/20231016101856-recognize.jpg
# Captures/20231016105433-recognize.jpg
# Captures/20231016105434-recognize.jpg
# Captures/20231016105436-recognize.jpg

    mat = cv2.imread(
        "Captures/20240425011448-recognize.jpg")
    ret = CombatMatch().combat_check(mat)
    print(ret)
    gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)

    main_color = get_main_color(mat, (226, 290, 6, 6))
    print(main_color)

    crop_x, crop_y, crop_w, crop_h = 522, 424, 52, 32
    crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
    # 查找所有匹配的位置
    locations = find_matches(template_gray, crop_gray, 0.6, 10)

    # 在目标图片中标记所有匹配的位置
    for loc in locations:
        cv2.rectangle(mat, (crop_x + loc[0] ,
                      crop_y + loc[1]), (crop_x + loc[0] + _template.shape[1],
                      crop_y + loc[1] + _template.shape[0]), (0, 0, 255), 2)
        print(loc)

    # 显示结果
    cv2.imshow("Matches", mat)
    cv2.waitKey(0)

    for i in range(4):
        txt = ocr_move_effect(gray, 689, 351 + 53 * i, 54, 18)
        print(txt)
        txt = ocr_move_pp(gray, 872, 335 + 53 * i, 24, 27)
        print(txt)



def ocr_move_effect(gray, crop_x, crop_y, crop_w, crop_h):
    crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
    crop_gray = cv2.resize(crop_gray, (crop_w*50, crop_h*50))
    _, thresh1 = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    cv2.imshow("thresh1", thresh1)
    cv2.imshow("closing", closing)
    cv2.waitKey(0)

    # 使用Tesseract进行文字识别
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=效果绝佳有不好'
    text = pytesseract.image_to_string(closing, lang='chi_sim', config=custom_config)
    text = "".join(text.split())
    return text

def ocr_move_pp(gray, crop_x, crop_y, crop_w, crop_h):
    crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
    crop_gray = cv2.resize(crop_gray, (crop_w*10, crop_h*10))
    # 对图片进行二值化处理
    _, thresh1 = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

    # 使用Tesseract进行文字识别
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(closing, config=custom_config)
    text = "".join(text.split())
    num = int(text) if text.isdigit() else 0
    return num

if __name__ == "__main__":
    main()
