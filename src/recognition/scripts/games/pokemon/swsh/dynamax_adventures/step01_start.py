from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus


class SWSHDAStart(BaseSubStep):
    def __init__(self, script: BaseScript, timeout: float = -1) -> None:
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
            self.start_step_0,
            self.start_step_1,
            self.start_step_2,
            self.start_step_3,
            # self.hatch_step_3,
        ]
    
    def start_step_0(self):
        self._process_step_index += 1

    def start_step_1(self):
        self.script.macro_text_run("A:0.1->0.4->A:0.1->0.4", block=True,loop=7)
        self.time_sleep(2)
        self._process_step_index += 1

    def start_step_2(self):
        self.script.macro_text_run("BOTTOM:0.1->0.4->A:0.1->0.4", block=True)
        self.time_sleep(2)
        self._process_step_index += 1
    def start_step_3(self):
        self.script.macro_text_run("A:0.1", block=True)
        self.time_sleep(21)
        self._process_step_index += 1

# 对话 A
# 非正常退出，没有惩罚 3次A
# 有惩罚  ？

# 现在就出发 A -> 2次A
# 选择挑战对象 A
# 保存进度 A -> 是（A）

# 极巨大冒险界面 发起单人挑战 下 -> A
# 选择宝可梦 A —> 19s 左右