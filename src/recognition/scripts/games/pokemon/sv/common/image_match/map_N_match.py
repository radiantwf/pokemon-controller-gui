import cv2

from recognition.image_func import find_matches


class MapNIconMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._map_N_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/raid/map_N_icon.jpg", cv2.IMREAD_GRAYSCALE)

    def match_map_N_icon_template(self, gray, threshold=0.8) -> bool:
        rect = (864, 371, 13, 13)
        crop_gray = gray[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        res = cv2.matchTemplate(
            crop_gray, self._map_N_icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
