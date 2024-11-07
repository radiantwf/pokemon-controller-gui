
import time

import cv2
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus


class SVGimmighoulBattle(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 60) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._begin_time = None
        self._end_time = None
        self._combat_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/raid/combat_icon.jpg", cv2.IMREAD_GRAYSCALE)

    def _process(self) -> SubStepRunningStatus:
        if self._begin_time is None:
            self._begin_time = time.monotonic()
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
    def run_time_span(self):
        if self._begin_time is None:
            return 0
        if self._end_time is None:
            return time.monotonic() - self._begin_time
        return self._end_time - self._begin_time

    @property
    def _process_steps(self):
        return [
            self._process_step_0,
            self._process_step_1,
            self._process_step_2,
        ]

    def _process_step_0(self):
        self.script.macro_text_run(
            "BOTTOM:0.1->0.4->A:0.05", block=True)
        self.time_sleep(5)
        self._process_step_index += 1

    def _process_step_1(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        is_match = self._match_combat_icon_template(gray_frame)
        if is_match:
            self._process_step_index += 1

    def _process_step_2(self):
        self.script.macro_text_run(
            "TOP:0.1->0.3->A:0.05->0.7->A:0.05", block=True)
        self.time_sleep(10)
        self._process_step_index += 1


    def _match_combat_icon_template(self, gray, threshold=0.8) -> bool:
        rect = (750, 390, 35, 130)
        crop_gray = gray[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        res = cv2.matchTemplate(
            crop_gray, self._combat_icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
