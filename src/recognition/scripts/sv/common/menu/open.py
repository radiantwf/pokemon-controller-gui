import time

import cv2
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus


class SVOpenMenu(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 6) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._menu_arrow_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/menu_arrow.jpg")
        self._menu_arrow_template = cv2.cvtColor(
            self._menu_arrow_template, cv2.COLOR_BGR2GRAY)
        self._jump_next_frame = False
        self._status = None

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
        self.script.macro_text_run(
            "B:0.05\n0.05", loop=-1, timeout=2.5, block=True)
        time.sleep(0.1)
        self._process_step_index += 1

    def step_1(self):
        self.script.macro_text_run("X", block=True)
        time.sleep(0.5)
        self._jump_next_frame = True
        self._process_step_index += 1

    def step_2(self):
        image = self.script.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(
            gray, self._menu_arrow_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val < 0.5:
            self._process_step_index = 0
            return
        self._process_step_index += 1
