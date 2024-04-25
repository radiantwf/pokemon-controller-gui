import math
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2


class SWSHDAChoosePath(BaseSubStep):
    def __init__(self, script: BaseScript, battle_index: int = 0, path: int = 0, event: bool = True, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._battle_index = battle_index
        self._path = int(path)
        self._event = event
        self._choose_path_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/choose_path.png")
        self._choose_path_template = cv2.cvtColor(
            self._choose_path_template, cv2.COLOR_BGR2GRAY)

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
        ]

    def process_steps_0(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._battle_index < 3 and self._match_choose_path(gray_frame):
            if self._path < 0:
                self.script.macro_text_run(
                    "{LEFT:0.1->0.3}*"+f"{math.abs(self._path)}\n" + "A:0.1", block=True)
            elif self._path == 0:
                self.script.macro_text_run(f"A:0.1", block=True)
            elif self._path > 0:
                self.script.macro_text_run(
                    "{RIGHT:0.1->0.3}*"+f"{self._path}\n" + "A:0.1", block=True)
        elif self._battle_index >= 3:
            pass
        else:
            self.time_sleep(0.5)
            return
        self.script.macro_text_run(
            f"{'A' if self._event else 'B'}:0.1->0.4", block=True, loop=28)
        self._process_step_index += 1
        self.time_sleep(0.5)

    def _match_choose_path(self, gray) -> bool:
        crop_x, crop_y, crop_w, crop_h = 232, 432, 476, 72
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._choose_path_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            return True
