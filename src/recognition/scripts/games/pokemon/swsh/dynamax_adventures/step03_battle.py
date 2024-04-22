from recognition.scripts.base.base_script import BaseScript
from recognition.scripts.base.base_sub_step import BaseSubStep, SubStepRunningStatus


class SWSHDABattle(BaseSubStep):
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

# 判断战斗操作
# 识别 战斗、宝可梦、逃走 按钮 -> A
    # 识别 极巨化图标 左 -> A
    # 选择技能 优先度次序 1、PP数量大于0 2、技能下方小字 效果绝佳/有效果/效果不好 3、从上到下
# 识别 呐喊（玩家控制宝可梦倒下） -> A -> ?
# 识别 右下角捕捉/不捕捉按钮 战斗成功
# 识别 ？ 战斗失败



    # def hatch_step_0(self):
    #     self.script.macro_text_run(
    #         "B:0.05\n0.05", loop=-1, timeout=2.5, block=True)
    #     self.time_sleep(2.5)
    #     self._process_step_index += 1

    # def hatch_step_1(self):
    #     self.script.macro_run("recognition.pokemon.sv.eggs.hatching_run",
    #                           120, {}, False, None)
    #     self._process_step_index += 1

    # def hatch_step_2(self):
    #     image = self.script.current_frame
    #     ret = HatchMatch().hatched_tag_check(image)
    #     if ret:
    #         self.script.macro_stop(True)
    #         self._process_step_index += 1
    #         return
    #     ret = CombatMatch().combat_check(image)
    #     if ret:
    #         self._status = SubStepRunningStatus.Interrupted
    #         self.script.send_log("{}函数返回状态为{}，检测到遭遇战斗".format(
    #             "hatch_step_2", self._status.name))
    #         return
    #     if not self.script.macro_running:
    #         self._status = SubStepRunningStatus.Failed
    #         return

    # def hatch_step_3(self):
    #     self.script.macro_text_run(
    #         "A:0.01->0.005->A:0.05\n0.1", loop=5 * 17, block=True)
    #     self._hatched_eggs += 1
    #     if self._hatched_eggs < self._eggs:
    #         self._process_step_index = 1
    #         return
    #     self._status = SubStepRunningStatus.OK
