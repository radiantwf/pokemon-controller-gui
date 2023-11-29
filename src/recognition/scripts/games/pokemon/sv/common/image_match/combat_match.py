import cv2
from cv2 import typing

from recognition.image_func import find_matches


class CombatMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._combat_action_template_1 = cv2.imread(
            "resources/img/recognition/pokemon/sv/combat/combat_action_icon_1.png")
        self._combat_action_template_1 = cv2.cvtColor(
            self._combat_action_template_1, cv2.COLOR_BGR2GRAY)
        self._combat_action_template_2 = cv2.imread(
            "resources/img/recognition/pokemon/sv/combat/combat_action_icon_2.png")
        self._combat_action_template_2 = cv2.cvtColor(
            self._combat_action_template_2, cv2.COLOR_BGR2GRAY)
        self._combat_action_template_3 = cv2.imread(
            "resources/img/recognition/pokemon/sv/combat/combat_action_icon_3.png")
        self._combat_action_template_3 = cv2.cvtColor(
            self._combat_action_template_3, cv2.COLOR_BGR2GRAY)
        self._combat_action_template_4 = cv2.imread(
            "resources/img/recognition/pokemon/sv/combat/combat_action_icon_4.png")
        self._combat_action_template_4 = cv2.cvtColor(
            self._combat_action_template_4, cv2.COLOR_BGR2GRAY)

    def combat_check(self, image, threshold=0.8) -> bool:
        matches_counter = 0
        x, y, w, h = 738, 345, 45, 180
        crop_image = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(crop_image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._combat_action_template_1, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            matches_counter += 1
        match = cv2.matchTemplate(
            gray, self._combat_action_template_2, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            matches_counter += 1
        match = cv2.matchTemplate(
            gray, self._combat_action_template_3, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            matches_counter += 1
        match = cv2.matchTemplate(
            gray, self._combat_action_template_4, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            matches_counter += 1
        if matches_counter >= 3:
            return True
        return False
