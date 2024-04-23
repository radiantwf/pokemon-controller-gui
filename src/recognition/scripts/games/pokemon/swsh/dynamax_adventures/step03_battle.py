import time
from enum import Enum
from recognition.image_func import find_matches
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2
import numpy as np
import pytesseract


class SWSHDABattleResult(Enum):
    Error = -1
    Won = 0
    Lost = 1
    Running = 9


class SWSHDABattle(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._battle_status = 0
        self._last_action_time_monotonic = time.monotonic()
        self._action_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/battle/action.png")
        self._action_template = cv2.cvtColor(
            self._action_template, cv2.COLOR_BGR2GRAY)
        self._dynamax_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/battle/dynamax_icon.png")
        self._dynamax_icon_template = cv2.cvtColor(
            self._dynamax_icon_template, cv2.COLOR_BGR2GRAY)
        self._choose_move_arrow_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/battle/choose_move_arrow.png")
        self._choose_move_arrow_template = cv2.cvtColor(
            self._choose_move_arrow_template, cv2.COLOR_BGR2GRAY)
        self._won_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/battle/won.png")
        self._won_template = cv2.cvtColor(
            self._won_template, cv2.COLOR_BGR2GRAY)

    @property
    def battle_status(self) -> SWSHDABattleResult:
        return self._battle_status

    def _process(self) -> SubStepRunningStatus:
        self._status = self.running_status
        if self._process_step_index >= 0:
            if self._process_step_index >= len(self._process_steps):
                return SubStepRunningStatus.OK
            elif self._status == SubStepRunningStatus.Running:
                self._process_steps[self._process_step_index]()
                return self._status
            else:
                return self._status
        else:
            self._process_step_index = 0
            return self._process()

    @property
    def _process_steps(self):
        return [
            self._process_steps_0,
            # self.hatch_step_1,
            # self.hatch_step_2,
            # self.hatch_step_3,
        ]

    def _process_steps_0(self):
        if time.monotonic() - self._last_action_time_monotonic > 60:
            self._status = SubStepRunningStatus.Timeout
            self._battle_status = SWSHDABattleResult.Error
            return

        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        ret = self._check_action(gray_frame)
        if ret:
            return
        ret = self._check_dynamax_icon(gray_frame)
        if ret:
            return
        ret = self._choose_move(gray_frame)
        if ret:
            return
        ret = self._check_won(gray_frame)
        if ret:
            self._process_step_index += 1
            self._battle_status = SWSHDABattleResult.Won
            return

    # 识别 宝可梦、逃走 按钮，操作：A
    def _check_action(self, gray):
        crop_x, crop_y, crop_w, crop_h = 887, 421, 66, 110
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._action_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            self.script.macro_text_run("A:0.1", block=True)
            self.time_sleep(0.5)

            self._last_action_time_monotonic = time.monotonic()
            return True
        return False

    # 识别 极巨化图标，操作：左 -> A
    def _check_dynamax_icon(self, gray):
        crop_x, crop_y, crop_w, crop_h = 522, 424, 52, 32
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._dynamax_icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            self.script.macro_text_run("LEFT:0.1->0.2->A:0.1", block=True)
            self.time_sleep(0.2)
            self._last_action_time_monotonic = time.monotonic()
            return True
        return False

    # 识别 招式选择
    def _choose_move(self, gray):
        crop_x, crop_y, crop_w, crop_h = 620, 320, 46, 220
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        matches = find_matches(
            crop_gray, self._choose_move_arrow_template, threshold=0.7, min_distance=10)
        if len(matches) > 0:
            current_index = self._get_current_move(matches[0][1])
            if current_index < 0:
                return False
            effects = []
            pps = []
            for i in range(4):
                effect = ""
                pp = 0
                effect = self._ocr_move_effect(
                    gray, 689, 351 + 53 * i, 54, 18)
                pp = self._ocr_move_pp(
                    gray, 872, 335 + 53 * i, 24, 27)
                effects.append(effect)
                pps.append(pp)
            choice_first = -1
            choice_second = -1
            choice_third = -1
            choice_forth = -1
            for i in range(4):
                if pps[i] <= 0:
                    continue
                if effects[i] == "效果绝佳":
                    choice_first = i
                    break
                if effects[i] == "有效果" and choice_second < 0:
                    choice_second = i
                if effects[i] == "效果不好" and choice_third < 0:
                    choice_third = i
                if choice_forth < 0:
                    choice_forth = i
            target = -1
            if choice_first >= 0:
                target = choice_first
            elif choice_second >= 0:
                target = choice_second
            elif choice_third >= 0:
                target = choice_third
            else:
                target = choice_forth
            if target < 0:
                return False

            move_times = target - current_index
            if move_times < 0:
                self.script.macro_text_run(
                    "TOP:0.05->0.1", block=True, loop=abs(move_times))
            elif move_times > 0:
                self.script.macro_text_run(
                    "BOTTOM:0.05->0.1", block=True, loop=move_times)
            self.script.macro_text_run("A:0.1->0.3", block=True, loop=5)
            self.time_sleep(1)
            self._last_action_time_monotonic = time.monotonic()
            return True
        else:
            return False

    # 识别 胜利
    def _check_won(self, gray):
        crop_x, crop_y, crop_w, crop_h = 748, 445, 204, 90
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._won_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            self._last_action_time_monotonic = time.monotonic()
            return True
        return False

    def _get_current_move(self, y):
        if 0 <= y < 30:
            index = 0
        elif 53 <= y < 83:
            index = 1
        elif 106 <= y < 136:
            index = 2
        elif 159 <= y < 189:
            index = 3
        else:
            index = -1
        return index

    def _ocr_move_effect(self, gray, crop_x, crop_y, crop_w, crop_h):
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*10, crop_h*10))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(
            crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=效果绝佳没有不好'
        text = pytesseract.image_to_string(
            closing, lang='chi_sim', config=custom_config)
        text = "".join(text.split())
        return text

    def _ocr_move_pp(self, gray, crop_x, crop_y, crop_w, crop_h):
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        crop_gray = cv2.resize(crop_gray, (crop_w*10, crop_h*10))
        # 对图片进行二值化处理
        _, thresh1 = cv2.threshold(
            crop_gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

        # 使用Tesseract进行文字识别
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        text = pytesseract.image_to_string(closing, config=custom_config)
        text = "".join(text.split())
        num = int(text) if text.isdigit() else 0
        return num
# 判断战斗操作
# 识别 战斗、宝可梦、逃走 按钮 -> A
    # 识别 极巨化图标 左 -> A
    # 选择技能 优先度次序 1、PP数量大于0 2、技能下方小字 效果绝佳/有效果/效果不好/没有效果 3、从上到下
# 识别 呐喊（玩家控制宝可梦倒下） -> A -> ?
# 识别 右下角捕捉/不捕捉按钮 战斗成功
# 识别 ？ 战斗失败

    # def hatch_step_0(self):
    #     self.script.macro_text_run(
    #         "B:0.05\n0.05", loop=-1, timeout=2.5, block=True)
    #     self.time_sleep(2.5)
    #     self._process_step_index += 1

    # def hatch_step_1(self):
    #     self.script.macro_run("recognition.pokemon.sv.eggs.hatching_run",
    #                           120, {}, False, None)
    #     self._process_step_index += 1

    # def hatch_step_2(self):
    #     image = self.script.current_frame
    #     ret = HatchMatch().hatched_tag_check(image)
    #     if ret:
    #         self.script.macro_stop(True)
    #         self._process_step_index += 1
    #         return
    #     ret = CombatMatch().combat_check(image)
    #     if ret:
    #         self._status = SubStepRunningStatus.Interrupted
    #         self.script.send_log("{}函数返回状态为{}，检测到遭遇战斗".format(
    #             "hatch_step_2", self._status.name))
    #         return
    #     if not self.script.macro_running:
    #         self._status = SubStepRunningStatus.Failed
    #         return

    # def hatch_step_3(self):
    #     self.script.macro_text_run(
    #         "A:0.01->0.005->A:0.05\n0.1", loop=5 * 17, block=True)
    #     self._hatched_eggs += 1
    #     if self._hatched_eggs < self._eggs:
    #         self._process_step_index = 1
    #         return
    #     self._status = SubStepRunningStatus.OK
