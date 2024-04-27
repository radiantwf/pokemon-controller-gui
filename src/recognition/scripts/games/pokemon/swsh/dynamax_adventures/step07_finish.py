from enum import Enum
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2

from recognition.scripts.games.pokemon.swsh.common.image_match.checkbox_match import ChatBoxMatch
from recognition.scripts.games.pokemon.swsh.common.image_match.pokemon_detail_shiny_match import PokemonDetailShinyMatch


class SWSHDAFinish(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 30) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._check_counter = 0
        self._get_rewards_label_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/get_rewards_label.png")
        self._get_rewards_label_template = cv2.cvtColor(
            self._get_rewards_label_template, cv2.COLOR_BGR2GRAY)

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
            self._process_steps_1,
            self._process_steps_2,
        ]

    def _process_steps_0(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if not self._match_get_rewards_page(gray_frame):
            self.time_sleep(0.5)
            return
        self._process_step_index += 1

    def _process_steps_1(self):
        self.script.macro_text_run("A:0.1->2.5->B:0.1->0.3->A:0.1", block=True)
        self.time_sleep(0.5)
        self._process_step_index += 1

    def _match_get_rewards_page(self, gray, threshold=0.9):
        crop_x, crop_y, crop_w, crop_h = 435, 25, 525, 75
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._get_rewards_label_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
    
    def _process_steps_2(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if ChatBoxMatch().match_next_arrow(gray=gray_frame, threshold=0.9):
            self._process_step_index += 1
            return
        self.script.macro_text_run("A:0.1", block=True)
        self.time_sleep(0.4)