import cv2


class PokemonDetailShinyMatch:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self._shiny_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/common/pokemon_detail_shiny_icon.png")
        self._shiny_icon_template = cv2.cvtColor(
            self._shiny_icon_template, cv2.COLOR_BGR2GRAY)

    def match_shiny(self, gray, threshold=0.9) -> bool:
        x, y, w, h = 70, 287, 32, 24
        crop_gray = gray[y:y+h, x:x+w]
        match = cv2.matchTemplate(
            crop_gray, self._shiny_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= threshold:
            return True
        return False
