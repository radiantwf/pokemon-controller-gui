from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.sv.eggs_hatch.box_opt.function import move_cursor


class SVBoxMoveShinyPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 20) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None

    def _process(self) -> SubStepRunningStatus:
        self._status = self.running_status
        if self._process_step_index >= 0:
            if self._process_step_index >= len(self.process_steps):
                return SubStepRunningStatus.OK
            elif self._status == SubStepRunningStatus.Running:
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
            self.move_step_0,
            self.move_step_1,
            self.move_step_2,
        ]

    def move_step_0(self):
        image = self.script.current_frame
        box, current_cursor = BoxMatch().match(image)
        if box[0][self._target_shiny_pokemon_index] == 0:
            self._status = SubStepRunningStatus.OK
            return
        elif box[0][self._target_shiny_pokemon_index] != 1:
            self._status = SubStepRunningStatus.Failed
            return
        if current_cursor is None:
            self._status = SubStepRunningStatus.Failed
            return

        target_shiny_pokemon: tuple[int, int] = (0, 1)
        if current_cursor[0] == target_shiny_pokemon[0] and current_cursor[1] == target_shiny_pokemon[1]:
            self._process_step_index += 1
            return
        move_cursor(self,
            current_cursor, target_shiny_pokemon)
        self.time_sleep(0.5)

    def move_step_1(self):
        image = self.script.current_frame
        ret = BoxMatch().shiny_tag_check(image)
        if ret:
            self._status = SubStepRunningStatus.Failed
            self.script.send_log("{}函数返回状态为{}".format("move_step_1",SubStepRunningStatus.Failed))
            return
        self._process_step_index += 1

    def move_step_2(self):
        self._move_target: tuple[int, int] = (-1, -1)
        image = self.script.current_frame
        box, _ = BoxMatch().match(image)
        for x in range(0, len(box)):
            for y in range(0, len(box[x])):
                if box[x][y] == 0:
                    self._move_target = (x, y)
                    break
        if self._move_target[0] == -1 or self._move_target[1] == -1:
            self.script.send_log("{}函数返回状态为{}".format("move_step_2",SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return
        current_cursor = (0, 1)
        self.script.macro_text_run("Y:0.05", block=True)

        move_cursor(self,
            current_cursor, self._move_target)
        self.time_sleep(0.5)
        self._process_step_index += 1

    def move_step_3(self):
        image = self.script.current_frame
        current_cursor = BoxMatch().match_arrow(image)
        if current_cursor is None:
            self.script.send_log("{}函数返回状态为{}".format("move_step_3",SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return
        if current_cursor[0] == self._move_target[0] and current_cursor[1] == self._move_target[1]:
            self._process_step_index += 1
            return
        move_cursor(self,
                    current_cursor, self._move_target)
        self.time_sleep(0.5)

    def move_step_4(self):
        self.script.macro_text_run("A:0.05", block=True)
        self.time_sleep(0.5)
        self._process_step_index = 0
