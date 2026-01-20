import math
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2
import time


class SWSHDAChoosePath(BaseSubStep):
    def __init__(self, script: BaseScript, leave_event: bool = True, enter_event: bool = True, battle_index: int = 0, path: int = 0, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._battle_index = battle_index
        self._path = int(path)
        self._leave_event = leave_event
        self._enter_event = enter_event
        self._choose_path_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/choose_path.png")
        self._choose_path_template = cv2.cvtColor(
            self._choose_path_template, cv2.COLOR_BGR2GRAY)
        self._process_step_2_start_monotonic = 0

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
            self.process_steps_0,
            self.process_steps_1,
            self.process_steps_2,
        ]

    def process_steps_0(self):
        if self._battle_index >= 3:
            self.script.macro_text_run(
                f"{'A' if self._leave_event else 'B'}:0.1->0.4", block=True, loop=28)
            self._process_step_index += 1
            self.time_sleep(0.5)
            self._status = SubStepRunningStatus.OK
            return
        self._process_step_index += 1

    def process_steps_1(self):
        if self._process_step_2_start_monotonic == 0:
            self._process_step_2_start_monotonic = time.monotonic()
            self._check_times = 0
        if time.monotonic() - self._process_step_2_start_monotonic > 30:
            self._process_step_2_start_monotonic = 0
            self._status = SubStepRunningStatus.OK
            return
        current_frame_960x480 = self.script.current_frame_960x480
        gray_frame = cv2.cvtColor(current_frame_960x480, cv2.COLOR_BGR2GRAY)
        if not self._match_choose_path(gray_frame):
            if self._battle_index > 0:
                if self._check_times >= 2:
                    self.script.macro_text_run(
                        f"{'A' if self._enter_event else 'B'}:0.1", block=True)
                    self._check_times = 0
                    self.time_sleep(0.3)
                else:
                    self._check_times += 1
                    self.time_sleep(0.2)
            else:
                self.time_sleep(0.5)
            return
        else:
            self._process_step_index += 1

    def process_steps_2(self):
        if self._path < 0:
            self.script.macro_text_run("LEFT:0.1->0.3", block=True,loop=math.fabs(self._path))
        elif self._path > 0:
            self.script.macro_text_run("RIGHT:0.1->0.3", block=True,loop=self._path)
        self.script.macro_text_run(f"A:0.1->0.4", block=True)
        self.script.macro_text_run(
            f"{'A' if self._leave_event else 'B'}:0.1->0.4", block=True, loop=28)
        self.time_sleep(0.5)
        self._process_step_index += 1

    def _match_choose_path(self, gray) -> bool:
        crop_x, crop_y, crop_w, crop_h = 232, 432, 476, 72
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._choose_path_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            return True
