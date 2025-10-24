from enum import Enum
import multiprocessing
import time
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2


class ZaFossil(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict = None):
        super().__init__(ZaFossil.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, ZaFossil.script_paras())
        self._prepare_step_index = -1
        self._cycle_step_index = -1
        self._jump_next_frame = False
        self._shiny_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/za/shiny-icon.png", cv2.IMREAD_GRAYSCALE)
        self._alpha_icon_template = cv2.imread(
            "resources/img/recognition/pokemon/za/alpha-icon.png", cv2.IMREAD_GRAYSCALE)
        self._check_pokemon_index = -1

        self.set_paras(paras)

        # 获取脚本参数
        self._loop = self.get_para("loop")
        self._durations = self.get_para("durations")
        self._ns1 = self.get_para("ns1") if "ns1" in paras else False

    @staticmethod
    def script_name() -> str:
        return "宝可梦ZA刷闪化石"

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
        self.send_log(f"开始运行{ZaFossil.script_name()}脚本")

    def on_cycle(self):
        run_time_span = self.run_time_span
        log_txt = ""
        log_txt += f"[{ZaFossil.script_name()}] 脚本运行中，耗时{int(run_time_span/3600)}小时{int((run_time_span %
                                                                                         3600) / 60)}分{int(run_time_span % 60)}秒"
        self.send_log(log_txt)
        self._check_pokemon_index = -1

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(ZaFossil.script_name(
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
            self.step_2,
        ]

    def _finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        self.macro_run("common.switch_sleep",
                       loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(ZaFossil.script_name(), self.cycle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()

    def _re_cycle(self):
        pass

    def _cycle_init(self):
        pass

    def step_0(self):
        # 复原30个化石
        self.macro_run("common.press_button_a",
                       loop=-1, paras={}, block=True, timeout=390)
        self.macro_run("common.press_button_b",
                       loop=-1, paras={}, block=True, timeout=3)
        self._cycle_step_index += 1

    def check_shiny_icon(self, image):
        # 检查是否有宝可梦闪光
        crop_x, crop_y, crop_w, crop_h = 813, 61, 16, 16
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._shiny_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val1, _, _ = cv2.minMaxLoc(match)
        if max_val1 >= 0.7:
            return True
        crop_x, crop_y, crop_w, crop_h = 795, 61, 16, 16
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._shiny_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val2, _, _ = cv2.minMaxLoc(match)
        if max_val2 >= 0.7:
            return True
        return False

    def check_alpha_icon(self, image):
        # 检查是否有宝可梦是头目宝可梦
        crop_x, crop_y, crop_w, crop_h = 813, 61, 16, 16
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        match = cv2.matchTemplate(crop_gray, self._alpha_icon_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        if max_val >= 0.7:
            return True
        return False

    def step_1(self):
        if self._check_pokemon_index == -1:
            # 打开盒子
            self.macro_text_run(
                "X:0.1->0.8->A:0.1->0.8", block=True)
            self._jump_next_frame = True
            self._check_pokemon_index += 1
            return
        # 5行，每行6个宝可梦
        image = self.current_frame
        if self.check_shiny_icon(image):
            self.send_log("找到目标闪光宝可梦")
            self._finished_process()
            return
        if self.check_alpha_icon(image):
            pass
        self._check_pokemon_index += 1
        if self._check_pokemon_index == 30:
            self._cycle_step_index += 1
            return
        self.macro_text_run(
            "RIGHT:0.05->0.1", block=True)
        if self._check_pokemon_index % 6 == 0:
            self.macro_text_run(
                "BOTTOM:0.05->0.1", block=True)
        self._jump_next_frame = True

    def step_2(self):
        self.send_log("所有宝可梦检查完毕，目标宝可梦未闪光，重新启动游戏")
        self.macro_run("pokemon.za.common.restart_game",
                       loop=1, paras={"ns1": str(self._ns1)}, block=True, timeout=None)
        self._cycle_step_index += 1
