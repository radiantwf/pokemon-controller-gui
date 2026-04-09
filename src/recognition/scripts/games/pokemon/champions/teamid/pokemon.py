from recognition.ocr.easy import EasyOCR
import cv2


class Pokemon:
    def __init__(self):
        self._name = ''
        self._nature = 'Serious'
        self.ocr_engine = EasyOCR()
        self._stat_up_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/stat_up.png", cv2.IMREAD_GRAYSCALE)
        self._stat_down_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/stat_down.png", cv2.IMREAD_GRAYSCALE)

        self._dict: dict = {
            "atk,def": "Lonely",
            "atk,spa": "Adamant",
            "atk,spd": "Naughty",
            "atk,spe": "Brave",
            "def,atk": "Bold",
            "def,spa": "Impish",
            "def,spd": "Lax",
            "def,spe": "Relaxed",
            "spa,atk": "Modest",
            "spa,def": "Mild",
            "spa,spd": "Rash",
            "spa,spe": "Quiet",
            "spd,atk": "Calm",
            "spd,def": "Gentle",
            "spd,spa": "Careful",
            "spd,spe": "Sassy",
            "spe,atk": "Timid",
            "spe,def": "Hasty",
            "spe,spa": "Jolly",
            "spe,spd": "Naive",
            "others": "Serious",
        }

    def process_moves_image(self, image):
        regions = [
            (80, 32, 230, 38),  # name
            (90, 82, 226, 32),  # ability
            (90, 130, 226, 38),  # item
            (500, 39, 175, 30),  # move1
            (500, 86, 175, 30),  # move2
            (500, 129, 175, 30),  # move3
            (500, 174, 175, 30),  # move4
        ]

        result = self.ocr_engine.recognize_english_roi(image, regions[0])
        self._name = result['text'].strip()
        result = self.ocr_engine.recognize_english_roi(image, regions[1])
        self._ability = result['text'].strip()
        result = self.ocr_engine.recognize_english_roi(image, regions[2])
        self._item = result['text'].strip()
        
        self._moves = [self.ocr_engine.recognize_english_roi(image, regions[i])['text'].strip() for i in range(3, 7)]

    def process_states_image(self, image):
        regions = [
            (322, 83, 32, 28),  # evs hp
            (322, 127, 32, 29),  # atk
            (322, 172, 32, 29),  # def
            (672, 83, 32, 28),  # spa
            (672, 127, 32, 29),  # spd
            (672, 172, 32, 29),  # spe
        ]
        results = [
            self.ocr_engine.recognize_number_roi(image, region)
            for region in regions
        ]
        self._evs = results
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self._stat_up_point = self._match(gray, up=True)
        self._stat_down_point = self._match(gray, up=False)
        self._set_nature(self._stat_up_point, self._stat_down_point)

    def get_stat_by_point(self, point):
        if point is None:
            return None
        if point[0] < 322:
            if point[1] < 127:
                return None
            elif point[1] < 172:
                return "atk"
            else:
                return "def"
        else:
            if point[1] < 127:
                return "spa"
            elif point[1] < 172:
                return "spd"
            else:
                return "spe"


    def _set_nature(self, up_point, down_point):
        if up_point is None or down_point is None:
            return
        up = self.get_stat_by_point(up_point)
        down = self.get_stat_by_point(down_point)
        self._nature = self._dict.get(f"{up},{down}", self._dict["others"])

    def _match(self, gray, up=True, max_value_threshold=0.8):
        if up:
            template = self._stat_up_template
        else:
            template = self._stat_down_template
        match = cv2.matchTemplate(
            gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val < max_value_threshold:
            return None
        return p

    @property
    def name(self):
        return self._name

    def __str__(self) -> str:
        str = f"{self._name}"
        if self._item != '':
            str += f" @ {self._item}\n"
        if self._ability != '':
            str += f"Ability: {self._ability}\n"
        if any([var != 0 for var in self._evs]):
            is_first = True
            for i in range(len(self._evs)):
                if self._evs[i] == 0:
                    continue
                if is_first:
                    is_first = False
                    str += f"EVs: "
                else:
                    str += " / "
                str += f"{(self._evs[i]-1)*8+4}"
                if i == 0:
                    str += " HP"
                elif i == 1:
                    str += " Atk"
                elif i == 2:
                    str += " Def"
                elif i == 3:
                    str += " SpA"
                elif i == 4:
                    str += " SpD"
                elif i == 5:
                    str += " Spe"
            str += "\n"
        str += f"{self._nature} Nature\n"
        for move in self._moves:
            if move != '':
                str += f"- {move}\n"
        return str
