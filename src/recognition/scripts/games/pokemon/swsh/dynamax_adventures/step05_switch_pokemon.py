from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
import cv2


class SWSHDASwitchPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, battle_index: int = 0, switch: bool = True, timeout: float = -1) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._battle_index = battle_index
        self._switch_pokemon = switch
        self._switch_pokemon_template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/dynamax_adventures/switch_pokemon/switch_pokemon.png")
        self._switch_pokemon_template = cv2.cvtColor(
            self._switch_pokemon_template, cv2.COLOR_BGR2GRAY)

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
        ]

    def _process_steps_0(self):
        if self._battle_index >= 3:
            self._process_step_index += 1
            return

        current_frame = self.script.current_frame
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if self._match_switch_pokemon(gray_frame):
            if self._switch_pokemon:
                self.script.macro_text_run("A:0.1", block=True)
            else:
                self.script.macro_text_run(
                    "BOTTOM:0.1->0.4->A:0.1", block=True)
            self.time_sleep(3)
            self._process_step_index += 1
        else:
            self.time_sleep(0.5)

    def _match_switch_pokemon(self, gray) -> bool:
        crop_x, crop_y, crop_w, crop_h = 336, 172, 76, 195
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        res = cv2.matchTemplate(
            crop_gray, self._switch_pokemon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > 0.9:
            return True
