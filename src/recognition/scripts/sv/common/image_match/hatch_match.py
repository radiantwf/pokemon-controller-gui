import cv2
from cv2 import typing

from recognition.image_func import find_matches


class HatchMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._hatched_tag_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/eggs/hatched-tag.png")
        self._hatched_tag_template = cv2.cvtColor(
            self._hatched_tag_template, cv2.COLOR_BGR2GRAY)

    def hatched_tag_check(self, image, threshold=0.8) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._hatched_tag_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False
