from recognition.ocr.paddle import PaddleOCRWrapper
import cv2


class Pokemon:
    def __init__(self):
        self._name = ''
        self._nature = 'Serious'
        self.ocr_engine = PaddleOCRWrapper(lang='en', use_angle_cls=False)
        self.ocr_engine_number = self.ocr_engine
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
            (80, 32, 230, 40),  # name
            (90, 82, 226, 32),  # ability
            (90, 130, 226, 38),  # item
            (500, 39, 175, 30),  # move1
            (500, 86, 175, 30),  # move2
            (500, 129, 175, 30),  # move3
            (500, 174, 175, 30),  # move4
        ]
        # cv2.imwrite("name.png", image[regions[0][1]:regions[0][1] + regions[0][3], regions[0][0]:regions[0][0] + regions[0][2]])
        # cv2.imwrite("ability.png", image[regions[1][1]:regions[1][1] + regions[1][3], regions[1][0]:regions[1][0] + regions[1][2]])
        # cv2.imwrite("item.png", image[regions[2][1]:regions[2][1] + regions[2][3], regions[2][0]:regions[2][0] + regions[2][2]])
        # cv2.imwrite("move1.png", image[regions[3][1]:regions[3][1] + regions[3][3], regions[3][0]:regions[3][0] + regions[3][2]])
        # cv2.imwrite("move2.png", image[regions[4][1]:regions[4][1] + regions[4][3], regions[4][0]:regions[4][0] + regions[4][2]])
        # cv2.imwrite("move3.png", image[regions[5][1]:regions[5][1] + regions[5][3], regions[5][0]:regions[5][0] + regions[5][2]])
        # cv2.imwrite("move4.png", image[regions[6][1]:regions[6][1] + regions[6][3], regions[6][0]:regions[6][0] + regions[6][2]])
        results = self.ocr_engine.batch_recognize_regions(
            image,
            regions,
            upscale=2.5,
            enable_preprocess=True,
        )

        self._name = results[0]['text'].strip()
        # if self._name == 'Gvarados' or self._name == 'Garadbs':
        #     self._name = 'Gyarados'
        # elif self._name == 'Tvranitar':
        #     self._name = 'Tyranitar'
        # elif self._name == 'Svlveon':
        #     self._name = 'Sylveon'
        # elif self._name == 'Rhvperior':
        #     self._name = 'Rhyperior'
        # elif self._name == 'Kommo-0':
        #     self._name = 'Kommo-o'
        # elif self._name == 'Aejodacty':
        #     self._name = 'Aerodactyl'
        # elif self._name == 'Kinoamhit':
        #     self._name = 'Kingambit'

        self._ability = results[1]['text'].strip()

        self._item = results[2]['text'].strip()

        self._moves = [results[i]['text'].strip() for i in range(3, 7)]
        for i in range(4):
            if self._moves[i].startswith('Psv'):
                self._moves[i] = self._moves[i].replace('Psv', 'Psy')
            elif self._moves[i] == 'Jet Aqua':
                self._moves[i] = 'Aqua Jet'
            elif self._moves[i] == 'Rough Play':
                self._moves[i] = 'Play Rough'
            elif self._moves[i] == 'Sphere Aura':
                self._moves[i] = 'Aura Sphere'
            elif self._moves[i] == 'Bellv Drum':
                self._moves[i] = 'Belly Drum'
            elif self._moves[i] == 'Icv Wind':
                self._moves[i] = 'Icy Wind'
            elif self._moves[i] == 'Bite Bug':
                self._moves[i] = 'Bug Bite'
            elif self._moves[i] == 'Sunn Day':
                self._moves[i] = 'Sunny Day'
            elif self._moves[i] == 'IzonHead':
                self._moves[i] = 'Iron Head'
            elif self._moves[i] == 'Fllare Blitz':
                self._moves[i] = 'Flare Blitz'
            elif self._moves[i].startswith('lce '):
                self._moves[i] = self._moves[i].replace('lce ', 'Ice ')
            elif self._moves[i].startswith('lron '):
                self._moves[i] = self._moves[i].replace('lron ', 'Iron ')

        if self._item == 'Beak Sharp':
            self._item == 'Sharp Beak'

        if self._name == 'Rotom':
            if any(move == 'Hydro Pump' for move in self._moves):
                self._name = 'Rotom-Wash'
            elif any(move == 'Overheat' for move in self._moves):
                self._name = 'Rotom-Heat'
            elif any(move == 'Blizzard' for move in self._moves):
                self._name = 'Rotom-Frost'
                

    def process_states_image(self, image):
        regions = [
            (322, 83, 32, 28),  # evs hp
            (322, 127, 32, 29),  # atk
            (322, 172, 32, 29),  # def
            (672, 83, 32, 28),  # spa
            (672, 127, 32, 29),  # spd
            (672, 172, 32, 29),  # spe
        ]
        # cv2.imwrite("hp.png", image[regions[0][1]:regions[0][1] + regions[0][3], regions[0][0]:regions[0][0] + regions[0][2]])
        # cv2.imwrite("atk.png", image[regions[1][1]:regions[1][1] + regions[1][3], regions[1][0]:regions[1][0] + regions[1][2]])
        # cv2.imwrite("def.png", image[regions[2][1]:regions[2][1] + regions[2][3], regions[2][0]:regions[2][0] + regions[2][2]])
        # cv2.imwrite("spa.png", image[regions[3][1]:regions[3][1] + regions[3][3], regions[3][0]:regions[3][0] + regions[3][2]])
        # cv2.imwrite("spd.png", image[regions[4][1]:regions[4][1] + regions[4][3], regions[4][0]:regions[4][0] + regions[4][2]])
        # cv2.imwrite("spe.png", image[regions[5][1]:regions[5][1] + regions[5][3], regions[5][0]:regions[5][0] + regions[5][2]])
        results = [
            self.ocr_engine_number.recognize_number_roi(image, region)
            for region in regions
        ]
        self._evs = results
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self._stat_up_point = self._match(gray, up=True)
        self._stat_down_point = self._match(gray, up=False)
        self._set_nature(self._stat_up_point, self._stat_down_point, regions)

    def get_stat_by_point(self, point, regions):
        if point is None:
            return None
        if point[0] < regions[0][0]:
            if point[1] < regions[1][1]:
                return None
            elif point[1] < regions[2][1]:
                return "atk"
            else:
                return "def"
        else:
            if point[1] < regions[1][1]:
                return "spa"
            elif point[1] < regions[2][1]:
                return "spd"
            else:
                return "spe"

    def _set_nature(self, up_point, down_point, regions):
        if up_point is None or down_point is None:
            return
        up = self.get_stat_by_point(up_point, regions)
        down = self.get_stat_by_point(down_point, regions)
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
        else:
            str += "\n"
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
                str += f"{self._evs[i]}"
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
