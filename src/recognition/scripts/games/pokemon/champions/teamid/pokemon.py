from dataclasses import dataclass
from enum import Enum, auto

from recognition.ocr.paddle import PaddleOCRWrapper
from recognition.ocr.easy import EasyOCR
import cv2
import re
from recognition.scripts.games.pokemon.champions.teamid.type_enum import PokemonTypeType


class PokemonFormSource(Enum):
    TYPE1 = auto()
    TYPE2 = auto()
    GENDER = auto()


@dataclass(frozen=True)
class PokemonFormRule:
    name: str
    source: PokemonFormSource
    matcher: object
    suffix: str


class Pokemon:
    _FORM_RULES = (
        PokemonFormRule("Rotom", PokemonFormSource.TYPE2, PokemonTypeType.Water, "-Wash"),
        PokemonFormRule("Rotom", PokemonFormSource.TYPE2, PokemonTypeType.Fire, "-Heat"),
        PokemonFormRule("Rotom", PokemonFormSource.TYPE2, PokemonTypeType.Grass, "-Mow"),
        PokemonFormRule("Rotom", PokemonFormSource.TYPE2, PokemonTypeType.Ice, "-Frost"),
        PokemonFormRule("Rotom", PokemonFormSource.TYPE2, PokemonTypeType.Flying, "-Fly"),
        
        # 阿罗拉地区
        PokemonFormRule("Raticate", PokemonFormSource.TYPE1, PokemonTypeType.Dark, "-Alola"),
        PokemonFormRule("Ninetales", PokemonFormSource.TYPE1, PokemonTypeType.Ice, "-Alola"),
        PokemonFormRule("Raichu", PokemonFormSource.TYPE2, PokemonTypeType.Psychic, "-Alola"),
        PokemonFormRule("Sandslash", PokemonFormSource.TYPE1, PokemonTypeType.Ice, "-Alola"),
        PokemonFormRule("Dugtrio", PokemonFormSource.TYPE2, PokemonTypeType.Steel, "-Alola"),
        PokemonFormRule("Persian", PokemonFormSource.TYPE1, PokemonTypeType.Dark, "-Alola"),
        PokemonFormRule("Golem", PokemonFormSource.TYPE2, PokemonTypeType.Electric, "-Alola"),
        PokemonFormRule("Muk", PokemonFormSource.TYPE2, PokemonTypeType.Dark, "-Alola"),
        PokemonFormRule("Marowak", PokemonFormSource.TYPE1, PokemonTypeType.Fire, "-Alola"),
        PokemonFormRule("Exeggutor", PokemonFormSource.TYPE2, PokemonTypeType.Dragon, "-Alola"),
        
        # 洗翠地区
        PokemonFormRule("Zoroark", PokemonFormSource.TYPE1, PokemonTypeType.Normal, "-Hisui"),
        PokemonFormRule("Arcanine", PokemonFormSource.TYPE2, PokemonTypeType.Rock, "-Hisui"),
        PokemonFormRule("Typhlosion", PokemonFormSource.TYPE2, PokemonTypeType.Ghost, "-Hisui"),
        PokemonFormRule("Samurott", PokemonFormSource.TYPE2, PokemonTypeType.Dark, "-Hisui"),
        PokemonFormRule("Goodra", PokemonFormSource.TYPE1, PokemonTypeType.Steel, "-Hisui"),
        PokemonFormRule("Avalugg", PokemonFormSource.TYPE2, PokemonTypeType.Rock, "-Hisui"),
        PokemonFormRule("Decidueye", PokemonFormSource.TYPE2, PokemonTypeType.Fighting, "-Hisui"),
        PokemonFormRule("Electrode", PokemonFormSource.TYPE2, PokemonTypeType.Grass, "-Hisui"),
        PokemonFormRule("Lilligant", PokemonFormSource.TYPE2, PokemonTypeType.Fighting, "-Hisui"),
        PokemonFormRule("Braviary", PokemonFormSource.TYPE1, PokemonTypeType.Psychic, "-Hisui"),
        
        # 帕底亚地区
        PokemonFormRule("Tauros", PokemonFormSource.TYPE2, PokemonTypeType.Fire, "-Paldea-Blaze"),
        PokemonFormRule("Tauros", PokemonFormSource.TYPE2, PokemonTypeType.Water, "-Paldea-Aqua"),
        PokemonFormRule("Tauros", PokemonFormSource.TYPE1, PokemonTypeType.Fighting, "-Paldea-Combat"),
        
        # 伽勒尔地区
        PokemonFormRule("Slowbro", PokemonFormSource.TYPE1, PokemonTypeType.Poison, "-Galar"),
        PokemonFormRule("Slowking", PokemonFormSource.TYPE1, PokemonTypeType.Poison, "-Galar"),
        PokemonFormRule("Stunfisk", PokemonFormSource.TYPE2, PokemonTypeType.Electric, "-Galar"),
        PokemonFormRule("Rapidash", PokemonFormSource.TYPE1, PokemonTypeType.Psychic, "-Galar"),
        PokemonFormRule("Weezing", PokemonFormSource.TYPE2, PokemonTypeType.Fairy, "-Galar"),
        PokemonFormRule("Articuno", PokemonFormSource.TYPE1, PokemonTypeType.Psychic, "-Galar"),
        PokemonFormRule("Zapdos", PokemonFormSource.TYPE1, PokemonTypeType.Fighting, "-Galar"),
        PokemonFormRule("Moltres", PokemonFormSource.TYPE1, PokemonTypeType.Dark, "-Galar"),
        PokemonFormRule("Darmanitan", PokemonFormSource.TYPE1, PokemonTypeType.Ice, "-Galar"),
        
        PokemonFormRule("Oinkologne", PokemonFormSource.GENDER, "F", "-F"),
        PokemonFormRule("Indeedee", PokemonFormSource.GENDER, "F", "-F"),
        PokemonFormRule("Basculegion", PokemonFormSource.GENDER, "F", "-F"),
        PokemonFormRule("Meowstic", PokemonFormSource.GENDER, "F", "-F"),
    )

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

        if self._name == 'Floette':
            self._name = 'Floette-Eternal'

        if self._item == 'Beak Sharp':
            self._item = 'Sharp Beak'
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
            elif self._moves[i] == "Dual V Wingbeat":
                self._moves[i] = 'Dual Wingbeat'
            elif self._moves[i] == "Strength n Sap":
                self._moves[i] = 'Strength Sap'
            elif self._moves[i] == 'Fllare Blitz':
                self._moves[i] = 'Flare Blitz'
            elif self._moves[i].startswith('lce '):
                self._moves[i] = self._moves[i].replace('lce ', 'Ice ')
            elif self._moves[i].startswith('lron '):
                self._moves[i] = self._moves[i].replace('lron ', 'Iron ')

        gender_image = image[regions[7][1]:regions[7][1] + regions[7][3], regions[7][0]:regions[7][0] + regions[7][2]]
        type1_image = image[regions[8][1]:regions[8][1] + regions[8][3], regions[8][0]:regions[8][0] + regions[8][2]]
        type2_image = image[regions[9][1]:regions[9][1] + regions[9][3], regions[9][0]:regions[9][0] + regions[9][2]]
        self._apply_form_rule(gender_image, type1_image, type2_image)

    def _apply_form_rule(self, gender_image, type1_image, type2_image):
        for rule in self._FORM_RULES:
            if self._name != rule.name:
                continue
            if self._match_form_rule(rule, gender_image, type1_image, type2_image):
                self._name += rule.suffix
                return

    def _match_form_rule(self, rule: PokemonFormRule, gender_image, type1_image, type2_image):
        if rule.source == PokemonFormSource.GENDER:
            return rule.matcher == "F" and self._match_gender_female(gender_image)

        images = {
            PokemonFormSource.TYPE1: type1_image,
            PokemonFormSource.TYPE2: type2_image,
        }
        image = images.get(rule.source)
        if image is None:
            return False
        return self._match_type(image, rule.matcher)

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
        total = sum(self._evs)
        if total != 66:
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')
            print(f"Warning: {self._name} has {total} EVs, expected 66\n\n")
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')

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
