import cv2


class ChatBoxMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._next_arrow_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/common/chatbox_next.png")
        self._next_arrow_template = cv2.cvtColor(
            self._next_arrow_template, cv2.COLOR_BGR2GRAY)
        
        self._select_box_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/common/chatbox_select_box.png")
        self._select_box_template = cv2.cvtColor(
            self._select_box_template, cv2.COLOR_BGR2GRAY)

    def match_next_arrow(self, gray, threshold=0.9) -> bool:
        x, y, w, h = 738, 488, 31, 31
        crop_gray = gray[y:y+h, x:x+w]
        match = cv2.matchTemplate(
            crop_gray, self._next_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False

    def match_select_box(self, gray, threshold=0.8) -> bool:
        x, y, w, h = 738, 488, 31, 31
        crop_gray = gray[y:y+h, x:x+w]
        match = cv2.matchTemplate(
            crop_gray, self._select_box_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False
