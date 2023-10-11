from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.sv.eggs_hatch.box_opt.release import SVBoxReleasePokemon


class SVBoxOptPokemon(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 0) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None
        self._sv_box_release = SVBoxReleasePokemon(self.script)

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
            self.release,
            self.step_1,
            self.step_2,
        ]

    def release(self):
        status = self._sv_box_release.run()
        if status == SubStepRunningStatus.Running:
            return
        elif status == SubStepRunningStatus.OK:
            self._process_step_index += 1
            return
        else:
            self.script.send_log("{}函数返回状态为{}".format("release", status.name))
            self._status = SubStepRunningStatus.Failed
            return

    def step_1(self):
        self._process_step_index += 1

    def step_2(self):
        self._process_step_index += 1
