from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus


class SVDASwitchPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, eggs: int, timeout: float = 600) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0

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
            # self.hatch_step_0,
            # self.hatch_step_1,
            # self.hatch_step_2,
            # self.hatch_step_3,
        ]