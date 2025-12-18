from enum import Enum
import multiprocessing
import time
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
import numpy as np
import pytesseract

ZaDlcDonutRecipes = {
    "闪耀力 - 混合": [(5, 4), (3, 4)],
    "道具力 - 混合": [(3, 4), (1, 4)],
    "闪耀力 - 扁樱果": [(8, 8)],
    "道具力 - 佛柑果": [(6, 8)],
}

ZaDlcDonutPowerLevels1 = [0, 1, 2, 3]
ZaDlcDonutPowerLevels2 = [-1, 0, 1, 2, 3]


class ZaDlcDonutPowerType(Enum):
    Sparkling = "闪耀力"
    Alpha = "头目力"
    Humungo = "大大力"
    Teensy = "小小力"
    Item = "道具力"
    BigHaul = "多多力"


class ZaDlcDonutItemType(Enum):
    Berries = "树果"
    Balls = "球"


class ZaDlcTypeType(Enum):
    All = "全属性"
    Normal = "一般"
    Flying = "飞行"
    Fire = "火"
    Psychic = "超能力"
    Water = "水"
    Bug = "虫"
    Electric = "电"
    Rock = "岩石"
    Grass = "草"
    Ghost = "幽灵"
    Ice = "冰"
    Dragon = "龙"
    Fighting = "格斗"
    Dark = "恶"
    Poison = "毒"
    Steel = "钢"
    Ground = "地面"
    Fairy = "妖精"


tessedit_char_whitelist = "".join(dict.fromkeys(
    "".join(e.value for e in ZaDlcDonutPowerType)
    + "".join(e.value for e in ZaDlcDonutItemType)
    + "".join(e.value for e in ZaDlcTypeType)
    + "Lv:0123"
))


class ZaDlcDonut(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(ZaDlcDonut.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, ZaDlcDonut.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False

        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._ns1 = self.get_para("ns1") if paras and "ns1" in paras else False
        self._recipe = [(8, 8), (0, 0), (0, 0)]
        if paras and "Recipe" in paras:
            recipe_items = ZaDlcDonutRecipes.get(self.get_para("Recipe"))
            if recipe_items:
                for idx, item in enumerate(recipe_items[:len(self._recipe)]):
                    self._recipe[idx] = item
        self._sparkling_power_level = self.get_para("SparklingPowerLevel") if paras and "SparklingPowerLevel" in paras else 0
        self._sparkling_power_type_list = self.get_para("SparklingPowerType") if paras and "SparklingPowerType" in paras else [e.value for e in ZaDlcTypeType]
        self._alpha_power_level = self.get_para("AlphaPowerLevel") if paras and "AlphaPowerLevel" in paras else 0
        self._humungo_power_level = self.get_para("HumungoPowerLevel") if paras and "HumungoPowerLevel" in paras else 0
        self._teensy_power_level = self.get_para("TeensyPowerLevel") if paras and "TeensyPowerLevel" in paras else 0
        self._item_power_level = self.get_para("ItemPowerLevel") if paras and "ItemPowerLevel" in paras else 0
        self._item_power_type_list = self.get_para("ItemPowerType") if paras and "ItemPowerType" in paras else [e.value for e in ZaDlcDonutItemType]
        self._big_haul_power_level = self.get_para("BigHaulPowerLevel") if paras and "BigHaulPowerLevel" in paras else 0

    @staticmethod
    def script_name() -> str:
        return "宝可梦-ZA-DLC-刷三明治"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["loop"] = ScriptParameter(
            "loop", int, -1, "运行次数")
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["ns1"] = ScriptParameter(
            "ns1", bool, False, "是否使用NS1")
        recipes = list(ZaDlcDonutRecipes.keys())
        paras["Recipe"] = ScriptParameter(
            "Recipe", str, recipes[0], "使用三明治配方", recipes)
        paras["SparklingPowerLevel"] = ScriptParameter(
            "SparklingPowerLevel", int, ZaDlcDonutPowerLevels1[len(ZaDlcDonutPowerLevels1) - 1], "闪耀力等级", ZaDlcDonutPowerLevels1)
        paras["SparklingPowerType"] = ScriptParameter(
            "SparklingPowerType", list, [e.value for e in ZaDlcTypeType], "闪耀力属性", [e.value for e in ZaDlcTypeType])
        paras["AlphaPowerLevel"] = ScriptParameter(
            "AlphaPowerLevel", int, ZaDlcDonutPowerLevels2[0], "头目力等级(-1时排除这个条件)", ZaDlcDonutPowerLevels2)
        paras["HumungoPowerLevel"] = ScriptParameter(
            "HumungoPowerLevel", int, ZaDlcDonutPowerLevels2[0], "(或)大大力等级(-1时排除这个条件)", ZaDlcDonutPowerLevels2)
        paras["TeensyPowerLevel"] = ScriptParameter(
            "TeensyPowerLevel", int, ZaDlcDonutPowerLevels2[0], "(或)小小力等级(-1时排除这个条件)", ZaDlcDonutPowerLevels2)
        paras["ItemPowerLevel"] = ScriptParameter(
            "ItemPowerLevel", int, ZaDlcDonutPowerLevels1[0], "道具力等级", ZaDlcDonutPowerLevels1)
        paras["ItemPowerType"] = ScriptParameter(
            "ItemPowerType", list, [e.value for e in ZaDlcDonutItemType], "道具力类型", [e.value for e in ZaDlcDonutItemType])
        paras["BigHaulPowerLevel"] = ScriptParameter(
            "BigHaulPowerLevel", int, ZaDlcDonutPowerLevels1[0], "多多力等级", ZaDlcDonutPowerLevels1)

        return paras

    def _check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False

    def _check_cycles(self):
        if self._loop <= 0:
            return False
        if self.cycle_times > self._loop:
            self.send_log("运行次数已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False

    def process_frame(self):
        if self._check_durations():
            return
        if self._check_cycles():
            return

        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self._prepare_step_list):
                    self.set_cycle_begin()
                    self._cycle_step_index = 0
                    return
                self._prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Cycle:
            if self.current_frame_count == 1:
                self._cycle_init()
            if self._jump_next_frame:
                self.clear_frame_queue()
                self._jump_next_frame = False
                return
            if self._cycle_step_index >= 0 and self._cycle_step_index < len(self._cycle_step_list):
                self._cycle_step_list[self._cycle_step_index]()
            else:
                self.macro_stop()
                self.set_cycle_continue()
                self._cycle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCycle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self._check_pokemon_index = -1
        self.send_log(f"开始运行{ZaDlcDonut.script_name()}脚本")

    def on_cycle(self):
        run_time_span = self.run_time_span
        log_txt = ""
        log_txt += f"[{ZaDlcDonut.script_name()}] 脚本运行中，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                           3600) / 60)}分{int(run_time_span % 60)}秒"
        self.send_log(log_txt)
        self._check_pokemon_index = -1

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(ZaDlcDonut.script_name(
        ), self.cycle_times, int(run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    @property
    def _prepare_step_list(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self._prepare_step_index += 1

    @property
    def _cycle_step_list(self):
        return [
            self.step_0,
            self.step_1,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(ZaDlcDonut.script_name(), self.cycle_times - 1, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        pass

    def _cycle_init(self):
        pass

    def step_0(self):
        self.macro_run("pokemon.za.common.restart_game",
                       loop=1, paras={"ns1": str(self._ns1), "restore_backup": True}, block=True, timeout=None)
        paras = {
            "berry1_position": self._recipe[0][0],
            "berry1_count": self._recipe[0][1],
            "berry2_position": self._recipe[1][0],
            "berry2_count": self._recipe[1][1],
            "berry3_position": self._recipe[2][0],
            "berry3_count": self._recipe[2][1],
        }
        self.macro_run("recognition.pokemon.za.dlc.donut.donut",
                       loop=1, paras=paras, block=True, timeout=None)
        self._jump_next_frame = True
        self._cycle_step_index += 1

    def step_1(self):
        current_frame = self.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        text1, text2, text3 = self._ocr_power_text(gray_frame)
        power1 = self._split_ocr_power_text(text1)
        power2 = self._split_ocr_power_text(text2)
        power3 = self._split_ocr_power_text(text3)
        if power1[0] is not None:
            sub_text = f": {power1[1].value}" if power1[1] is not None else ""
            self.send_log(f"行1：{power1[0].value}{sub_text} Lv.{power1[2]}")
        else:
            self.send_log("行1：未匹配到有效数据")
            if text1 and text1 != '':
                self.send_log(f"行1：原始文本：{text1}")
        if power2[0] is not None:
            sub_text = f": {power2[1].value}" if power2[1] is not None else ""
            self.send_log(f"行2：{power2[0].value}{sub_text} Lv.{power2[2]}")
        else:
            self.send_log("行2：未匹配到有效数据")
            if text2 and text2 != '':
                self.send_log(f"行2：原始文本：{text2}")
        if power3[0] is not None:
            sub_text = f": {power3[1].value}" if power3[1] is not None else ""
            self.send_log(f"行3：{power3[0].value}{sub_text} Lv.{power3[2]}")
        else:
            self.send_log("行3：未匹配到有效数据")
            if text3 and text3 != '':
                self.send_log(f"行3：原始文本：{text3}")

        result = True
        result &= (self._check_sparkling_power(power1[0], power1[1], power1[2])
                   or self._check_sparkling_power(power2[0], power2[1], power2[2])
                   or self._check_sparkling_power(power3[0], power3[1], power3[2]))
        if not result:
            self.send_log("闪耀力检测未通过")
            self._cycle_step_index += 1
            return
        result &= (self._alpha_power_level == -1 and self._humungo_power_level == -1 and self._teensy_power_level == -1) or (
            (self._alpha_power_level != -1 and
             (self._check_alpha_power(power1[0], power1[1], power1[2])
              or self._check_alpha_power(power2[0], power2[1], power2[2])
              or self._check_alpha_power(power3[0], power3[1], power3[2])))
            or (self._humungo_power_level != -1 and (self._check_humungo_power(power1[0], power1[1], power1[2])
                                                     or self._check_humungo_power(power2[0], power2[1], power2[2])
                or self._check_humungo_power(power3[0], power3[1], power3[2])))
            or (self._teensy_power_level != -1 and (self._check_teensy_power(power1[0], power1[1], power1[2])
                                                    or self._check_teensy_power(power2[0], power2[1], power2[2])
                or self._check_teensy_power(power3[0], power3[1], power3[2])))
        )
        if not result:
            self.send_log("头目力、大大力、小小力检测未通过")
            self._cycle_step_index += 1
            return
        result &= (self._check_item_power(power1[0], power1[1], power1[2])
                   or self._check_item_power(power2[0], power2[1], power2[2])
                   or self._check_item_power(power3[0], power3[1], power3[2]))
        if not result:
            self.send_log("道具力检测未通过")
            self._cycle_step_index += 1
            return
        result &= (self._check_big_haul_power(power1[0], power1[1], power1[2])
                   or self._check_big_haul_power(power2[0], power2[1], power2[2])
                   or self._check_big_haul_power(power3[0], power3[1], power3[2]))
        if not result:
            self.send_log("多多力检测未通过")
            self._cycle_step_index += 1
            return
        self._finished_process()
        self._cycle_step_index += 1

    def _ocr_power_text(self, gray):
        crop_x1, crop_y1, crop_w1, crop_h1 = 125, 410, 150, 22
        crop_x2, crop_y2, crop_w2, crop_h2 = 125, 435, 150, 22
        crop_x3, crop_y3, crop_w3, crop_h3 = 125, 460, 150, 22
        crop_gray1 = gray[crop_y1:crop_y1+crop_h1, crop_x1:crop_x1+crop_w1]
        crop_gray1 = cv2.resize(crop_gray1, (crop_w1*60, crop_h1*60))
        crop_gray2 = gray[crop_y2:crop_y2+crop_h2, crop_x2:crop_x2+crop_w2]
        crop_gray2 = cv2.resize(crop_gray2, (crop_w2*60, crop_h2*60))
        crop_gray3 = gray[crop_y3:crop_y3+crop_h3, crop_x3:crop_x3+crop_w3]
        crop_gray3 = cv2.resize(crop_gray3, (crop_w3*60, crop_h3*60))
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist="' + tessedit_char_whitelist + '"'

        # 对图片进行二值化处理
        _, thresh = cv2.threshold(
            crop_gray1, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        text1 = pytesseract.image_to_string(
            closing, lang='chi_sim+eng', config=custom_config)
        text1 = " ".join(text1.split())

        # 对图片进行二值化处理
        _, thresh = cv2.threshold(
            crop_gray2, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        text2 = pytesseract.image_to_string(
            closing, lang='chi_sim+eng', config=custom_config)
        text2 = " ".join(text2.split())

        # 对图片进行二值化处理
        _, thresh = cv2.threshold(
            crop_gray3, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        text3 = pytesseract.image_to_string(
            closing, lang='chi_sim+eng', config=custom_config)
        text3 = " ".join(text3.split())

        return (text1, text2, text3)

    def _split_ocr_power_text(self, text: str):
        powerStr, subPowerStr, lv = None, None, 0
        try:
            lindex = text.rindex('L')
        except ValueError:
            return None, None, 0

        lvStr = text[lindex:]
        text = text[:lindex]
        splits = text.split(':')
        powerStr = splits[0].strip()
        if len(splits) >= 2:
            subPowerStr = splits[1].strip()
        match powerStr:
            case '闪力' | '闪闪力':
                powerStr = '闪耀力'
        try:
            power = ZaDlcDonutPowerType(powerStr)
        except ValueError:
            power = None

        if power == ZaDlcDonutPowerType.Sparkling:
            try:
                subPower = ZaDlcTypeType(subPowerStr)
            except ValueError:
                subPower = None
        elif power == ZaDlcDonutPowerType.Item:
            try:
                subPower = ZaDlcDonutItemType(subPowerStr)
            except ValueError:
                subPower = None
        else:
            subPower = None

        if power:
            lvStr = lvStr.strip("Lv.:")
            try:
                lv = int(lvStr)
            except ValueError:
                lv = 0
        return power, subPower, lv

    def _check_sparkling_power(self, power: ZaDlcDonutPowerType, subPower, lv: int):
        if (self._sparkling_power_level <= 0):
            return True
        if power != ZaDlcDonutPowerType.Sparkling or lv < self._sparkling_power_level:
            return False
        if not (isinstance(subPower, ZaDlcTypeType)):
            return False
        allow_types = self._sparkling_power_type_list if isinstance(self._sparkling_power_type_list, list) else [self._sparkling_power_type_list]
        if not allow_types:
            return True
        if subPower == ZaDlcTypeType.All:
            return True
        if subPower.value in allow_types:
            return True
        return False

    def _check_alpha_power(self, power: ZaDlcDonutPowerType, subPower, lv: int):
        if (self._alpha_power_level <= 0):
            return True
        if power != ZaDlcDonutPowerType.Alpha or lv < self._alpha_power_level:
            return False
        return True

    def _check_humungo_power(self, power: ZaDlcDonutPowerType, subPower, lv: int):
        if (self._humungo_power_level <= 0):
            return True
        if power != ZaDlcDonutPowerType.Humungo or lv < self._humungo_power_level:
            return False
        return True

    def _check_teensy_power(self, power: ZaDlcDonutPowerType, subPower, lv: int):
        if (self._teensy_power_level <= 0):
            return True
        if power != ZaDlcDonutPowerType.Teensy or lv < self._teensy_power_level:
            return False
        return True

    def _check_item_power(self, power: ZaDlcDonutPowerType, subPower, lv: int):
        if (self._item_power_level <= 0):
            return True
        if power != ZaDlcDonutPowerType.Item or lv < self._item_power_level:
            return False
        if not (isinstance(subPower, ZaDlcDonutItemType)):
            return False
        allow_types = self._item_power_type_list if isinstance(self._item_power_type_list, list) else [self._item_power_type_list]
        if not allow_types:
            return True
        if subPower.value in allow_types:
            return True
        return False

    def _check_big_haul_power(self, power: ZaDlcDonutPowerType, subPower, lv: int):
        if (self._big_haul_power_level <= 0):
            return True
        if power != ZaDlcDonutPowerType.BigHaul or lv < self._big_haul_power_level:
            return False
        return True
