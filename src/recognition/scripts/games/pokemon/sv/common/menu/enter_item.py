from enum import IntEnum
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.games.pokemon.sv.common.image_match.menu_match import MenuCursorMatch


class SVMenuItems(IntEnum):
    Box = 1
    Panic = 2


class SVEnterMenuItem(BaseSubStep):
    def __init__(self, script: BaseScript, menu_item: SVMenuItems = SVMenuItems.Box, timeout: float = 8) -> None:
        super().__init__(script, timeout)
        if menu_item is not None:
            self._target_item_index = menu_item.value
        else:
            raise ValueError("menu_item must be an instance of SVMenuItems")
        self._status = None
        self._process_step_index = 0
        self._open_menu_ts = 0

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
            self.step_0,
            self.step_1,
            self.step_2,
        ]

    def step_0(self):
        image = self.script.current_frame

        ret = MenuCursorMatch().match(image, 0.5)
        if ret is None:
            self._status = SubStepRunningStatus.Failed
            return
        if len(ret) != 3:
            self._status = SubStepRunningStatus.Failed
            return
        if ret[0] == -1 or ret[1] == -1:
            self._status = SubStepRunningStatus.Failed
            return

        if ret[0] == 0 :
            self.script.macro_text_run("Right", block=True)
            self.time_sleep(0.5)
            return

        if ret[1] < self._target_item_index:
            self.script.macro_text_run("Bottom", block=True)
            self.time_sleep(0.1)
            return
        elif ret[1] > self._target_item_index:
            self.script.macro_text_run("Top", block=True)
            self.time_sleep(0.1)
            return
        self._process_step_index += 1

    def step_1(self):
        self.script.macro_text_run("A", block=True)
        self.time_sleep(0.3)
        self._process_step_index += 1

    def step_2(self):
        image = self.script.current_frame
        ret = MenuCursorMatch().match(image, 0.5)
        if ret is None:
            self.time_sleep(0.3)
            self._process_step_index += 1
        else:
            self._process_step_index -= 1