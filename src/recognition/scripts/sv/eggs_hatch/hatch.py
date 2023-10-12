from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.sv.eggs_hatch.box_opt.function import move_cursor


class SVHatchPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, eggs: int, timeout: float = 20) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None
        self._eggs = eggs
        self._hatched_eggs = 0

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
            self.hatch_step_0,
            self.hatch_step_1,
            self.hatch_step_2,
            self.hatch_step_3,
            self.hatch_step_4,
        ]

    def hatch_step_0(self):
        self.script.macro_run("recognition.pokemon.sv.eggs.hatching_run",
                              -1, {}, False, None)
        self._process_step_index += 1

    def hatch_step_1(self):
        self._process_step_index += 1

    def hatch_step_2(self):
        self.script.macro_text_run("A:0.1\n0.1", 5 * 30, block=False)
        self._hatched_eggs += 1
        if self._hatched_eggs < self._eggs:
            self._process_step_index += 1
        else:
            self._status = SubStepRunningStatus.OK

    def hatch_step_3(self):
        self._process_step_index += 1

    def hatch_step_4(self):
        self._process_step_index += 1
