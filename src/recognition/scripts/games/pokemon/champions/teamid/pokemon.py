from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import cv2
import re
import os
from recognition.scripts.games.pokemon.champions.teamid.type_enum import PokemonTypeType
from recognition.ocr.easy import EasyOCR
from recognition.scripts.games.pokemon.champions.teamid.ocr import RapidOCR
from recognition.scripts.games.pokemon.champions.teamid.locale import Dict, DictTag


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

    def __init__(self, number_ocr_engine=None):
        self._name = ''
        self._nature = 'Serious'
        self._ability = ''
        self._item = ''
        self._moves = []
        self._evs = [0, 0, 0, 0, 0, 0]
        self._ocr_errors = []
        self._conversion_errors = []
        self._ev_errors = []
        self.ocr_engine = RapidOCR(
            upscale=1,              # 放大倍数
            enable_preprocess=True,   # 启用预处理
        )
        self.ocr_engine_number = (
            number_ocr_engine if number_ocr_engine is not None
            else EasyOCR(langs='en', shared=False)
        )
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

    def _lookup_english_or_original(self, tag: DictTag, text: str, pokemon_index: int, pokemon_name: str, field_name: str) -> str:
        if text is None or str(text).strip() == "":
            return text
        try:
            return Dict.lookup_zh_english_text(tag, text)
        except KeyError as e:
            log = (
                f"宝可梦序号 {pokemon_index} ({pokemon_name}) "
                f"{field_name} 中英文转换失败，保留原值: {text}. {e}"
            )
            self._conversion_errors.append(log)
            print(f"[OCR Dict] {log}")
            return text

    def _record_empty_ocr_results(self, results, field_names, pokemon_index: int, pokemon_name: str):
        for result, field_name in zip(results, field_names):
            text = self._normalize_ocr_text(result.get("text") if isinstance(result, dict) else None)
            if text:
                continue
            log = (
                f"宝可梦序号 {pokemon_index} ({pokemon_name}) "
                f"{field_name} OCR 识别为空，score={float((result or {}).get('score') or 0.0):.3f}"
            )
            if isinstance(result, dict) and result.get("error"):
                log += f"，error={result['error']}"
            self._ocr_errors.append(log)
            print(f"[OCR Empty] {log}")

    def process_moves_image(self, image, i, output_dir="./img_champions", save_images: bool = True):
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
        poke_output_dir = Path(output_dir) / f"poke{i}"
        if save_images:
            os.makedirs(poke_output_dir, exist_ok=True)
            cv2.imwrite(str(poke_output_dir / "name.png"), image[regions[0][1]:regions[0][1] + regions[0][3], regions[0][0]:regions[0][0] + regions[0][2]])
            cv2.imwrite(str(poke_output_dir / "ability.png"), image[regions[1][1]:regions[1][1] + regions[1][3], regions[1][0]:regions[1][0] + regions[1][2]])
            cv2.imwrite(str(poke_output_dir / "item.png"), image[regions[2][1]:regions[2][1] + regions[2][3], regions[2][0]:regions[2][0] + regions[2][2]])
            cv2.imwrite(str(poke_output_dir / "move1.png"), image[regions[3][1]:regions[3][1] + regions[3][3], regions[3][0]:regions[3][0] + regions[3][2]])
            cv2.imwrite(str(poke_output_dir / "move2.png"), image[regions[4][1]:regions[4][1] + regions[4][3], regions[4][0]:regions[4][0] + regions[4][2]])
            cv2.imwrite(str(poke_output_dir / "move3.png"), image[regions[5][1]:regions[5][1] + regions[5][3], regions[5][0]:regions[5][0] + regions[5][2]])
            cv2.imwrite(str(poke_output_dir / "move4.png"), image[regions[6][1]:regions[6][1] + regions[6][3], regions[6][0]:regions[6][0] + regions[6][2]])
            cv2.imwrite(str(poke_output_dir / "gender.png"), image[regions[7][1]:regions[7][1] + regions[7][3], regions[7][0]:regions[7][0] + regions[7][2]])
            cv2.imwrite(str(poke_output_dir / "type1.png"), image[regions[8][1]:regions[8][1] + regions[8][3], regions[8][0]:regions[8][0] + regions[8][2]])
            cv2.imwrite(str(poke_output_dir / "type2.png"), image[regions[9][1]:regions[9][1] + regions[9][3], regions[9][0]:regions[9][0] + regions[9][2]])
        pokemon_image = image[regions[10][1]:regions[10][1] + regions[10][3], regions[10][0]:regions[10][0] + regions[10][2]]
        if save_images:
            cv2.imwrite(str(poke_output_dir / "poke.png"), pokemon_image)
            cv2.imwrite(str(Path(output_dir) / f"pokeImg{i}.png"), pokemon_image)
        results = self.ocr_engine.batch_recognize_regions(
            image,
            regions
        )
        field_names = ("name", "ability", "item", "move1", "move2", "move3", "move4")

        name = self._normalize_ocr_text(results[0]['text'])
        ability = self._normalize_ocr_text(results[1]['text'])
        item = self._normalize_ocr_text(results[2]['text'])
        moves = [self._normalize_ocr_text(results[i]['text']) for i in range(3, 7)]

        pokemon_log_name = name or f"poke{i}"
        self._record_empty_ocr_results(results[:7], field_names, i, pokemon_log_name)
        self._name = self._lookup_english_or_original(DictTag.POKEMON, name, i, pokemon_log_name, "name")
        pokemon_log_name = self._name or pokemon_log_name
        self._ability = self._lookup_english_or_original(DictTag.ABILITY, ability, i, pokemon_log_name, "ability")
        self._item = self._lookup_english_or_original(DictTag.ITEM, item, i, pokemon_log_name, "item")
        self._moves = [
            self._lookup_english_or_original(DictTag.MOVE, move, i, pokemon_log_name, f"move{move_index + 1}")
            for move_index, move in enumerate(moves)
        ]

        gender_image = image[regions[7][1]:regions[7][1] + regions[7][3], regions[7][0]:regions[7][0] + regions[7][2]]
        type1_image = image[regions[8][1]:regions[8][1] + regions[8][3], regions[8][0]:regions[8][0] + regions[8][2]]
        type2_image = image[regions[9][1]:regions[9][1] + regions[9][3], regions[9][0]:regions[9][0] + regions[9][2]]
        self._confirm_pokemon_form(pokemon_image, gender_image, type1_image, type2_image)

    def _confirm_pokemon_form(self, pokemon_image, gender_image, type1_image, type2_image):
        for rule in self._FORM_RULES:
            if self._name != rule.name:
                continue
            if self._match_form_rule(rule, gender_image, type1_image, type2_image):
                self._name += rule.suffix
                return

        pokemon_dir = Path("resources/img/recognition/pokemon/champions/team_id/pokemon") / self._name
        if not pokemon_dir.exists() or not pokemon_dir.is_dir():
            return

        best_name = None
        best_score = None
        for template_path in sorted(pokemon_dir.glob("*.png")):
            template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
            score = self._compare_pokemon_image(pokemon_image, template)
            if score is None or score < 0.8:
                continue
            if best_score is None or score > best_score:
                best_score = score
                best_name = template_path.stem

        if best_name is not None:
            self._name = best_name

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

    @staticmethod
    def _compare_pokemon_image(image, template):
        if template is None or image.size == 0:
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if gray.shape[0] < template.shape[0] or gray.shape[1] < template.shape[1]:
            template = cv2.resize(template, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_AREA)

        match = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        return max_val

    def process_states_image(self, image, i=0, output_dir="./img_champions", save_images: bool = True):
        regions = [
            (322, 83, 34, 28),  # evs hp
            (322, 127, 34, 29),  # atk
            (322, 172, 34, 29),  # def
            (672, 83, 34, 28),  # spa
            (672, 127, 34, 29),  # spd
            (672, 172, 34, 29),  # spe
        ]
        poke_output_dir = Path(output_dir) / f"poke{i}"
        if save_images:
            os.makedirs(poke_output_dir, exist_ok=True)
            cv2.imwrite(str(poke_output_dir / "stat_hp.png"), image[regions[0][1]:regions[0][1] + regions[0][3], regions[0][0]:regions[0][0] + regions[0][2]])
            cv2.imwrite(str(poke_output_dir / "stat_atk.png"), image[regions[1][1]:regions[1][1] + regions[1][3], regions[1][0]:regions[1][0] + regions[1][2]])
            cv2.imwrite(str(poke_output_dir / "stat_def.png"), image[regions[2][1]:regions[2][1] + regions[2][3], regions[2][0]:regions[2][0] + regions[2][2]])
            cv2.imwrite(str(poke_output_dir / "stat_spa.png"), image[regions[3][1]:regions[3][1] + regions[3][3], regions[3][0]:regions[3][0] + regions[3][2]])
            cv2.imwrite(str(poke_output_dir / "stat_spd.png"), image[regions[4][1]:regions[4][1] + regions[4][3], regions[4][0]:regions[4][0] + regions[4][2]])
            cv2.imwrite(str(poke_output_dir / "stat_spe.png"), image[regions[5][1]:regions[5][1] + regions[5][3], regions[5][0]:regions[5][0] + regions[5][2]])

        stat_regions = regions
        results = [
            int(self.ocr_engine_number.recognize_stats_number_roi(image, region, 6))
            for region in stat_regions
        ]
        self._evs = results
        total = sum(self._evs)
        if total != 66:
            warning_msg = f"宝可梦序号 {i} ({self._name}) 努力值合计错误: {total}，期望 66，识别值 {self._evs}"
            self._ev_errors.append(warning_msg)
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')
            print(f"{warning_msg}\n\n")
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self._stat_up_point = self._match_stat_modify(gray, up=True)
        self._stat_down_point = self._match_stat_modify(gray, up=False)
        self._set_nature(self._stat_up_point, self._stat_down_point, stat_regions)

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

    @property
    def ocr_errors(self):
        return list(self._ocr_errors)

    @property
    def conversion_errors(self):
        return list(self._conversion_errors)

    @property
    def ev_errors(self):
        return list(self._ev_errors)

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
