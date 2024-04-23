from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus
from recognition.scripts.games.pokemon.sv.common.image_match.box_match import BoxMatch
from recognition.scripts.games.pokemon.sv.eggs_hatch.box_opt.function import move_cursor

# 定义全局变量
global_page_turns_count = 0


def reset_global_page_turns_count():
    global global_page_turns_count
    global_page_turns_count = 0


class SVBoxMoveEggs(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = 20) -> None:
        super().__init__(script, timeout)
        self._process_step_index = 0
        self._status = None

        self._target_col = -1

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
            self.move_step_0,
            self.move_step_1,
            self.move_step_2,
            self.move_step_3,
            self.move_step_4,
            self.move_step_5,
            self.move_step_6,
            self.move_step_7,
        ]

    def move_step_0(self):
        image = self.script.current_frame
        box, current_cursor = BoxMatch().match(image)
        if current_cursor is None:
            self._status = SubStepRunningStatus.Failed
            return
        for x in range(len(box)):
            if x == 0:
                for y in range(len(box[x])):
                    if box[x][y] == 9:
                        self._status = SubStepRunningStatus.OK
                        return
            for y in range(len(box[x])):
                if box[x][y] == 9:
                    self._target_col = x
                    break
            if self._target_col > 0:
                break

        if self._target_col > 0:
            self._process_step_index += 1
        else:
            global global_page_turns_count
            global_page_turns_count += 1
            if global_page_turns_count >= 36:
                self._status = SubStepRunningStatus.Finished
                return
            self.script.macro_text_run("R:0.05", block=True)
            self.script.send_log(f"翻页{global_page_turns_count}次")
            self.time_sleep(0.8)
        return

    def move_step_1(self):
        move_target = (self._target_col, 0)
        image = self.script.current_frame
        current_cursor = BoxMatch().match_arrow(image)
        if current_cursor is None:
            self.script.send_log("{}函数返回状态为{}".format(
                "move_step_1", SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return
        if current_cursor[0] == move_target[0] and current_cursor[1] == move_target[1]:
            self._process_step_index += 1
            return
        move_cursor(self,
                    current_cursor, move_target)
        self.time_sleep(0.1)

    def move_step_2(self):
        self.script.macro_text_run("Minus:0.05", block=True)
        self.time_sleep(0.2)
        self._process_step_index += 1

    def move_step_3(self):
        move_target = (self._target_col, 4)
        image = self.script.current_frame
        current_cursor = BoxMatch().match_arrow(image)
        if current_cursor is None:
            self.script.send_log("{}函数返回状态为{}".format(
                "move_step_3", SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return
        if current_cursor[0] == move_target[0] and current_cursor[1] == move_target[1]:
            self._process_step_index += 1
            return
        move_cursor(self,
                    current_cursor, move_target)
        self.time_sleep(0.1)

    def move_step_4(self):
        self.script.macro_text_run("A:0.01->0.005->A:0.05", block=True)
        self.time_sleep(0.2)
        self._process_step_index += 1

    def move_step_5(self):
        self._process_step_index += 1

    def move_step_6(self):
        move_target = (0, 1)
        image = self.script.current_frame
        current_cursor = BoxMatch().match_arrow(image)
        if current_cursor is None:
            self.script.send_log("{}函数返回状态为{}".format(
                "move_step_6", SubStepRunningStatus.Failed))
            self._status = SubStepRunningStatus.Failed
            return
        if current_cursor[0] == move_target[0] and current_cursor[1] == move_target[1]:
            self._process_step_index += 1
            return
        move_cursor(self,
                    current_cursor, move_target)
        self.time_sleep(0.1)

    def move_step_7(self):
        self.script.macro_text_run("A:0.01->0.005->A:0.05", block=True)
        self.time_sleep(0.2)
        self._process_step_index += 1
