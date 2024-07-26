import multiprocessing
import time
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
from recognition.scripts.parameter_struct import ScriptParameter

DEBUG = False


class SwshBattleShiny(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict() = None):
        super().__init__(SwshBattleShiny.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, SwshBattleShiny.script_paras())
        self._prepare_steps = self.init_prepare_steps()
        self._prepare_step_index = -1
        self._cycle_steps = self.init_cycle_steps()
        self._cycle_step_index = -1
        self._template = cv2.imread(
            "resources/img/recognition/pokemon/swsh/battle_shiny.png")
        self._template = cv2.cvtColor(self._template, cv2.COLOR_BGR2GRAY)
        self._template_p = (
            860, 432, self._template.shape[1], self._template.shape[0])
        self.set_paras(paras)
        self._durations = self.get_para("durations")
        self._secondary = self.get_para("secondary")
        self._span = self.get_para("span")

    @staticmethod
    def script_name() -> str:
        return "宝可梦剑盾刷定点闪"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["secondary"] = ScriptParameter(
            "secondary", bool, False, "副设备")
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["span"] = ScriptParameter(
            "span", float, 1.1, "对方精灵登场框消失与己方精灵登场框出现间隔时间（秒）\n 雷吉神庙建议1.1秒，雷吉奇卡斯建议2.45秒")
        return paras

    def _check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False

    def process_frame(self):
        if self._check_durations():
            return
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0 and self._prepare_step_index < len(self._prepare_steps):
                self._prepare_steps[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Cycle:
            if self.current_frame_count == 1:
                self._cycle_init()
            if self._cycle_step_index >= 0 and self._cycle_step_index < len(self._cycle_steps):
                self._cycle_steps[self._cycle_step_index]()
            else:
                self.set_cycle_continue()
                self._cycle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCycle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self.send_log("开始运行宝可梦剑盾定点闪图像识别检测脚本")

    def on_cycle(self):
        if self.cycle_times > 0 and self.cycle_times % 10 == 0:
            run_time_span = self.run_time_span
            self.send_log("闪光检测中，已经运行{}次，耗时{}小时{}分{}秒".format(self.cycle_times, int(
                run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format('宝可梦剑盾定点闪图像识别检测脚本', self.cycle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    def init_prepare_steps(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self.set_cycle_begin()
        self._cycle_step_index = 0

    def init_cycle_steps(self):
        return [
            self.cycle_step_0,
            self.cycle_step_1,
            self.cycle_step_2,
            self.cycle_step_3,
        ]

    def _cycle_init(self):
        self._cycle_step_2_start_time_monotonic = 0
        self._cycle_step_2_time_monotonic_check_1_temp = 0
        self._cycle_step_2_time_monotonic_check_1 = 0
        self._cycle_step_2_frame_count_check_1 = 0
        pass

    def cycle_step_0(self):
        if self.current_frame_count == 1:
            self.macro_run("recognition.pokemon.swsh.common.restart_game",
                           1, {"secondary": str(self._secondary)}, True, None)
            self._cycle_step_index += 1
        else:
            self.macro_stop()
            self.set_cycle_continue()
            self._cycle_step_index = 0

    def cycle_step_1(self):
        self.macro_run("common.press_button_a", -1, {}, False, None)
        self._cycle_step_index += 1

    def cycle_step_2(self):
        if self._cycle_step_2_start_time_monotonic == 0:
            self._cycle_step_2_start_time_monotonic = time.monotonic()

        if self.current_cycle_time_span > 80:
            self._cycle_step_index += 1
            return

        image = self.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_x, crop_y, crop_w, crop_h = self._template_p[
            0], self._template_p[1], self._template_p[2], self._template_p[3]
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(
            crop_gray, self._template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val > 0.92:
            if self._cycle_step_2_time_monotonic_check_1 == 0:
                if self._cycle_step_2_time_monotonic_check_1_temp == 0:
                    self.macro_stop(block=False)
                self._cycle_step_2_time_monotonic_check_1_temp = time.monotonic()
            else:
                span = time.monotonic() - self._cycle_step_2_time_monotonic_check_1
                if DEBUG:
                    self.send_log("time_span:{:.2f}, frames_span:{}".format(
                        span, self.current_frame_count - self._cycle_step_2_frame_count_check_1))
                if span < self._span:
                    self._cycle_step_index += 1
                    return
                elif span < self._span + 3:
                    run_time_span = self.run_time_span
                    if self.current_frame_count - self._cycle_step_2_frame_count_check_1 <= 4:
                        self._cycle_step_index += 1
                        return
                    self.macro_stop(block=False)
                    self.send_log("检测到闪光，请人工核查，已运行{}次，耗时{}小时{}分{}秒".format(self.cycle_times, int(
                        run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
                    self._finished_process()
        elif self._cycle_step_2_time_monotonic_check_1_temp > 0 and self._cycle_step_2_time_monotonic_check_1 == 0:
            self._cycle_step_2_time_monotonic_check_1 = self._cycle_step_2_time_monotonic_check_1_temp
            self._cycle_step_2_frame_count_check_1 = self.current_frame_count

    def cycle_step_3(self):
        self.macro_stop()
        self.set_cycle_continue()
        # self.send_log("未检测到闪光,帧数:{},时长{}".format(self.current_frame_count,self.current_cycle_time_span))
        self._cycle_step_index = 0

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(SwshBattleShiny.script_name(), self.cycle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()
