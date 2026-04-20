from recognition.ocr.easy import EasyOCR
from recognition.ocr.rapidocr import RapidOCR
from typing import Tuple
import cv2
from recognition.scripts.games.pokemon.champions.usage.pokemon import DetailTagEnum
from datetime import datetime


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

    def _check_pokemon_forme(self, image, row, pokemon, isTeammate=False):
        pokemon_regions = [[1142, 306, 120, 94]  # row1
                           , [1142, 438, 120, 94]  # row2
                           , [1142, 570, 120, 94]  # row3
                           , [1142, 705, 120, 94]  # row4
                           , [1142, 710, 120, 94]  # row4-2
                           , [1142, 842, 120, 94]]  # row5
        if isTeammate:
            pokemon_regions = [[730, 325, 120, 94]  # row1
                               , [730, 452, 120, 94]  # row2
                               , [730, 578, 120, 94]  # row3
                               , [730, 708, 120, 94]  # row4
                               , [730, 715, 120, 94]  # row4-2
                               , [730, 842, 120, 94]]  # row5
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

    def recognize_pokemon(self, image, cursor_rank: int = 0) -> Tuple[str, bool]:
        regions = [[1253, 327, 284, 58]  # row1
                   , [1253, 458, 284, 58]  # row2
                   , [1253, 591, 284, 58]  # row3
                   , [1253, 723, 284, 58]  # row4
                   , [1253, 728, 284, 58]  # row4-2
                   , [1253, 860, 284, 58]]  # row5

        if cursor_rank >= 5:
            row = 4
        else:
            row = cursor_rank - 1
        rank_region = regions[row].copy()
        rank_region[0] = 1005
        rank_region[2] = 118

        rank = int(self.ocr_engine_number.recognize_champions_row_number_roi(image, rank_region))
        text, score = self.ocr_engine.recognize_champions_row_text_roi(image, regions[row])
        if text is not None:
            text = self._fix_error_text(text.strip())

        isLast = False

        if rank == cursor_rank-1:
            row = 5
            rank_region = regions[row].copy()
            rank_region[0] = 1105
            rank_region[2] = 118
            text, score = self.ocr_engine.recognize_champions_row_text_roi(image, regions[row])
            if text is not None:
                text = self._fix_error_text(text.strip())
            isLast = True
        forme = self._check_pokemon_forme(image, row, text)
        if forme is not None:
            text = forme

        if text not in self._pokemon_dict:
            self._pokemon_dict[text] = rank
        else:
            pokemon_regions = [[1142, 306, 120, 94]  # row1
                               , [1142, 438, 120, 94]  # row2
                               , [1142, 570, 120, 94]  # row3
                               , [1142, 705, 120, 94]  # row4
                               , [1142, 710, 120, 94]  # row4-2
                               , [1142, 842, 120, 94]]  # row5
            pokemon_region = pokemon_regions[row]
            cv2.imwrite(f'img_champions/usage/{rank}-{text}.png', image[pokemon_region[1]:pokemon_region[1]+pokemon_region[3], pokemon_region[0]:pokemon_region[0]+pokemon_region[2]])

        return text, isLast

    def recognize_detail(self, image, tag: DetailTagEnum, index: int) -> Tuple[str, float, bool]:
        isLast = False
        if index >= 4:
            row = 4
        else:
            row = index

        text, percent, rank = self._recognize_detail_row(image, tag, row)
        print(rank, text, percent)
        if rank == 0:
            isLast = True
            return text, percent, isLast
        elif index == rank:
            isLast = True
            row = 5
            text, percent, rank = self._recognize_detail_row(image, tag, row)
            print(rank, text, percent)
        return text, percent, isLast

    def _recognize_detail_row(self, image, tag: DetailTagEnum, row: int) -> Tuple[str, float]:
        text_top = [343, 474, 600, 726, 736, 862]
        text_height = 56
        evs_regions = [[740, 374, 556, 48]  # row1
                       , [740, 498, 556, 48]  # row2
                       , [740, 627, 556, 48]  # row3
                       , [740, 750, 556, 48]  # row4
                       , [740, 760, 556, 48]  # row4-2
                       , [740, 886, 556, 48]]  # row5

        if tag == DetailTagEnum.Move:
            text_left = 846
            text_width = 370
        elif tag == DetailTagEnum.Item:
            text_left = 852
            text_width = 460
        elif tag == DetailTagEnum.Teammate:
            text_left = 840
            text_width = 310
        elif tag == DetailTagEnum.Nature:
            text_left = 862
            text_width = 130
        elif tag == DetailTagEnum.Ability:
            text_left = 794
            text_width = 440

        percent_regions = [[616, 372, 114, 48]  # row1
                           , [616, 500, 114, 48]  # row2
                           , [616, 627, 114, 48]  # row3
                           , [616, 750, 114, 48]  # row4
                           , [616, 763, 114, 48]  # row4-2
                           , [616, 890, 114, 48]]  # row5

        if tag == DetailTagEnum.EVs:
            text_region = evs_regions[row]
            percent_region = percent_regions[row]
        else:
            text_region = [text_left, text_top[row], text_width, text_height]
            percent_region = percent_regions[row]

        rank_region = percent_region.copy()
        if tag != DetailTagEnum.Teammate:
            rank_region[1] = rank_region[1] - 40
            rank_region[3] = 40
        else:
            rank_region[1] = rank_region[1] - 50
            rank_region[3] = rank_region[3] + 50

        if tag != DetailTagEnum.Teammate:
            percent = self.ocr_engine_number.recognize_champions_row_number_roi(image, percent_region)
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

        rank = int(self.ocr_engine_number.recognize_champions_row_number_roi(image, rank_region))
        if tag == DetailTagEnum.Teammate:
            forme = self._check_pokemon_forme(image, row, text, True)
            if forme is not None:
                text = forme

        if text == "" and rank != 0:
            cv2.imwrite(f'img_champions/usage/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}-{tag.name}-{rank}.png', image[text_region[1]:text_region[1]+text_region[3], text_region[0]:text_region[0]+text_region[2]])

        return text, percent, rank

    fix_replace_text = {
        "之枢": "之躯",
        "之驱": "之躯",
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
                     "玛拉": "玛狃拉",
                     "玛扭拉": "玛狃拉",
                     "智挥": "智挥猩",
                     "制之爪": "先制之爪",
                     "炽焰哮虎": "炽焰咆哮虎",
                     "西狮海王": "西狮海",
                     "西狮海王": "西狮海壬",
                     "國快龙": "快龙",
                     "車淘气": "淘气",
                     "淘气車": "淘气",
                     "淘气電": "淘气",
                     "寞想": "冥想",
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
                     "慧星拳": "彗星拳",
                     "聚岩狼人": "鬃岩狼人",
                     "拔雪": "拨雪",
                     "拔沙": "拨沙",
                     }

    def _fix_error_text(self, text: str) -> str:
        if text in self.fix_text_dict:
            return self.fix_text_dict[text]
        for key in self.fix_replace_text:
            text = text.replace(key, self.fix_replace_text[key])
        return text
