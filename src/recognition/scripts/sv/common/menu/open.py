from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.menu_match import MenuCursorMatch


class SVOpenMenu(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 8) -> None:
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
            self.step_0,
            self.step_1,
            self.step_2,
        ]

    def step_0(self):
        self.script.macro_text_run(
            "B:0.05\n0.05", loop=-1, timeout=2.5, block=True)
        self.time_sleep(1.5)
        self.script.macro_text_run(
            "L:0.05\n0.05", loop=1, block=True)
        self._process_step_index += 1

    def step_1(self):
        self.script.macro_text_run("X", block=True)
        self.time_sleep(0.5)
        self._process_step_index += 1

    def step_2(self):
        image = self.script.current_frame
        ret = MenuCursorMatch().match(image, 0.5)
        if ret is None:
            self._process_step_index = 0
            return
        self.time_sleep(0.5)
        self._process_step_index += 1
