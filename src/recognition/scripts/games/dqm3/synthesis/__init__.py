import math
import multiprocessing
import time
from recognition.scripts.parameter_struct import ScriptParameter
from recognition.scripts.base.base_script import BaseScript, WorkflowEnum
import cv2
import numpy as np
from recognition.scripts.base.base_sub_step import SubStepRunningStatus

class DQM3Synthesis(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue, paras: dict() = None):
        super().__init__(DQM3Synthesis.script_name(), stop_event,
                         frame_queue, controller_input_action_queue, DQM3Synthesis.script_paras())
        self._prepare_step_index = -1
        self._circle_step_index = -1
        self._jump_next_frame = False
        self.set_paras(paras)
        self._durations = self.get_para("durations")
        self._secondary = self.get_para("secondary")
        self._shiny_star_template = cv2.imread("resources/img/recognition/dqm3/synthesis/shiny_star.png")
        self._shiny_star_template = cv2.cvtColor(self._shiny_star_template, cv2.COLOR_BGR2GRAY)
        crop_x, crop_y, crop_w, crop_h = 300, 300, 360, 240
        self._template_crop = (crop_x, crop_y, crop_w, crop_h)


    @staticmethod
    def script_name() -> str:
        return "勇者斗恶龙怪兽篇3配种"

    @staticmethod
    def script_paras() -> dict:
        paras = dict()
        paras["durations"] = ScriptParameter(
            "durations", float, -1, "运行时长（分钟）")
        paras["secondary"] = ScriptParameter(
            "secondary", bool, False, "副设备")
        paras["m1_page"] = ScriptParameter(
            "m1_page", int, 1, "怪兽1所在页面")
        paras["m1_row"] = ScriptParameter(
            "m1_row", int, 1, "怪兽1所在行")
        paras["m1_col"] = ScriptParameter(
            "m1_col", int, 1, "怪兽1所在列")
        paras["m2_page"] = ScriptParameter(
            "m2_page", int, 1, "怪兽2所在页面")
        paras["m2_row"] = ScriptParameter(
            "m2_row", int, 1, "怪兽2所在行")
        paras["m2_col"] = ScriptParameter(
            "m2_col", int, 2, "怪兽2所在列")
        paras["m3_target"] = ScriptParameter(
            "m3_target", int, 1, "配种怪兽3位置")
        paras["m3_talents"] = ScriptParameter(
            "m3_talents", str, "1,2,3", "配种怪兽3天赋")
        return paras
    
    def check_durations(self):
        if self._durations <= 0:
            return False
        if self.run_time_span >= self._durations * 60:
            self.send_log("运行时间已到达设定值，脚本停止")
            self.finished_process()
            return True
        return False
        
    def process_frame(self):
        if self.check_durations():
            return
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self.prepare_step_list):
                    self.set_circle_begin()
                    self._circle_step_index = 0
                    return
                self.prepare_step_list[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._jump_next_frame:
                self._jump_next_frame = False
                return
            if self._circle_step_index >= 0 and self._circle_step_index < len(self.cycle_step_list):
                self.cycle_step_list[self._circle_step_index]()
            else:
                self.macro_stop()
                self.set_circle_continue()
                self._circle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCircle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self.send_log(f"开始运行{DQM3Synthesis.script_name()}脚本")

    def on_circle(self):
        pass
        # run_time_span = self.run_time_span
        # self.send_log("脚本运行中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, int(
        #     run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format(DQM3Synthesis.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))

    def on_error(self):
        pass

    @property
    def prepare_step_list(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self._prepare_step_index += 1

    @property
    def cycle_step_list(self):
        return [
            self.prepare_cycle,
            self.restart_game,
            self.synthesis,
            self.check_shiny,
        ]
    
    def circle_init(self):
        pass

    def prepare_cycle(self):
        self._check_shiny_frame_count = 0
        self._circle_step_index += 1

    def restart_game(self):
        self.macro_run("recognition.dqm3.common.restart_game",
                        1, {"secondary": str(self._secondary)}, True, None)
        self._circle_step_index += 1

    def synthesis(self):
        macro_paras = dict()
        for p in self.paras.values():
            macro_paras[p.name] = p.value

        self.macro_run("recognition.dqm3.synthesis.synthesis",
                        1, macro_paras, True, None)
        self._jump_next_frame = True
        self._circle_step_index += 1

    def check_shiny(self):
        image = self.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_gray = gray[self._template_crop[1]:self._template_crop[1]+self._template_crop[3], self._template_crop[0]:self._template_crop[0]+self._template_crop[2]]
        match = cv2.matchTemplate(crop_gray, self._shiny_star_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(match)
        self._check_shiny_frame_count += 1
        if max_val >= 0.7:
            self.send_log("已成功配种闪光怪兽，脚本停止")
            self.finished_process()
            return
        if self._check_shiny_frame_count >= 6:
            self._circle_step_index += 1

    def finished_process(self):
        run_time_span = self.run_time_span
        self.macro_stop(block=True)
        # self.macro_run("common.switch_sleep",
        #                loop=1, paras={}, block=True, timeout=10)
        self.send_log("[{}] 脚本完成，已运行{}次，耗时{}小时{}分{}秒".format(DQM3Synthesis.script_name(), self.circle_times, int(
            run_time_span/3600), int((run_time_span % 3600) / 60), int(run_time_span % 60)))
        self.stop_work()
