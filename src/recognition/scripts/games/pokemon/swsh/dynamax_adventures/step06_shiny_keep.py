from enum import Enum
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2

from recognition.scripts.games.pokemon.swsh.common.image_match.pokemon_detail_shiny_match import PokemonDetailShinyMatch


class SWSHDAShinyKeepResult(Enum):
    NotKept = 0
    Kept = 1
    KeptLegendary = 2


class SWSHDAShinyKeep(BaseSubStep):
    def __init__(self, script: BaseScript, legendary_caught: bool, only_keep_legendary: bool = False, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._legendary_caught = legendary_caught
        self._only_keep_legendary = only_keep_legendary
        self._process_step_index = 0
        self._check_counter = 0
        self._kept_result = SWSHDAShinyKeepResult.NotKept
        self._keep_pokemon_label_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/keep_pokemon_label.png")
        self._keep_pokemon_label_template = cv2.cvtColor(
            self._keep_pokemon_label_template, cv2.COLOR_BGR2GRAY)

    @property
    def kept_result(self) -> SWSHDAShinyKeepResult:
        return self._kept_result

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
        ]

    def _process_steps_0(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if not self._match_keep_pokemon_page(gray_frame):
            self.time_sleep(0.5)
            return
        if (not self._legendary_caught) and self._only_keep_legendary:
            self._not_keep()
            self._status == SubStepRunningStatus.OK
            return
        self.script.macro_text_run(
            "TOP:0.1->0.4->A:0.1->0.6->BOTTOM:0.1->0.6->A:0.1", block=True)
        self.time_sleep(2)
        self._check_counter = 0
        self._process_step_index += 1

    def _process_steps_1(self):
        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_shiny(gray_frame):
            self._quit_pokemon_detail()
            self._keep()
            self._process_step_index += 1
            return
        if self._only_keep_legendary:
            self._quit_pokemon_detail()
            self._not_keep()
            self._process_step_index += 1
            return
        else:
            self._check_counter += 1
            if self._check_counter < 4:
                self.script.macro_text_run("TOP:0.1", block=True)
                self.time_sleep(0.5)
                return
            else:
                self._quit_pokemon_detail()
                self._not_keep()
                self._process_step_index += 1
                return

    def _quit_pokemon_detail(self):
        self.script.macro_text_run("B:0.1", block=True)
        self.time_sleep(2)

    def _keep(self):
        if self._check_counter == 0 and self._legendary_caught:
            self._kept_result = SWSHDAShinyKeepResult.KeptLegendary
        else:
            self.script.macro_text_run("A:0.05->0.5->A:0.05->0.5->A:0.05->0.2->A:0.05->0.2->A:0.05", block=True)
            self.time_sleep(0.5)
            self._kept_result = SWSHDAShinyKeepResult.Kept

    def _not_keep(self):
        self.script.macro_text_run(
            "B:0.1->0.6->A:0.1->0.4->A:0.1->0.4->A:0.1", block=True)
        self.time_sleep(1)

    def _match_keep_pokemon_page(self, gray, threshold=0.9) -> bool:
        crop_x, crop_y, crop_w, crop_h = 435, 25, 525, 75
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._keep_pokemon_label_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        return max_val >= threshold
    
    def _match_shiny(self, gray) -> bool:
        return PokemonDetailShinyMatch().match_shiny(gray = gray, threshold=0.9)