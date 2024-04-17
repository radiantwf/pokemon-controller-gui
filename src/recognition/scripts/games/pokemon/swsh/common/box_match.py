import cv2


class ChatBoxNextMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._egg_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/common/chatbox_next.png")
        self._egg_template = cv2.cvtColor(
            self._egg_template, cv2.COLOR_BGR2GRAY)

    def next_arrow_check(self, image, threshold=0.9) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        x, y, w, h = 738, 488, 31, 31
        crop_gray = gray[y:y+h, x:x+w]
        match = cv2.matchTemplate(
            crop_gray, self._sv_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False
