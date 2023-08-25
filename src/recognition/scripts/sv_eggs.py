import math
import multiprocessing
import time
from recognition.scripts.base import BaseScript, WorkflowEnum
import cv2
import numpy as np


class SVEggs(BaseScript):
    def __init__(self, stop_event: multiprocessing.Event, frame_queue: multiprocessing.Queue, controller_input_action_queue: multiprocessing.Queue):
        super().__init__(SVEggs.script_name(), stop_event,
                         frame_queue, controller_input_action_queue)
        self._prepare_steps = self.init_prepare_steps()
        self._prepare_step_index = -1
        self._circle_steps = self.init_circle_steps()
        self._circle_step_index = -1
        self._template = None

    @staticmethod
    def script_name() -> str:
        return "朱紫野餐孵蛋放生"

    def process_frame(self):
        if self.running_status == WorkflowEnum.Preparation:
            if self._prepare_step_index >= 0:
                if self._prepare_step_index >= len(self._prepare_steps):
                    self.set_circle_begin()
                    self._circle_step_index = 0
                    return
                self._prepare_steps[self._prepare_step_index]()
            return
        if self.running_status == WorkflowEnum.Circle:
            if self.current_frame_count == 1:
                self.circle_init()
            if self._circle_step_index >= 0 and self._circle_step_index < len(self._circle_steps):
                self._circle_steps[self._circle_step_index]()
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
        self.send_log("开始运行宝可梦朱紫野餐孵蛋放生脚本")

    def on_circle(self):
        pass
        # run_time_span = self.run_time_span
        # self.send_log("脚本运行中，已经运行{}次，耗时{}小时{}分{}秒".format(self.circle_times, math.floor(
        #     run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))

    def on_stop(self):
        run_time_span = self.run_time_span
        self.send_log("[{}] 脚本停止，实际运行{}次，耗时{}小时{}分{}秒".format('宝可梦朱紫野餐孵蛋放生脚本', self.circle_times, math.floor(
            run_time_span/3600), math.floor((run_time_span % 3600) / 60), math.floor(run_time_span % 60)))

    def on_error(self):
        pass

    def init_prepare_steps(self):
        return [
            self.prepare_step_0,
        ]

    def prepare_step_0(self):
        self._prepare_step_index += 1

    def init_circle_steps(self):
        return [
            self.circle_picnic,
            self.circle_picnic,
        ]

    def circle_init(self):
        self.last_capture_time = 0
        pass

    def circle_picnic(self):
        self.send_log("1")
        self.macro_text_run("X\n", block=True)
        self.send_log("2")
        self._circle_step_index += 1

    def circle_hatching(self):
        self._circle_step_index += 1

    def circle_release(self):
        self._circle_step_index += 1
