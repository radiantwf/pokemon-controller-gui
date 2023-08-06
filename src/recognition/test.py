import cv2
import os


def main():
    # 获取用户主目录的绝对路径
    home_dir = os.path.expanduser('~')

    # 从文件读取图片
    img_path = os.path.join(
        home_dir, 'workspace/pokemon/pokemon-controller-gui/Captures/20230806223006-66.jpg')
    img = cv2.imread(img_path)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 截取图片
    img2 = img[100: 130, 415: 415+240]
    img2_path = os.path.join(
        home_dir, 'workspace/pokemon/pokemon-controller-gui/Captures/20230806223006-66-2.jpg')
    cv2.imwrite(img2_path, img2)

    # 遍历Captures目录下的所有jpg文件
    captures_dir = os.path.join(
        home_dir, 'workspace/pokemon/pokemon-controller-gui/Captures')
    for file in os.listdir(captures_dir):
        if file.endswith(".jpg"):
            img_path = os.path.join(captures_dir, file)
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = img[100: 130, 415: 415+240]
            match = cv2.matchTemplate(img, img2, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, p = cv2.minMaxLoc(match)
            if max_val > 0.75:
                print(file, max_val, p)
            

if __name__ == "__main__":
    main()
