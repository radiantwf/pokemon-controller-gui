from recognition.ocr.paddle import PaddleOCRWrapper
from recognition.ocr.easy import EasyOCR
import cv2
import re
from recognition.scripts.games.pokemon.champions.teamid.type_enum import PokemonTypeType


class Pokemon:
    def __init__(self):
        self._name = ''
        self._nature = 'Serious'
        self._ability = ''
        self._item = ''
        self._moves = []
        self._evs = [0, 0, 0, 0, 0, 0]
        self.ocr_engine = PaddleOCRWrapper(lang='en', use_angle_cls=False)
        self.ocr_engine_number = EasyOCR(langs='en')
        self._stat_up_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/stat_up.png", cv2.IMREAD_GRAYSCALE)
        self._stat_down_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/stat_down.png", cv2.IMREAD_GRAYSCALE)
        self._gender_female_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/gender/female.png", cv2.IMREAD_GRAYSCALE)

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

    @staticmethod
    def _normalize_ocr_text(text):
        normalized = str(text or "").strip()
        repeated_tail_pattern = re.compile(r"\b([A-Za-z]+)([A-Za-z])\s+([A-Za-z])\s+([A-Z][A-Za-z]*)\b")
        split_initial_pattern = re.compile(r"\b([A-Za-z]+)\s+([A-Z])\s+([A-Z][A-Za-z]*)\b")
        previous = None
        while normalized != previous:
            previous = normalized
            normalized = repeated_tail_pattern.sub(
                lambda match: (
                    f"{match.group(1)}{match.group(2)} {match.group(4)}"
                    if match.group(3) == match.group(2)
                    else match.group(0)
                ),
                normalized
            )
            normalized = split_initial_pattern.sub(
                lambda match: (
                    f"{match.group(1)} {match.group(3)}"
                    if match.group(3).startswith(match.group(2))
                    else match.group(0)
                ),
                normalized
            )
        return normalized

    def process_moves_image(self, image, i):
        regions = [
            (80, 32, 230, 40)  # name
            , (90, 82, 226, 32)  # ability
            , (90, 130, 226, 38)  # item
            , (500, 39, 175, 30)  # move1
            , (500, 86, 175, 30)  # move2
            , (500, 129, 175, 30)  # move3
            , (500, 174, 175, 30)  # move4
            , (315, 34, 33, 33)  # gender
            , (353, 35, 32, 32)  # type1
            , (395, 35, 32, 32)  # type2
            , (10, 2, 72, 72)  # pokemon
        ]
        # cv2.imwrite(f"./name{i}.png", image[regions[0][1]:regions[0][1] + regions[0][3], regions[0][0]:regions[0][0] + regions[0][2]])
        # cv2.imwrite(f"./ability{i}.png", image[regions[1][1]:regions[1][1] + regions[1][3], regions[1][0]:regions[1][0] + regions[1][2]])
        # cv2.imwrite(f"./item{i}.png", image[regions[2][1]:regions[2][1] + regions[2][3], regions[2][0]:regions[2][0] + regions[2][2]])
        # cv2.imwrite(f"./move1{i}.png", image[regions[3][1]:regions[3][1] + regions[3][3], regions[3][0]:regions[3][0] + regions[3][2]])
        # cv2.imwrite(f"./move2{i}.png", image[regions[4][1]:regions[4][1] + regions[4][3], regions[4][0]:regions[4][0] + regions[4][2]])
        # cv2.imwrite(f"./move3{i}.png", image[regions[5][1]:regions[5][1] + regions[5][3], regions[5][0]:regions[5][0] + regions[5][2]])
        # cv2.imwrite(f"./move4{i}.png", image[regions[6][1]:regions[6][1] + regions[6][3], regions[6][0]:regions[6][0] + regions[6][2]])
        # cv2.imwrite(f"./gender{i}.png", image[regions[7][1]:regions[7][1] + regions[7][3], regions[7][0]:regions[7][0] + regions[7][2]])
        # cv2.imwrite(f"./type1_{i}.png", image[regions[8][1]:regions[8][1] + regions[8][3], regions[8][0]:regions[8][0] + regions[8][2]])
        # cv2.imwrite(f"./type2_{i}.png", image[regions[9][1]:regions[9][1] + regions[9][3], regions[9][0]:regions[9][0] + regions[9][2]])
        cv2.imwrite(f"./img_champions/pokeImg{i}.png", image[regions[10][1]:regions[10][1] + regions[10][3], regions[10][0]:regions[10][0] + regions[10][2]])

        results = self.ocr_engine.batch_recognize_regions(
            image,
            regions,
            upscale=2.5,
            enable_preprocess=True,
        )

        self._name = self._normalize_ocr_text(results[0]['text'])
        self._ability = self._normalize_ocr_text(results[1]['text'])
        self._item = self._normalize_ocr_text(results[2]['text'])
        self._moves = [self._normalize_ocr_text(results[i]['text']) for i in range(3, 7)]

        if self._item == 'Beak Sharp':
            self._item == 'Sharp Beak'
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

        gender_image = image[regions[7][1]:regions[7][1] + regions[7][3], regions[7][0]:regions[7][0] + regions[7][2]]
        type1_image = image[regions[8][1]:regions[8][1] + regions[8][3], regions[8][0]:regions[8][0] + regions[8][2]]
        type2_image = image[regions[9][1]:regions[9][1] + regions[9][3], regions[9][0]:regions[9][0] + regions[9][2]]
        if self._name == 'Rotom':
            if self._match_type(type2_image, PokemonTypeType.Water):
                self._name = 'Rotom-Wash'
            elif self._match_type(type2_image, PokemonTypeType.Fire):
                self._name = 'Rotom-Heat'
            elif self._match_type(type2_image, PokemonTypeType.Grass):
                self._name = 'Rotom-Mow'
            elif self._match_type(type2_image, PokemonTypeType.Ice):
                self._name = 'Rotom-Frost'
            elif self._match_type(type2_image, PokemonTypeType.Flying):
                self._name = 'Rotom-Fly'
        elif self._name == 'Ninetales':
            if self._match_type(type1_image, PokemonTypeType.Ice):
                self._name = self._name + '-Alola'
        elif self._name == 'Zoroark':
            if self._match_type(type1_image, PokemonTypeType.Normal):
                self._name = self._name + '-Hisui'
        elif self._name == 'Arcanine':
            if self._match_type(type2_image, PokemonTypeType.Rock):
                self._name = self._name + '-Hisui'
        elif self._name == 'Typhlosion':
            if self._match_type(type2_image, PokemonTypeType.Ghost):
                self._name = self._name + '-Hisui'
        elif self._name == 'Tauros':
            if self._match_type(type2_image, PokemonTypeType.Fire):
                self._name = self._name + '-Paldea-Blaze'
            elif self._match_type(type2_image, PokemonTypeType.Water):
                self._name = self._name + '-Paldea-Aqua'
            elif self._match_type(type1_image, PokemonTypeType.Fighting):
                self._name = self._name + '-Paldea-Combat'
        elif self._name == 'Basculegion' \
                or self._name == 'Meowstic':
            if self._match_gender_female(gender_image):
                self._name = self._name + '-F'

        # 肯泰罗 第二属性 水火

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
            int(self.ocr_engine_number.recognize_number_roi(image, region, 6))
            for region in regions
        ]
        self._evs = results
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self._stat_up_point = self._match_stat_modify(gray, up=True)
        self._stat_down_point = self._match_stat_modify(gray, up=False)
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

    def _match_gender_female(self, image, max_value_threshold=0.8):
        if self._gender_female_template is None or image.size == 0:
            return False
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if gray.shape[0] < self._gender_female_template.shape[0] or gray.shape[1] < self._gender_female_template.shape[1]:
            return False
        match = cv2.matchTemplate(
            gray, self._gender_female_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        return max_val >= max_value_threshold

    def _match_type(self, image, type: PokemonTypeType, max_value_threshold=0.8):
        if image.size == 0:
            return False
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(PokemonTypeType.get_template_path(type), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False
        if gray.shape[0] < template.shape[0] or gray.shape[1] < template.shape[1]:
            return False
        match = cv2.matchTemplate(
            gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        return max_val >= max_value_threshold

    def _match_stat_modify(self, gray, up=True, max_value_threshold=0.8):
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
        s = f"{self._name}"
        if self._item != '':
            s += f" @ {self._item}"
        s += "\n"
        if self._ability != '':
            s += f"Ability: {self._ability}\n"
        if any([var != 0 for var in self._evs]):
            is_first = True
            for i in range(len(self._evs)):
                if self._evs[i] == 0:
                    continue
                if is_first:
                    is_first = False
                    s += f"EVs: "
                else:
                    s += " / "
                s += f"{self._evs[i]}"
                if i == 0:
                    s += " HP"
                elif i == 1:
                    s += " Atk"
                elif i == 2:
                    s += " Def"
                elif i == 3:
                    s += " SpA"
                elif i == 4:
                    s += " SpD"
                elif i == 5:
                    s += " Spe"
            s += "\n"
        s += f"{self._nature} Nature\n"
        for move in self._moves:
            if move != '':
                s += f"- {move}\n"
        return s
