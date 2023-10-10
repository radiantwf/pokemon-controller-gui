from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.box_match import BoxMatch


class SVBoxReleasePokemon(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 0) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None
        self.target_release_index = 1

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
            self.release_step_0,
            self.release_step_1,
            self.release_step_2,
        ]

    def release_step_0(self):
        image = self.script.current_frame
        box, current_cursor = BoxMatch().match(image)
        print(box, current_cursor)
        if box[0][self.target_release_index] == 0:
            self._status = SubStepRunningStatus.OK
            return
        if current_cursor is None:
            self._status = SubStepRunningStatus.Failed
            return
        x = 0 - current_cursor[0]
        y = self.target_release_index - current_cursor[1]
        if x == 0 and y == 0:
            self._process_step_index += 1
            return
        while x != 0 or y != 0:
            if x > 0:
                self.script.macro_text_run("RIGHT:0.05", block=True)
                x -= 1
            elif x < 0:
                self.script.macro_text_run("LEFT:0.05", block=True)
                x += 1
            elif y > 0:
                self.script.macro_text_run("BOTTOM:0.05", block=True)
                y -= 1
            elif y < 0:
                self.script.macro_text_run("TOP:0.05", block=True)
                y += 1
        self.time_sleep(0.5)

    def release_step_1(self):
        image = self.script.current_frame
        ret = BoxMatch().shiny_tag_check(image)
        if ret:
            self.target_release_index = self.target_release_index + 1
            self._process_step_index = 0
            return
        self.script.macro_text_run(
            "A:0.05\n0.3\nTOP:0.05\n0.1\nTOP:0.05", block=True)
        self.time_sleep(0.01)
        self._process_step_index += 1

    def release_step_2(self):
        image = self.script.current_frame
        ret = BoxMatch().release_tag_check(image)
        if ret:
            self.script.macro_text_run(
                "A:0.05\n0.6\nTOP:0.05\n0.1\nA:0.05\n1.6\nA:0.05\n", block=True)
            self.time_sleep(1)
            self._process_step_index = 0
        else:
            self._status = SubStepRunningStatus.Failed
            return
