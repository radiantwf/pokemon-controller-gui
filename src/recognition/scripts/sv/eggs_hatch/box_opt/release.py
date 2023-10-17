import time
import cv2
from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.sv.eggs_hatch.box_opt.function import move_cursor


class SVBoxReleasePokemon(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 0) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None
        self.target_release_pokemon_index = 1

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
        # print(box)
        if box[0][self.target_release_pokemon_index] == 0:
            self._status = SubStepRunningStatus.OK
            return
        if current_cursor is None:
            self.script.send_log("{}函数返回状态为{}".format(
                "release_step_0", SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return

        target: tuple[int, int] = (0, self.target_release_pokemon_index)
        if current_cursor[0] == target[0] and current_cursor[1] == target[1]:
            self._process_step_index += 1
            return
        move_cursor(self,
                    current_cursor, target)
        self.time_sleep(0.5)

    def release_step_1(self):
        image = self.script.current_frame
        box, _ = BoxMatch().match(image)
        ret = BoxMatch().sv_tag_check(image)
        if ret and box[0][self.target_release_pokemon_index] == 1:
            self._status = SubStepRunningStatus.Interrupted
            self.script.send_log("{}函数返回状态为{}，宝可梦朱紫标志检测错误，请尝试手动按+键切换宝可梦显示模式，再次运行脚本，或确认同行宝可梦是否是有朱紫标志。".format(
                "release_step_1", self._status.name))
            return
        ret = BoxMatch().shiny_tag_check(image)
        if box[0][self.target_release_pokemon_index] == 9 or ret:
            self.target_release_pokemon_index = self.target_release_pokemon_index + 1
            if self.target_release_pokemon_index > 5:
                self._status = SubStepRunningStatus.OK
                return
            self._process_step_index = 0
            return
        self.script.macro_text_run(
            "A:0.01->0.005->A:0.05\n0.3\nTOP:0.05\n0.1\nTOP:0.05", block=True)
        self.time_sleep(0.05)
        self._process_step_index += 1

    def release_step_2(self):
        image = self.script.current_frame
        ret = BoxMatch().release_tag_check(image)
        if ret:
            self.script.macro_text_run(
                "A:0.01->0.005->A:0.05\n0.6\nTOP:0.05\n0.1\nA:0.01->0.005->A:0.05\n1.6\nA:0.01->0.005->A:0.05\n", block=True)
            self.time_sleep(1)
            self._process_step_index = 0
        else:
            self.script.send_log("{}函数返回状态为{}".format(
                "release_step_2", SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return
