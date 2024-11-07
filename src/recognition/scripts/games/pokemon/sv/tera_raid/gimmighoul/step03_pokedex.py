
from enum import Enum
import time

import cv2
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.games.pokemon.sv.common.image_match.map_N_match import MapNIconMatch


class SVPokedexShinyMatchResult(Enum):
    NotShiny = 0
    Shiny = 1


class SVGimmighoulPokedex(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 30) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._begin_time = None
        self._end_time = None
        self._result = SVPokedexShinyMatchResult.NotShiny
        self._pokedex_shiny_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/sv/raid/pokedex_shiny_icon.jpg", cv2.IMREAD_GRAYSCALE)

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
    def result(self) -> SVPokedexShinyMatchResult:
        return self._result

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
            self._process_step_3,
        ]

    def _process_step_0(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        is_match = MapNIconMatch().match_map_N_icon_template(gray_frame)
        if is_match:
            self._process_step_index += 1

    def _process_step_1(self):
        self.script.macro_text_run("Y:0.1->0.05", loop=4, block=True)
        self.time_sleep(2.5)
        self.script.macro_text_run(
            "X:0.1->0.4->BOTTOM:0.1->0.4->A:0.1->2", block=True)
        self.script.macro_text_run(
            "BOTTOM:0.1->0.6->BOTTOM:0.1->0.6->A:0.1->1->A:0.1", block=True)
        self.time_sleep(2)
        self._process_step_index += 1

    def _process_step_2(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        is_match = self._match_pokedex_shiny_icon_template(gray_frame)
        if is_match:
            self._result = SVPokedexShinyMatchResult.Shiny
            self._status = SubStepRunningStatus.OK
            return
        self._process_step_index += 1

    def _process_step_3(self):
        self.script.macro_text_run("B:0.1->0.4", loop=5, block=True)
        self.time_sleep(0.5)
        self._process_step_index += 1

    def _match_pokedex_shiny_icon_template(self, gray, threshold=0.8) -> bool:
        rect = (180, 105, 20, 30)
        crop_gray = gray[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]]
        res = cv2.matchTemplate(
            crop_gray, self._pokedex_shiny_icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
