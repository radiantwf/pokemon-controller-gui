from enum import Enum
import time

import cv2
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus


class SVMenuItems(Enum):
    Box = 2
    Panic = 3


class SVEnterMenuItem(BaseSubStep):
    def __init__(self, script: BaseScript, menu_item: SVMenuItems = SVMenuItems.Box, timeout: float = 8) -> None:
        super().__init__(script, timeout)
        self._item_y = 0
        if menu_item == SVMenuItems.Box:
            self._item_y = 160
        elif menu_item == SVMenuItems.Panic:
            self._item_y = 200
        else:
            raise ValueError("menu_item must be an instance of SVMenuItems")
        self._status = None
        self._process_step_index = 0
        self._menu_arrow_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/menu_arrow.jpg")
        self._menu_arrow_template = cv2.cvtColor(
            self._menu_arrow_template, cv2.COLOR_BGR2GRAY)
        self._jump_next_frame = False
        self._open_menu_ts = 0

    def _process(self) -> SubStepRunningStatus:
        self._status = self.running_status
        if self._process_step_index >= 0:
            if self._process_step_index >= len(self.process_steps):
                return SubStepRunningStatus.OK
            elif self._status == SubStepRunningStatus.Running:
                if self._jump_next_frame:
                    self._jump_next_frame = False
                    return self._status
                self.process_steps[self._process_step_index]()
                return self._status
            else:
                return self._status
        else:
            self._process_step_index = 0
            return self._process()

    @property
    def process_steps(self):
        return [
            self.step_0,
            self.step_1,
            self.step_2,
        ]

    def step_0(self):
        image = self.script.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._menu_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val < 0.5:
            self._status = SubStepRunningStatus.Failed
            return

        # 包包 0.9837725162506104 (648, 121)
        # 盒子 0.9873440265655518 (649, 161)
        # 野餐 0.9854351282119751 (648, 201)
        # 宝可入口站 0.9781053066253662 (648, 241)
        # 设置 0.9854401350021362 (648, 281)
        # 记录 0.9784520864486694 (648, 321)
        # 付费新增内容 0.9627913236618042 (649, 419)

        # 宝可梦1 0.9802355170249939 (23, 91)
        # 宝可梦2 0.9705981016159058 (23, 154)
        # 宝可梦3 0.9855178594589233 (23, 217)
        # 宝可梦4 0.9850992560386658 (23, 280)
        # 宝可梦5 0.9853918552398682 (23, 343)
        # 宝可梦6 0.9780521988868713 (23, 406)
        # 坐骑 0.9853339195251465 (23, 491)

        if p[0] < 600:
            self.script.macro_text_run("Right", block=True)
            self._jump_next_frame = True
            time.sleep(0.5)
            return
        if p[1] < self._item_y - 10:
            self.script.macro_text_run("Bottom", block=True)
            self._jump_next_frame = True
            time.sleep(0.1)
            return
        if p[1] > self._item_y + 10:
            self.script.macro_text_run("Top", block=True)
            self._jump_next_frame = True
            time.sleep(0.1)
            return
        self._process_step_index += 1

    def step_1(self):
        self.script.macro_text_run("A", block=True)
        time.sleep(0.5)
        self._jump_next_frame = True
        self._process_step_index += 1

    def step_2(self):
        image = self.script.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._menu_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val >= 0.5 and p[1] >= self._item_y - 10 and p[1] <= self._item_y:
            self._process_step_index -= 1
            return
        self._process_step_index += 1
