from enum import Enum
import multiprocessing
import time
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2


class FrlgDeoxys(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(FrlgDeoxys.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, FrlgDeoxys.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False
        self._battle_text_template = cv2.imread(
            "resources/img/recognition/pokemon/frlg/deoxys-battle-text.png", cv2.IMREAD_GRAYSCALE)
        self._check_pokemon_index = -1

        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._ns1 = self.get_para("ns1") if paras and "ns1" in paras else False

    @staticmethod
    def script_name() -> str:
        return "宝可梦-火红叶绿-代欧奇希斯"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["loop"] = ScriptParameter(
            "loop", int, -1, "运行次数")
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["ns1"] = ScriptParameter(
            "ns1", bool, False, "是否使用NS1")
        return paras

    def _check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False

    def _check_cycles(self):
        if self._loop <= 0:
            return False
        if self.cycle_times > self._loop:
            self.send_log("运行次数已到达设定值，脚本停止")
            self._finished_process()
            return True
        return False

    def process_frame(self):
        if self._check_durations():
            return
        if self._check_cycles():
            return

        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self._prepare_step_list):
                    self.set_cycle_begin()
                    self._cycle_step_index = 0
                    return
                self._prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Cycle:
            if self.current_frame_count == 1:
                self._cycle_init()
            if self._jump_next_frame:
                self.clear_frame_queue()
                self._jump_next_frame = False
                return
            if self._cycle_step_index >= 0 and self._cycle_step_index < len(self._cycle_step_list):
                self._cycle_step_list[self._cycle_step_index]()
            else:
                self.macro_stop()
                self.set_cycle_continue()
                self._cycle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCycle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self._check_pokemon_index = -1
        self.send_log(f"开始运行{FrlgDeoxys.script_name()}脚本")

    def on_cycle(self):
        if self.cycle_times > 0 and self.cycle_times % 5 == 0:
            run_time_span = self.run_time_span
            log_txt = ""
            log_txt += f"[{FrlgDeoxys.script_name()}] 脚本运行中，已运行{self.cycle_times}次，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                            3600) / 60)}分{int(run_time_span % 60)}秒"
            self.send_log(log_txt)
        self._check_pokemon_index = -1

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(FrlgDeoxys.script_name(
        ), self.cycle_times, int(run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    @property
    def _prepare_step_list(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self._prepare_step_index += 1

    @property
    def _cycle_step_list(self):
        return [
            self.step_0,
            self.step_1,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(FrlgDeoxys.script_name(), self.cycle_times - 1, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        self._cycle_step_1_start_time_monotonic = 0

    def _cycle_init(self):
        self._cycle_step_1_start_time_monotonic = 0

    def step_0(self):
        self.macro_text_run("X|Y|A|B:0.1\n0.1", loop=1, block=True)
        self.macro_run("common.press_button_a",
                       loop=-1, paras={}, block=True, timeout=20)
        self._jump_next_frame = True
        self._cycle_step_index += 1

    def check_battle_text(self, image):
        crop_x, crop_y, crop_w, crop_h = 240, 806, 865, 70
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._battle_text_template, cv2.TM_CCOEFF_NORMED)
        _, max_val1, _, _ = cv2.minMaxLoc(match)
        if max_val1 >= 0.7:
            return True
        return False

    def step_1(self):
        if self._cycle_step_1_start_time_monotonic == 0:
            self._cycle_step_1_start_time_monotonic = time.monotonic()
        
        current_frame = self.current_frame
        if not self.check_battle_text(current_frame):
            return
        time_span = time.monotonic() - self._cycle_step_1_start_time_monotonic
        self.send_log(f"检测到 进入战斗文本，耗时{time_span:.2f}秒")
        if time_span > 6:
            self.send_log(f"成功检测到闪光代欧奇希斯")
            self._finished_process()
            return
        self._cycle_step_index += 1
        return
