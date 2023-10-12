from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.sv.common.image_match.hatch_match import HatchMatch
from recognition.scripts.sv.eggs_hatch.box_opt.function import move_cursor


class SVHatchPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, eggs: int, timeout: float = 600) -> None:
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
        ]

    def hatch_step_0(self):
        self.script.macro_text_run(
            "B:0.05\n0.05", loop=-1, timeout=2.5, block=True)
        self.time_sleep(2.5)
        self._process_step_index += 1

    def hatch_step_1(self):
        self.script.macro_run("recognition.pokemon.sv.eggs.hatching_run",
                              120, {}, False, None)
        self._process_step_index += 1

    def hatch_step_2(self):
        image = self.script.current_frame
        ret = HatchMatch().hatched_tag_check(image)
        if ret:
            self.script.macro_stop(True)
            self._process_step_index += 1
            return
        if not self.script.macro_running:
            self._status = SubStepRunningStatus.Failed
            return

    def hatch_step_3(self):
        self.script.macro_text_run("A:0.1\n0.1", loop=5 * 20, block=True)
        self._hatched_eggs += 1
        if self._hatched_eggs < self._eggs:
            self._process_step_index = 1
            return
        self._status = SubStepRunningStatus.OK
