import math
import multiprocessing
import time
from recognition.scripts.base import BaseScript, WorkflowEnum
import cv2
import numpy as np


class SwshBattleShiny(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        super().__init__(SwshBattleShiny.script_name(), stop_event,
                         frame_queue, controller_input_action_queue)
        self._prepare_steps = self.init_prepare_steps()
        self._prepare_step_index = -1
        self._circle_steps = self.init_circle_steps()
        self._circle_step_index = -1
        self._template = cv2.imread("resources/img/recognition/pokemon/swsh/battle_shiny.jpg")
        self._template = cv2.cvtColor(self._template, cv2.COLOR_BGR2GRAY)
        self._template_p = (865, 430)

    @staticmethod
    def script_name() -> str:
        return "剑盾定点刷闪"

    def process_frame(self):
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0 and self._prepare_step_index < len(self._prepare_steps):
                self._prepare_steps[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._circle_step_index >= 0 and self._circle_step_index < len(self._circle_steps):
                self._circle_steps[self._circle_step_index]()
            else:
                self.set_circle_continue()
                self._circle_step_index = 0
            return
        if self.running_status == WorkflowEnum.AfterCircle:
            self.stop_work()
            return

    def on_start(self):
        self._prepare_step_index = 0
        self.send_log("开始运行宝可梦剑盾定点闪图像识别检测脚本")

    def on_circle(self):
        if self.circle_times > 0 and self.circle_times % 10 == 0:
            run_time_span = self.run_time_span
            self.send_log("闪光检测中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, math.floor(
                run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format('宝可梦剑盾定点闪图像识别检测脚本', self.circle_times, math.floor(
            run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))

    def on_error(self):
        pass

    def init_prepare_steps(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self.set_circle_begin()
        self._circle_step_index = 0

    def init_circle_steps(self):
        return [
            self.circle_step_0,
            self.circle_step_1,
            self.circle_step_2,
            self.circle_step_3,
        ]

    def circle_init(self):
        self._circle_step_2_start_time_monotonic = 0
        self._circle_step_2_time_monotonic_check_1_temp = 0
        self._circle_step_2_time_monotonic_check_1 = 0
        self._circle_step_2_frame_count_check_1 = 0
        pass

    def circle_step_0(self):
        if self.current_frame_count == 1:
            self.macro_run("recognition.pokemon.swsh.common.restart_game",
                           1, {"secondary": "True"}, True, None)
            self._circle_step_index += 1
        else:
            self.macro_stop()
            self.set_circle_continue()
            self._circle_step_index = 0

    def circle_step_1(self):
        self.macro_run("common.press_button_a", -1, {}, False, None)
        self._circle_step_index += 1

    def circle_step_2(self):
        if self._circle_step_2_start_time_monotonic == 0:
            self._circle_step_2_start_time_monotonic = time.monotonic()

        if self.current_circle_time_span > 80:
            self._circle_step_index += 1
            return

        image = self.current_frame
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(gray, self._template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, p = cv2.minMaxLoc(match)
        if max_val > 0.75 and abs(p[0] - self._template_p[0]) <= 10 and abs(p[1] - self._template_p[1]) <= 10:
            if self._circle_step_2_time_monotonic_check_1 == 0:
                if self._circle_step_2_time_monotonic_check_1_temp == 0:
                    self.macro_stop(block=False)
                self._circle_step_2_time_monotonic_check_1_temp = time.monotonic()
            else:
                span = time.monotonic() - self._circle_step_2_time_monotonic_check_1
                if span < 1.1:
                    self._circle_step_index += 1
                    return
                elif span < 5:
                    # self.send_log("time_span:{:.2f}, frames_span:{}".format(
                    #     span, self.current_frame_count - self._circle_step_2_frame_count_check_1))
                    run_time_span = self.run_time_span
                    if self.current_frame_count - self._circle_step_2_frame_count_check_1 <= 4:
                        self._circle_step_index += 1
                        return
                    self.macro_stop(block=False)
                    self.send_log("检测到闪光，请人工核查，已运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, math.floor(
                        run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))
                    self.stop_work()
        elif self._circle_step_2_time_monotonic_check_1_temp > 0 and self._circle_step_2_time_monotonic_check_1 == 0:
            self._circle_step_2_time_monotonic_check_1 = self._circle_step_2_time_monotonic_check_1_temp
            self._circle_step_2_frame_count_check_1 = self.current_frame_count

    def circle_step_3(self):
        self.macro_stop()
        self.set_circle_continue()
        # self.send_log("未检测到闪光,帧数:{},时长{}".format(self.current_frame_count,self.current_circle_time_span))
        self._circle_step_index = 0
