from turtle import width
from recognition.ocr.easy import EasyOCR
from recognition.ocr.rapidocr import RapidOCR
from typing import Tuple
import cv2
from recognition.scripts.games.pokemon.champions.usage.pokemon import DetailTagEnum
from datetime import datetime

pokemons_regions_y = [297, 441, 561, 693, 825]
pokemons_top_clipped_offset_y = 8


details_regions_y = [321, 447, 573, 699, 825]
details_top_clipped_offset_y = 12


class Recognize:
    _instance = None
    _pokemon_dict = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.ocr_engine = RapidOCR(
            upscale=1,              # 放大倍数
            enable_preprocess=True,   # 启用预处理
        )
        self.ocr_engine_number = EasyOCR(langs='en')
        self._details_clipped_row_segment_template = cv2.imread(
            "resources/img/recognition/pokemon/champions/usage/details_clipped_row_segment.png", cv2.IMREAD_GRAYSCALE)

    def check_detail_top_clipped(self, image, max_value_threshold: float = 0.8):
        region = [556, 286, 786, 28]
        crop = image[region[1]:region[1]+region[3], region[0]:region[0]+region[2]]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._details_clipped_row_segment_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        return max_val >= max_value_threshold

    def recognize_pokemon(self, image, cursor_rank: int = 0) -> Tuple[str, bool]:
        top_clipped = False
        if cursor_rank > 4:
            top_clipped = True
            row = 3
        else:
            row = cursor_rank - 1

        top = pokemons_regions_y.copy()
        for i in range(len(top)):
            if top_clipped:
                top[i] += pokemons_top_clipped_offset_y
        pokemon_x = 1142
        pokemon_width = 120
        pokemon_height = 94
        pokemon_offsets_y = 9
        pokemon_regions = []
        for i in range(len(top)):
            pokemon_regions.append([pokemon_x, top[i] + pokemon_offsets_y, pokemon_width, pokemon_height])

        text_x = 1253
        text_width = 284
        text_height = 58
        text_offsets_y = 30
        text_regions = []
        for i in range(len(top)):
            text_regions.append([text_x, top[i] + text_offsets_y, text_width, text_height])

        text_region = text_regions[row].copy()
        rank_region = text_regions[row].copy()
        rank_region[0] = 1005
        rank_region[2] = 118

        rank = int(self.ocr_engine_number.recognize_champions_row_number_roi(image, rank_region))
        text, score = self.ocr_engine.recognize_champions_row_text_roi(image, text_region)
        if text is not None:
            text = self._fix_error_text(text.strip())

        isLast = False

        if rank == cursor_rank-1:
            row = 4
            rank_region = text_region.copy()
            rank_region[0] = 1105
            rank_region[2] = 118
            text, score = self.ocr_engine.recognize_champions_row_text_roi(image, text_region)
            if text is not None:
                text = self._fix_error_text(text.strip())
            isLast = True
        forme = self._check_pokemon_forme(image, top_clipped, row, text)
        if forme is not None:
            text = forme

        if text not in self._pokemon_dict:
            self._pokemon_dict[text] = rank
        else:
            pokemon_region = pokemon_regions[row]
            cv2.imwrite(f'img_champions/usage/{rank}-{text}.png', image[pokemon_region[1]:pokemon_region[1]+pokemon_region[3], pokemon_region[0]:pokemon_region[0]+pokemon_region[2]])

        return text, isLast

    def recognize_detail_row_rank(self, image, tag: DetailTagEnum, top_clipped: bool, row: int) -> int:
        top = details_regions_y.copy()
        for i in range(len(top)):
            if top_clipped:
                top[i] += details_top_clipped_offset_y
        x = 616
        width = 114
        height = 40 if tag != DetailTagEnum.Teammate else 98
        offsets_y = 11 if tag != DetailTagEnum.Teammate else 1
        regions = []
        for i in range(len(top)):
            regions.append([x, top[i] + offsets_y, width, height])

        rank_region = regions[row]
        rank = int(self.ocr_engine_number.recognize_champions_row_number_roi(image, rank_region))
        return rank

    def recognize_detail_row(self, image, tag: DetailTagEnum, top_clipped: bool, row: int) -> Tuple[str, float, bool]:
        top = details_regions_y.copy()
        for i in range(len(top)):
            if top_clipped:
                top[i] += details_top_clipped_offset_y
        if tag == DetailTagEnum.Move:
            text_x = 846
            text_width = 370
        elif tag == DetailTagEnum.Item:
            text_x = 852
            text_width = 460
        elif tag == DetailTagEnum.Teammate:
            text_x = 840
            text_width = 310
        elif tag == DetailTagEnum.Nature:
            text_x = 862
            text_width = 130
        elif tag == DetailTagEnum.Ability:
            text_x = 794
            text_width = 440
        else:
            text_x = 0
            text_width = 100
        text_height = 56
        text_offsets_y = 22
        text_regions = []
        for i in range(len(top)):
            text_regions.append([text_x, top[i] + text_offsets_y, text_width, text_height])

        evs_x = 740
        evs_width = 556
        evs_height = 48
        evs_offsets_y = 53
        evs_regions = []
        for i in range(len(top)):
            evs_regions.append([evs_x, top[i] + evs_offsets_y, evs_width, evs_height])

        percent_x = 616
        percent_width = 114
        percent_height = 48
        percent_offsets_y = 51
        percent_regions = []
        for i in range(len(top)):
            percent_regions.append([percent_x, top[i] + percent_offsets_y, percent_width, percent_height])

        percent_region = percent_regions[row]

        text_region = evs_regions[row] if tag == DetailTagEnum.EVs else text_regions[row]

        if tag != DetailTagEnum.Teammate:
            percent = self.ocr_engine_number.recognize_champions_row_number_roi(image, percent_region)
            percent_region = percent_regions[row] if tag != DetailTagEnum.Teammate else None
        else:
            percent = 0

        if tag != DetailTagEnum.EVs:
            text, score = self.ocr_engine.recognize_champions_row_text_roi(image, text_region)
            if text is not None:
                text = self._fix_error_text(text.strip())
        else:
            evs = []
            for i in range(6):
                width = evs_regions[row][2] // 6
                x = evs_regions[row][0] + i * width
                ev = int(self.ocr_engine_number.recognize_champions_row_number_roi(image, [x, evs_regions[row][1], width, evs_regions[row][3]]))
                evs.append(ev)
            text = f"{evs[0]}/{evs[1]}/{evs[2]}/{evs[3]}/{evs[4]}/{evs[5]}"
            if text == "0/0/0/0/0/0" and percent == 0.0:
                text = ""
        if text is None:
            text = ""

        if tag == DetailTagEnum.Teammate:
            forme = self._check_pokemon_forme(image, top_clipped, row, text, True)
            if forme is not None:
                text = forme

        if text == "":
            cv2.imwrite(f'img_champions/usage/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}-{tag.name}-{row}.png', image[text_region[1]:text_region[1]+text_region[3], text_region[0]:text_region[0]+text_region[2]])
        return text, percent

    def _check_pokemon_forme(self, image, top_clipped: bool, row, pokemon, isTeammate=False):
        top = details_regions_y.copy() if isTeammate else pokemons_regions_y.copy()
        for i in range(len(top)):
            if top_clipped:
                top[i] += details_top_clipped_offset_y if isTeammate else pokemons_top_clipped_offset_y
        x = 730 if isTeammate else 1142
        width = 120
        height = 94
        pokemon_offsets_y = 4 if isTeammate else 9
        pokemon_regions = []
        for i in range(len(top)):
            pokemon_regions.append([x, top[i] + pokemon_offsets_y, width, height])

        pokemon_region = pokemon_regions[row]
        forme = None
        best_score = float("-inf")
        lists = []
        if pokemon == '洛托姆':
            lists = [
                '洛托姆',
                '清洗洛托姆',
                '加热洛托姆',
                '结冰洛托姆',
                '切割洛托姆',
                '旋转洛托姆',
            ]
        elif pokemon == '雷丘':
            lists = [
                '雷丘',
                '雷丘-阿罗拉的样子',
            ]
        elif pokemon == '九尾':
            lists = [
                '九尾',
                '九尾-阿罗拉的样子',
            ]
        elif pokemon == '风速狗':
            lists = [
                '风速狗',
                '风速狗-洗翠的样子',
            ]
        elif pokemon == '呆壳兽':
            lists = [
                '呆壳兽',
                '呆壳兽-伽勒尔的样子',
            ]
        elif pokemon == '呆呆王':
            lists = [
                '呆呆王',
                '呆呆王-伽勒尔的样子',
            ]
        elif pokemon == '肯泰罗':
            lists = [
                '肯泰罗',
                '肯泰罗-帕底亚的样子（斗战种）',
                '肯泰罗-帕底亚的样子（火炽种）',
                '肯泰罗-帕底亚的样子（水澜种）',
            ]
        elif pokemon == '超能妙喵':
            lists = [
                '超能妙喵',
                '超能妙喵-雌性',
            ]
        elif pokemon == '幽尾玄鱼':
            lists = [
                '幽尾玄鱼',
                '幽尾玄鱼-雌性',
            ]
        elif pokemon == '泥巴鱼':
            lists = [
                '泥巴鱼',
                '泥巴鱼-伽勒尔的样子',
            ]
        elif pokemon == '索罗亚克':
            lists = [
                '索罗亚克',
                '索罗亚克-洗翠的样子',
            ]
        elif pokemon == '火暴兽':
            lists = [
                '火暴兽',
                '火暴兽-洗翠的样子',
            ]
        elif pokemon == '大剑鬼':
            lists = [
                '大剑鬼',
                '大剑鬼-洗翠的样子',
            ]
        elif pokemon == '黏美龙':
            lists = [
                '黏美龙',
                '黏美龙-洗翠的样子',
            ]
        elif pokemon == '冰岩怪':
            lists = [
                '冰岩怪',
                '冰岩怪-洗翠的样子',
            ]
        elif pokemon == '狙射树枭':
            lists = [
                '狙射树枭',
                '狙射树枭-洗翠的样子',
            ]
        elif pokemon == '鬃岩狼人':
            lists = [
                '鬃岩狼人',
                '鬃岩狼人-黑夜的样子',
                '鬃岩狼人-黄昏的样子',
            ]
        elif pokemon == '南瓜怪人':
            lists = [
                '南瓜怪人',
                '南瓜怪人-大',
                '南瓜怪人-特大',
                '南瓜怪人-小',
            ]
        try:
            gray = cv2.cvtColor(
                image[
                    pokemon_region[1]:pokemon_region[1] + pokemon_region[3],
                    pokemon_region[0]:pokemon_region[0] + pokemon_region[2]
                ],
                cv2.COLOR_BGR2GRAY
            )
            for l in lists:
                path = f'resources/img/recognition/pokemon/champions/usage/pokemon/{l}.png'
                template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if template is None:
                    continue
                match = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(match)
                print(isTeammate, pokemon, l, max_val)
                if max_val > best_score:
                    best_score = max_val
                    forme = l
        except Exception:
            cv2.imwrite(
                f'img_champions/usage/{pokemon}.png',
                image[
                    pokemon_region[1]:pokemon_region[1] + pokemon_region[3],
                    pokemon_region[0]:pokemon_region[0] + pokemon_region[2]
                ]
            )
        # if not isTeammate:
        #     cv2.imwrite(f'img_champions/usage/{pokemon}.png', image[pokemon_region[1]:pokemon_region[1]+pokemon_region[3], pokemon_region[0]:pokemon_region[0]+pokemon_region[2]])
        return forme

    fix_replace_text = {
        "之枢": "之躯",
        "之驱": "之躯",
        "组射": "狙射",
        "树案": "树枭",
        "：": "",
        "、": "",
        "，": "",
        "　": "",
    }

    fix_text_dict = {"花叶带": "花叶蒂-永恒之花",
                     "花叶蒂": "花叶蒂-永恒之花",
                     "花叶": "花叶蒂-永恒之花",
                     "毒蛙": "毒骷蛙",
                     "花叶带进化石": "花叶蒂进化石",
                     "花叶糖进化石": "花叶蒂进化石",
                     "大拉": "大狃拉",
                     "大扭拉": "大狃拉",
                     "迷人之": "迷人之躯",
                     "玛拉": "玛狃拉",
                     "玛扭拉": "玛狃拉",
                     "智挥": "智挥猩",
                     "智挥握": "智挥猩",
                     "制之爪": "先制之爪",
                     "炽焰哮虎": "炽焰咆哮虎",
                     "西狮海王": "西狮海",
                     "西狮海王": "西狮海壬",
                     "國快龙": "快龙",
                     "車淘气": "淘气",
                     "淘气車": "淘气",
                     "淘气電": "淘气",
                     "寞想": "冥想",
                     "真想": "冥想",
                     "挑鲜": "挑衅",
                     "终爲之歌": "终焉之歌",
                     "踏脚": "跺脚",
                     "长喙": "长嚎",
                     "DD金勾臂": "ＤＤ金勾臂",
                     "胆小、": "胆小",
                     "干香果": "千香果",
                     "香果": "千香果",
                     "食士": "食土",
                     "追计": "诡计",
                     "造计": "诡计",
                     "追异咒语": "诡异咒语",
                     "追异光语": "诡异咒语",
                     "花石翼龙": "化石翼龙",
                     "选失棺": "迭失棺",
                     "选失板": "迭失板",
                     "超能艳驼": "超能艳鸵",
                     "拦路": "挡路",
                     "反邹": "反刍",
                     "反鱼": "反刍",
                     "反多": "反刍",
                     "伴攻": "佯攻",
                     "踩脚": "跺脚",
                     "霹果": "霹霹果",
                     "软沙子": "柔软沙子",
                     "秘剑·千重涛": "秘剑・千重涛",
                     "调堡": "碉堡",
                     "满珊": "蹒跚",
                     "追角鹿": "诡角鹿",
                     "追角座": "诡角鹿",
                     "投猴": "投掷猴",
                     "嘴大鸟": "铳嘴大鸟",
                     "冷水": "冷水猿",
                     "爆香": "爆香猿",
                     "花椰": "花椰猿",
                     "慧星拳": "彗星拳",
                     "繁岩狼人": "鬃岩狼人",
                     "聚岩狼人": "鬃岩狼人",
                     "卡比": "卡比兽",
                     "双倍率还": "双倍奉还",
                     "拔雪": "拨雪",
                     "拔沙": "拨沙",
                     "海气": "淘气",
                     "快手述击": "快手还击",
                     "怕寂奠": "怕寂寞",
                     "冰冻之": "冰冻之躯",
                     "锐利乌嘴": "锐利鸟嘴",
                     "挑畔": "挑衅",
                     "抗胖": "挑衅",
                     "草蛋果": "草蚕果",
                     "十万马边": "十万马力",
                     "最当": "反刍",
                     "逾计": "诡计",
                     "热水電": "热水",
                     "": "",
                     }

    def _fix_error_text(self, text: str) -> str:
        if text in self.fix_text_dict:
            return self.fix_text_dict[text]
        for key in self.fix_replace_text:
            text = text.replace(key, self.fix_replace_text[key])
        return text
